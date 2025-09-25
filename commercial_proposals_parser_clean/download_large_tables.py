#!/usr/bin/env python3
"""
Скачивание больших таблиц через AdvancedDownloader
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.advanced_downloader import AdvancedDownloader
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata

def download_large_failed_sheets():
    """Скачиваем большие таблицы, которые не удалось скачать ранее"""
    
    print("🚀 СКАЧИВАНИЕ БОЛЬШИХ ТАБЛИЦ ЧЕРЕЗ ADVANCED DOWNLOADER")
    print("=" * 70)
    
    session = DatabaseManager.get_session()
    
    try:
        # Находим таблицы без файлов (failed to download)
        failed_sheets = session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.is_(None),
            SheetMetadata.sheet_url.isnot(None)
        ).limit(20).all()  # Берем первые 20
        
        print(f"📋 Найдено таблиц для скачивания: {len(failed_sheets)}")
        
        if not failed_sheets:
            print("✅ Все таблицы уже скачаны!")
            return
        
        # Создаем продвинутый скачиватель
        downloader = AdvancedDownloader()
        
        if not downloader.drive_service or not downloader.sheets_service:
            print("❌ Не удалось инициализировать Google API")
            return
        
        # Скачиваем по очереди
        successful = 0
        failed = 0
        
        for i, sheet in enumerate(failed_sheets, 1):
            print(f"\\n📥 [{i}/{len(failed_sheets)}] Скачиваем: {sheet.sheet_title}")
            
            try:
                # Пробуем многоуровневое скачивание
                file_path = downloader.download_large_sheet(
                    sheet.sheet_url, 
                    sheet.sheet_title
                )
                
                if file_path:
                    # Обновляем путь к файлу в БД
                    sheet.local_file_path = file_path
                    sheet.status = 'downloaded'
                    session.commit()
                    successful += 1
                    print(f"✅ Успешно: {Path(file_path).name}")
                else:
                    failed += 1
                    print(f"❌ Не удалось скачать")
                    
            except Exception as e:
                failed += 1
                print(f"❌ Ошибка: {e}")
                continue
        
        print(f"\\n📊 ИТОГИ СКАЧИВАНИЯ:")
        print(f"   ✅ Успешно: {successful}")  
        print(f"   ❌ Ошибок: {failed}")
        
        if successful > 0:
            print(f"\\n🎉 Скачано {successful} больших таблиц!")
            print(f"   📋 Теперь можно их парсить")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    download_large_failed_sheets()


