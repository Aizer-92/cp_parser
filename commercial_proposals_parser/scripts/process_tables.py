#!/usr/bin/env python3
"""
Основной скрипт для обработки Google Sheets таблиц
Объединяет скачивание и анализ
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def main():
    """Основная функция"""
    
    print("🚀 Обработка Google Sheets таблиц")
    print("=" * 50)
    print("Этот скрипт объединяет два этапа:")
    print("1. Скачивание таблиц из Google Sheets")
    print("2. Анализ скачанных файлов и сохранение в БД")
    print()
    
    # Этап 1: Скачивание
    print("📥 ЭТАП 1: Скачивание таблиц")
    print("-" * 30)
    
    try:
        from scripts.download_tables import download_all_sheets
        download_all_sheets()
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # Этап 2: Анализ
    print("🔍 ЭТАП 2: Анализ таблиц")
    print("-" * 30)
    
    try:
        from scripts.analyze_tables import analyze_all_sheets
        analyze_all_sheets()
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        return
    
    print("\n" + "=" * 50)
    print("✅ Обработка завершена!")

if __name__ == "__main__":
    main()
