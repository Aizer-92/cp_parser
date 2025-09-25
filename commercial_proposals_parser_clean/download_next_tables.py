#!/usr/bin/env python3
"""
Скачивание следующих 20 таблиц из Google Sheets
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.google_drive_downloader import GoogleDriveDownloader

def main():
    """Скачиваем следующие 20 таблиц"""
    
    print("🚀 СКАЧИВАНИЕ 20 НОВЫХ ТАБЛИЦ ИЗ GOOGLE SHEETS")
    print("=" * 70)
    
    try:
        downloader = GoogleDriveDownloader()
        
        if not downloader.drive_service:
            print("❌ Не удалось инициализировать Google Drive API")
            print("   Проверьте файл учетных данных Google")
            return
        
        # Скачиваем 20 таблиц
        results = downloader.download_sheets_from_db(limit=20)
        
        print(f"\n📊 ИТОГИ СКАЧИВАНИЯ:")
        print(f"   ✅ Успешно: {results.get('successful', 0)}")  
        print(f"   ❌ Ошибок: {results.get('failed', 0)}")
        print(f"   📁 Папка: storage/excel_files/")
        
        if results.get('successful', 0) > 0:
            print(f"\n✅ Скачивание завершено! Теперь можно парсить таблицы.")
        else:
            print(f"\n⚠️  Новых таблиц для скачивания не найдено.")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()


