@echo off
echo 🚀 Запуск Planfix Dashboard 2025...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python final_dashboard.py
pause
