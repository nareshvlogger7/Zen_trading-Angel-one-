import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from celery import Celery
from SmartApi import SmartConnect
import pyotp
import pandas as pd
import datetime as dt
import time
from typing import Dict, List, Optional, Union

app = Flask(__name__)
CORS(app)

# Celery configuration
celery = Celery('tasks', broker='redis://localhost:6379/0')
celery.conf.update(app.config)

# SmartAPI configuration
api_key = os.environ.get('API_KEY')
client_id = os.environ.get('CLIENT_ID')
password = os.environ.get('PASSWORD')
token = os.environ.get('TOKEN')

class AngelOneClient:
    def __init__(self):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.token = token
        self.totp = pyotp.TOTP(self.token).now()
        self.smart_api = None
        self.instrument_list = None

    def _initialize_smart_api(self):
        if self.smart_api is None:
            self.smart_api = SmartConnect(self.api_key)
            self.smart_api.generateSession(self.client_id, self.password, self.totp)

    def get_open_orders(self):
        self._initialize_smart_api()
        try:
            response = self.smart_api.orderBook()
            df = pd.DataFrame(response['data'])
            if len(df) > 0:
                return df[df['orderstatus'] == 'open']
            else:
                return None
        except Exception as e:
            print(e)
            return None

angel_one_client = AngelOneClient()

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    # TODO: Implement actual subscription logic (e.g., payment processing)
    return jsonify({"success": True, "message": "Subscription successful"}), 200

@app.route('/api/start-trading', methods=['POST'])
def start_trading():
    celery.send_task('tasks.run_trade_task')
    return jsonify({"success": True, "message": "Trading process started"}), 200

@app.route('/api/order-history', methods=['GET'])
def order_history():
    orders = angel_one_client.get_open_orders()
    if orders is not None:
        return jsonify(orders.to_dict(orient='records')), 200
    return jsonify([]), 200

@app.route('/api/portfolio', methods=['GET'])
def portfolio():
    angel_one_client._initialize_smart_api()
    try:
        positions = pd.DataFrame(angel_one_client.smart_api.position()['data'])
        return jsonify(positions.to_dict(orient='records')), 200
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        return jsonify([]), 500

@app.route('/api/profit-loss', methods=['GET'])
def profit_loss():
    angel_one_client._initialize_smart_api()
    try:
        positions = pd.DataFrame(angel_one_client.smart_api.position()['data'])
        total_pnl = positions['pnl'].sum()
        return jsonify({
            "total_profit_loss": float(total_pnl),
            "positions": positions[['tradingsymbol', 'pnl']].to_dict(orient='records')
        }), 200
    except Exception as e:
        print(f"Error calculating profit/loss: {e}")
        return jsonify({"error": "Failed to calculate profit/loss"}), 500

@celery.task(name="tasks.run_trade_task")
def run_trade_task():
    # Implement your trading logic here
    pass

if __name__ == '__main__':
    app.run(debug=True)