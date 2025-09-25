#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: делаем product_id nullable в таблице product_images
"""

import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from sqlalchemy import text

def migrate_product_id_nullable():
    """Делает product_id nullable в таблице product_images"""
    print("🔧 Миграция: product_id → nullable в product_images")
    
    session = DatabaseManager.get_session()
    
    try:
        # Для SQLite нужно пересоздать таблицу
        print("📋 Создаем временную таблицу...")
        
        # 1. Создаем временную таблицу с новой структурой
        session.execute(text("""
            CREATE TABLE product_images_new (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                sheet_id INTEGER,
                local_path VARCHAR(500),
                image_type VARCHAR(50) DEFAULT 'main',
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                format VARCHAR(20),
                is_downloaded INTEGER DEFAULT 1,
                position JSON,
                "row" INTEGER,
                "column" VARCHAR(10),
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (sheet_id) REFERENCES sheets_metadata(id)
            )
        """))
        
        # 2. Копируем данные
        print("📋 Копируем данные...")
        session.execute(text("""
            INSERT INTO product_images_new 
            SELECT * FROM product_images
        """))
        
        # 3. Удаляем старую таблицу
        print("📋 Удаляем старую таблицу...")
        session.execute(text("DROP TABLE product_images"))
        
        # 4. Переименовываем новую таблицу
        print("📋 Переименовываем новую таблицу...")
        session.execute(text("ALTER TABLE product_images_new RENAME TO product_images"))
        
        session.commit()
        print("✅ Миграция завершена успешно!")
        
        # Проверяем результат
        result = session.execute(text("SELECT COUNT(*) FROM product_images WHERE product_id IS NULL"))
        null_count = result.scalar()
        
        total_result = session.execute(text("SELECT COUNT(*) FROM product_images"))
        total_count = total_result.scalar()
        
        print(f"📊 Изображений без product_id: {null_count}")
        print(f"📊 Всего изображений: {total_count}")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_product_id_nullable()
