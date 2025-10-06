#!/usr/bin/env python3
"""
Изменение типа колонки quantity на BIGINT
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def fix_column_type():
    print("🔧 Изменение типа колонки quantity на BIGINT...")
    
    engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Изменяем тип колонки
        session.execute(text("""
            ALTER TABLE price_offers 
            ALTER COLUMN quantity TYPE BIGINT
        """))
        
        session.commit()
        print("✅ Колонка quantity изменена на BIGINT!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_column_type()
