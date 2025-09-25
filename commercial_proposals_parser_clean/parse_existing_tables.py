#!/usr/bin/env python3
"""
Парсинг уже скачанных таблиц с корректными проверками
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata
from scripts.complete_parsing_pipeline_v5 import EnhancedParser

def parse_existing_downloaded_tables(limit=25):
    """Парсит уже скачанные таблицы"""
    
    session = DatabaseManager.get_session()
    
    try:
        # Получаем таблицы со скачанными файлами, но не полностью обработанными
        tables_to_parse = session.query(SheetMetadata).filter(
            SheetMetadata.status != 'completed',  # Не завершенные
            SheetMetadata.local_file_path.isnot(None)  # Файл есть
        ).limit(limit).all()
        
        if not tables_to_parse:
            print("✅ Все скачанные таблицы уже обработаны!")
            return
        
        print(f"🚀 ПАРСИНГ {len(tables_to_parse)} УЖЕ СКАЧАННЫХ ТАБЛИЦ")
        print("=" * 70)
        
        # Создаем парсер
        parser = EnhancedParser()
        
        successful = 0
        failed = 0
        
        for i, sheet in enumerate(tables_to_parse, 1):
            print(f"\n📊 [{i}/{len(tables_to_parse)}] Парсим: {sheet.sheet_title}")
            
            # Проверяем существование файла
            if not sheet.local_file_path:
                print("❌ Нет пути к файлу")
                failed += 1
                continue
                
            excel_file_path = Path(sheet.local_file_path)
            if not excel_file_path.exists():
                print(f"❌ Файл не найден: {excel_file_path}")
                failed += 1
                continue
            
            try:
                # Парсим таблицу (методу нужен только sheet_id)
                success = parser.parse_sheet_complete(sheet_id=sheet.id)
                
                if success:
                    # Обновляем статус
                    sheet.status = 'completed'
                    session.commit()
                    successful += 1
                    print("✅ Успешно обработано")
                else:
                    failed += 1
                    print("❌ Ошибка парсинга")
                    
            except Exception as e:
                print(f"❌ Критическая ошибка: {e}")
                failed += 1
                continue
        
        print(f"\n📊 ИТОГИ ПАРСИНГА:")
        print(f"   ✅ Успешно: {successful}")  
        print(f"   ❌ Ошибок: {failed}")
        
        # Показываем статистику товаров
        if successful > 0:
            print(f"\n🎉 Обработано {successful} новых таблиц!")
            print(f"   📋 Проверьте результаты командой: python3 scripts/final_validation_report.py")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    parse_existing_downloaded_tables()
