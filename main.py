from celery_config import app
from trading_bot import TradeMaster

if __name__ == "__main__":
    app.start()
