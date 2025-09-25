#!/usr/bin/env python3
"""
Скрипт для исправления изображений товаров "Мерч для Sense"
"""

import sys
import os
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def clear_merch_sense_images():
    """Очистка изображений товаров 'Мерч для Sense'"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        # Удаляем изображения товаров "Мерч для Sense" (ID 29-43)
        session.execute(text('DELETE FROM product_images WHERE product_id BETWEEN 29 AND 43'))
        session.commit()
        print("✅ Очищены изображения товаров 'Мерч для Sense'")
        
    finally:
        session.close()

def main():
    print("🔄 Исправление изображений товаров 'Мерч для Sense'...")
    
    # Очищаем неправильные изображения
    clear_merch_sense_images()
    
    # Проверяем результат
    db = CommercialProposalsDB(DATABASE_URL_V4)
    products = db.get_all_products_with_details()
    
    print(f"\n📊 Проверяем результат:")
    merch_sense_products = [(p, po, i) for p, po, i in products if p.id >= 29]
    
    for product, price_offers, images in merch_sense_products:
        if images:
            print(f"  {product.name} (ID: {product.id}) - {len(images)} изображений")
        else:
            print(f"  {product.name} (ID: {product.id}) - НЕТ изображений")

if __name__ == "__main__":
    main()
