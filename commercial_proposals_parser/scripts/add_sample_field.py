#!/usr/bin/env python3
"""
Добавление поля is_sample в таблицу price_offers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL
from sqlalchemy import text

def add_sample_field():
    """Добавляет поле is_sample в таблицу price_offers"""
    
    db = CommercialProposalsDB(DATABASE_URL)
    
    try:
        # Добавляем поле is_sample
        with db.get_session() as session:
            session.execute(text("ALTER TABLE price_offers ADD COLUMN is_sample BOOLEAN DEFAULT FALSE"))
            session.commit()
            print("✅ Поле is_sample добавлено в таблицу price_offers")
            
            # Обновляем существующие записи с route_name = 'Образец'
            session.execute(text("UPDATE price_offers SET is_sample = TRUE WHERE route_name = 'Образец'"))
            session.commit()
            print("✅ Обновлены записи с route_name = 'Образец'")
            
    except Exception as e:
        print(f"❌ Ошибка при добавлении поля: {e}")

if __name__ == "__main__":
    add_sample_field()
