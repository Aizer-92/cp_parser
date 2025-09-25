#!/usr/bin/env python3
"""
Скрипт для исправления описаний товаров в базе данных
"""

import json
import sys
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def fix_descriptions():
    """Исправление описаний товаров"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        # Загружаем данные из JSON файлов
        with open('parsed_products.json', 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        with open('merch_sense_products.json', 'r', encoding='utf-8') as f:
            merch_data = json.load(f)
        
        # Создаем словарь для быстрого поиска
        all_data = {}
        for item in parsed_data:
            all_data[item['name']] = item
        for item in merch_data:
            all_data[item['name']] = item
        
        # Получаем все товары из базы данных
        products = db.get_all_products_with_details()
        
        print(f"🔧 Исправляем описания для {len(products)} товаров...")
        
        for product, price_offers, images in products:
            if product.name in all_data:
                item = all_data[product.name]
                
                # Обновляем характеристики и кастом
                session.execute(text('''
                    UPDATE products 
                    SET characteristics = :characteristics, custom_design = :custom_design 
                    WHERE id = :product_id
                '''), {
                    'characteristics': item.get('characteristics', ''),
                    'custom_design': item.get('custom_design', ''),
                    'product_id': product.id
                })
                
                print(f"  ✅ {product.name} - обновлены характеристики и кастом")
            else:
                print(f"  ⚠️  {product.name} - не найден в JSON данных")
        
        session.commit()
        print("✅ Описания исправлены!")
        
    finally:
        session.close()

def main():
    print("🔄 Исправление описаний товаров...")
    fix_descriptions()
    
    # Проверяем результат
    db = CommercialProposalsDB(DATABASE_URL_V4)
    products = db.get_all_products_with_details()
    
    print(f"\n📊 Проверяем результат:")
    for i, (product, price_offers, images) in enumerate(products[:3], 1):
        print(f"{i}. {product.name}")
        print(f"   Характеристики: {product.characteristics[:100] if product.characteristics else 'НЕТ'}...")
        print(f"   Кастом: {product.custom_design[:50] if product.custom_design else 'НЕТ'}...")
        print()

if __name__ == "__main__":
    main()
