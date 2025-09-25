#!/usr/bin/env python3
"""
Добавление полей start_row и end_row в таблицу products
"""

import sys
from pathlib import Path
import logging

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from database.manager_v4 import DatabaseManager
from sqlalchemy import text

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def add_row_columns():
    """Добавляет поля start_row и end_row в таблицу products"""
    session = DatabaseManager.get_session()
    try:
        logger.info("=== ДОБАВЛЕНИЕ ПОЛЕЙ start_row И end_row ===")
        
        # Добавляем поле start_row
        logger.info("Добавление поля start_row...")
        session.execute(text("ALTER TABLE products ADD COLUMN start_row INTEGER"))
        
        # Добавляем поле end_row
        logger.info("Добавление поля end_row...")
        session.execute(text("ALTER TABLE products ADD COLUMN end_row INTEGER"))
        
        session.commit()
        logger.info("✅ Поля start_row и end_row успешно добавлены")
        
        # Проверяем результат
        result = session.execute(text('PRAGMA table_info(products)'))
        columns = result.fetchall()
        logger.info("Столбцы в таблице products:")
        for col in columns:
            logger.info(f"  {col[1]} ({col[2]})")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка добавления полей: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    add_row_columns()

