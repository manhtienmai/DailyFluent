@echo off
cd /d E:\DailyFluent
call venv\Scripts\activate.bat

:: Dùng lệnh này để đánh thức Claude mà không bị lỗi Raw mode
echo Waking up Claude...
call claude --version

echo Done!
timeout /t 3