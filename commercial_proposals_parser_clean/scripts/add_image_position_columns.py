#!/usr/bin/env python3
"""
Миграция для добавления полей row и column в таблицу product_images
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from sqlalchemy import text

def add_image_position_columns():
    """Добавляет поля row и column в таблицу product_images"""
    db_manager = DatabaseManager
    session = db_manager.get_session()
    
    print("=== ДОБАВЛЕНИЕ ПОЛЕЙ ПОЗИЦИИ ИЗОБРАЖЕНИЙ ===")
    
    try:
        # Добавляем поля row и column
        session.execute(text("ALTER TABLE product_images ADD COLUMN row INTEGER"))
        session.execute(text("ALTER TABLE product_images ADD COLUMN column VARCHAR(10)"))
        
        session.commit()
        print("✅ Поля row и column добавлены в таблицу product_images")
        
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Поля row и column уже существуют")
        else:
            print(f"❌ Ошибка при добавлении полей: {e}")
            session.rollback()
    
    session.close()

if __name__ == "__main__":
    add_image_position_columns()
