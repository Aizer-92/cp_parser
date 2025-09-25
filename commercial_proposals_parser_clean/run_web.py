#!/usr/bin/env python3
"""
Скрипт для запуска веб-интерфейса
"""
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from web_app_v4.main import app

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса...")
    print("📱 Откройте http://localhost:8001 в браузере")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=8001, debug=True)

