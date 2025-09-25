#!/usr/bin/env python3
"""
Скрипт для исправления описаний товаров в базе данных - простая версия
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
        
        # Получаем все товары из базы данных напрямую
        result = session.execute(text('SELECT id, name FROM products'))
        products = result.fetchall()
        
        print(f"🔧 Исправляем описания для {len(products)} товаров...")
        
        for product_id, product_name in products:
            if product_name in all_data:
                item = all_data[product_name]
                
                # Обновляем характеристики и кастом
                characteristics = item.get('characteristics', '')
                custom_design = item.get('custom_design', '')
                
                session.execute(text('''
                    UPDATE products 
                    SET characteristics = :characteristics, custom_design = :custom_design 
                    WHERE id = :product_id
                '''), {
                    'characteristics': characteristics,
                    'custom_design': custom_design,
                    'product_id': product_id
                })
                
                print(f"  ✅ {product_name} - обновлены характеристики и кастом")
            else:
                print(f"  ⚠️  {product_name} - не найден в JSON данных")
        
        session.commit()
        print("✅ Описания исправлены!")
        
    finally:
        session.close()

def main():
    print("🔄 Исправление описаний товаров...")
    fix_descriptions()
    
    # Проверяем результат
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        result = session.execute(text('SELECT id, name, characteristics, custom_design FROM products LIMIT 3'))
        products = result.fetchall()
        
        print(f"\n📊 Проверяем результат:")
        for product_id, name, characteristics, custom_design in products:
            print(f"{product_id}. {name}")
            print(f"   Характеристики: {characteristics[:100] if characteristics else 'НЕТ'}...")
            print(f"   Кастом: {custom_design[:50] if custom_design else 'НЕТ'}...")
            print()
    finally:
        session.close()

if __name__ == "__main__":
    main()
