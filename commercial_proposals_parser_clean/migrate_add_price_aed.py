#!/usr/bin/env python3
"""
Миграция: добавление поля price_aed в таблицу price_offers
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from sqlalchemy import text

def migrate_add_price_aed():
    """Добавляет поле price_aed в таблицу price_offers"""
    
    session = DatabaseManager.get_session()
    
    try:
        print("🔄 МИГРАЦИЯ: Добавление поля price_aed")
        print("=" * 50)
        
        # Проверяем, есть ли уже поле
        result = session.execute(text("PRAGMA table_info(price_offers)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'price_aed' in columns:
            print("✅ Поле price_aed уже существует")
            return True
        
        # Добавляем новое поле
        session.execute(text("ALTER TABLE price_offers ADD COLUMN price_aed REAL"))
        session.commit()
        
        print("✅ Поле price_aed успешно добавлено в таблицу price_offers")
        
        # Проверяем результат
        result = session.execute(text("PRAGMA table_info(price_offers)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"📋 Все поля таблицы price_offers:")
        for col in columns:
            print(f"   • {col}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка миграции: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = migrate_add_price_aed()
    if success:
        print("\n🎉 Миграция завершена успешно!")
    else:
        print("\n💥 Миграция не удалась!")


