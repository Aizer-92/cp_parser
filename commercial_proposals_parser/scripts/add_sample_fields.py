#!/usr/bin/env python3
"""
Добавление полей для образцов в таблицу price_offers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def add_sample_fields():
    """Добавляет поля для образцов в таблицу price_offers"""
    
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    try:
        with db.get_session() as session:
            # Добавляем поля для образцов
            session.execute(text("ALTER TABLE price_offers ADD COLUMN sample_price FLOAT"))
            session.execute(text("ALTER TABLE price_offers ADD COLUMN sample_time VARCHAR(100)"))
            session.execute(text("ALTER TABLE price_offers ADD COLUMN sample_price_currency VARCHAR(10)"))
            session.commit()
            print("✅ Поля для образцов добавлены в таблицу price_offers")
            
    except Exception as e:
        if "duplicate column name" in str(e):
            print("✅ Поля для образцов уже существуют")
        else:
            print(f"❌ Ошибка при добавлении полей: {e}")

if __name__ == "__main__":
    add_sample_fields()
