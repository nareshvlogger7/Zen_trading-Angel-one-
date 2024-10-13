@echo off

REM Start Redis server
start "" redis-server

REM Wait for Redis to start
timeout /t 5

REM Run celery beat
start "" celery -A cronjobs beat --loglevel=info

REM Run celery worker
start "" celery -A cronjobs worker --loglevel=info

REM Keep the command prompt window open
pause