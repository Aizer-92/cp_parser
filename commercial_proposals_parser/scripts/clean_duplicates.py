#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов товаров - оставляем только товары с вариантами цен
"""

import sys
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def clean_duplicates():
    """Удаление дубликатов товаров - оставляем только товары с вариантами цен"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        # Удаляем товары без вариантов цен (ID 12-26)
        session.execute(text('DELETE FROM product_images WHERE product_id BETWEEN 12 AND 26'))
        session.execute(text('DELETE FROM price_offers WHERE product_id BETWEEN 12 AND 26'))
        session.execute(text('DELETE FROM products WHERE id BETWEEN 12 AND 26'))
        
        session.commit()
        print("✅ Дубликаты удалены")
        
    finally:
        session.close()

def main():
    print("🔄 Удаление дубликатов товаров...")
    clean_duplicates()
    
    # Проверяем результат
    db = CommercialProposalsDB(DATABASE_URL_V4)
    stats = db.get_statistics()
    print(f"\n📊 Итоговая статистика:")
    print(f"   Товаров: {stats['total_products']}")
    print(f"   Вариантов цен: {stats['total_price_offers']}")
    print(f"   Изображений: {stats['total_images']}")
    
    # Проверяем товары без вариантов цен
    products = db.get_all_products_with_details()
    products_without_prices = [p for p, po, i in products if not po]
    if products_without_prices:
        print(f"\n⚠️  Товары без вариантов цен: {len(products_without_prices)}")
        for product in products_without_prices:
            print(f"   - {product.name} (ID: {product.id})")
    else:
        print(f"\n✅ Все товары имеют варианты цен!")

if __name__ == "__main__":
    main()
