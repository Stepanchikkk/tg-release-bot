@echo off
echo [RUNNING TG-RELEASE-BOT IN DEV MODE]
set PYTHONPATH=%cd%
python -m bot.main
pause
