#!/usr/bin/env python3
"""
Загрузка только товаров в базу данных без очистки
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database.manager_v4 import CommercialProposalsDB

def load_products_from_json():
    """Загружает товары из JSON файла"""
    print("📦 Загрузка товаров из parsed_products.json...")
    
    db = CommercialProposalsDB('sqlite:///commercial_proposals_v4.db')
    
    # Читаем JSON файл
    with open('parsed_products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products_loaded = 0
    
    for item in data:
        try:
            # Создаем товар
            product = db.create_product(
                name=item['name'],
                characteristics=item.get('characteristics', ''),
                custom_design=item.get('custom_design', ''),
                sheet_id=item.get('sheet_id', 1)
            )
            
            print(f"  ✅ Создан товар: {product.name} (ID: {product.id})")
            products_loaded += 1
            
        except Exception as e:
            print(f"  ❌ Ошибка при создании товара {item['name']}: {e}")
    
    print(f"✅ Загружено товаров: {products_loaded}")

def main():
    """Основная функция"""
    print("🚀 Загрузка товаров в базу данных")
    print("=" * 50)
    
    # Загружаем товары
    load_products_from_json()
    
    print("\n✅ Процесс завершен!")

if __name__ == "__main__":
    main()
