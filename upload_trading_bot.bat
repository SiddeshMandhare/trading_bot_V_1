@echo off
echo ====================================
echo Upload Trading Bot to Server
echo ====================================
echo.

REM Set your trading_bot folder path - CHANGE THIS TO YOUR ACTUAL PATH
set TRADING_BOT_PATH=E:\siddesh\Trading\Sublime\code\Test\option\trading_bot_V_1

REM Check if folder exists
if not exist "%TRADING_BOT_PATH%" (
    echo ERROR: Trading bot folder not found at %TRADING_BOT_PATH%
    echo.
    echo Please update the TRADING_BOT_PATH variable in this script
    pause
    exit /b 1
)

echo Found trading bot at: %TRADING_BOT_PATH%
echo.
echo Uploading files to server...

cd /d "%TRADING_BOT_PATH%"

REM Upload all Python files
scp -i C:\Users\Sidma\.ssh\LightsailDefaultKey-ap-south-1.pem *.py ubuntu@65.2.12.127:/home/ubuntu/trading_bot/

REM Upload requirements and config files
scp -i C:\Users\Sidma\.ssh\LightsailDefaultKey-ap-south-1.pem *.txt *.json *.sh ubuntu@65.2.12.127:/home/ubuntu/trading_bot/ 2>nul

REM Upload folders if they exist
scp -i C:\Users\Sidma\.ssh\LightsailDefaultKey-ap-south-1.pem -r strategies ubuntu@65.2.12.127:/home/ubuntu/trading_bot/ 2>nul
scp -i C:\Users\Sidma\.ssh\LightsailDefaultKey-ap-south-1.pem -r backups ubuntu@65.2.12.127:/home/ubuntu/trading_bot/ 2>nul

echo.
echo Upload complete!
echo.
echo Now SSH into server and run:
echo ssh -i C:\Users\Sidma\.ssh\LightsailDefaultKey-ap-south-1.pem ubuntu@65.2.12.127
echo cd /home/ubuntu/trading_bot
echo python3 main.py
pause