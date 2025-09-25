#!/usr/bin/env python3
"""
Скрипт для запуска веб-приложения Commercial Proposals Parser
"""

import os
import sys
import subprocess

def main():
    """Запуск веб-приложения"""
    
    # Переходим в директорию веб-приложения
    web_app_dir = os.path.join(os.path.dirname(__file__), 'web_app_v4')
    
    if not os.path.exists(web_app_dir):
        print("❌ Директория web_app_v4 не найдена!")
        return
    
    print("🚀 Запуск Commercial Proposals Parser...")
    print("📍 Директория:", web_app_dir)
    print("🌐 Приложение будет доступно по адресу: http://localhost:8000")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        # Запускаем приложение
        os.chdir(web_app_dir)
        subprocess.run([sys.executable, 'main.py'], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Приложение остановлено")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()

