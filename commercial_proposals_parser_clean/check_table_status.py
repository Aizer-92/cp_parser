#!/usr/bin/env python3
"""
Проверка статуса обработки всех таблиц
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata
from sqlalchemy import desc

def check_table_status():
    """Проверяем статус всех таблиц"""
    
    session = DatabaseManager.get_session()
    
    # Получаем все таблицы
    all_sheets = session.query(SheetMetadata).order_by(SheetMetadata.id).all()
    
    print(f"📊 СТАТУС ВСЕХ ТАБЛИЦ ({len(all_sheets)} шт)")
    print("=" * 80)
    
    completed = 0
    pending = 0
    
    for sheet in all_sheets:
        status = sheet.parsing_status if sheet.parsing_status else "pending"
        status_icon = "✅" if status == "completed" else "⏳" if status == "processing" else "❌"
        
        print(f"{status_icon} ID {sheet.id:2d}: {sheet.sheet_title[:60]}")
        print(f"     Статус: {status}")
        print(f"     URL: {sheet.google_sheets_url[:80] if sheet.google_sheets_url else 'N/A'}...")
        
        if status == "completed":
            completed += 1
        else:
            pending += 1
        print()
    
    print("📈 ИТОГИ:")
    print(f"   ✅ Обработано: {completed}")
    print(f"   ⏳ Ожидает: {pending}")
    print(f"   📊 Всего: {len(all_sheets)}")
    
    # Показываем следующие необработанные таблицы
    unprocessed = session.query(SheetMetadata).filter(
        (SheetMetadata.parsing_status != "completed") | 
        (SheetMetadata.parsing_status.is_(None))
    ).order_by(SheetMetadata.id).limit(10).all()
    
    print(f"\n🎯 СЛЕДУЮЩИЕ {min(10, len(unprocessed))} НЕОБРАБОТАННЫХ ТАБЛИЦ:")
    print("=" * 80)
    
    for sheet in unprocessed:
        print(f"ID {sheet.id:2d}: {sheet.sheet_title}")
        print(f"     URL: {sheet.google_sheets_url[:80] if sheet.google_sheets_url else 'N/A'}...")
        print()
    
    session.close()

if __name__ == "__main__":
    check_table_status()


