#!/usr/bin/env python3
"""
Проверка структуры таблиц в SQLite
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, inspect

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"

def check_schema():
    engine = create_engine(SQLITE_URL)
    inspector = inspect(engine)
    
    print("=" * 80)
    print("СТРУКТУРА ТАБЛИЦ В SQLITE")
    print("=" * 80)
    
    # Проверяем price_offers
    print("\n📋 Таблица: price_offers")
    columns = inspector.get_columns('price_offers')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # Проверяем product_images
    print("\n📋 Таблица: product_images")
    columns = inspector.get_columns('product_images')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_schema()

