#!/usr/bin/env python3
"""
Скрипт запуска для Railway
Читает PORT из переменной окружения и запускает gunicorn
"""
import os
import subprocess
import sys

# Получаем порт из переменной окружения
port = os.environ.get('PORT', '5000')

print(f"🚀 Starting server on port {port}")
print(f"📁 Current directory: {os.getcwd()}")
print(f"📂 Web interface directory: {os.path.join(os.getcwd(), 'web_interface')}")

# Меняем директорию на web_interface
os.chdir('web_interface')

# Запускаем gunicorn с правильным портом
cmd = [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '4',
    '--timeout', '120',
    '--access-logfile', '-',
    '--error-logfile', '-',
    '--log-level', 'info',
    'app:app'
]

print(f"🔧 Running command: {' '.join(cmd)}")
sys.exit(subprocess.call(cmd))
