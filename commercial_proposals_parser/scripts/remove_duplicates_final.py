#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов товаров - оставляем только товары с вариантами цен
"""

import sys
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def remove_duplicates():
    """Удаление дубликатов товаров - оставляем только товары с вариантами цен"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        # Удаляем товары без вариантов цен (ID 12-26)
        # Это дубликаты товаров из parsed_products.json
        session.execute(text('DELETE FROM product_images WHERE product_id BETWEEN 12 AND 26'))
        session.execute(text('DELETE FROM price_offers WHERE product_id BETWEEN 12 AND 26'))
        session.execute(text('DELETE FROM products WHERE id BETWEEN 12 AND 26'))
        
        # Обновляем ID товаров с вариантами цен (ID 29-43 -> 12-26)
        # Обновляем product_images
        session.execute(text('UPDATE product_images SET product_id = product_id - 17 WHERE product_id BETWEEN 29 AND 43'))
        
        # Обновляем price_offers
        session.execute(text('UPDATE price_offers SET product_id = product_id - 17 WHERE product_id BETWEEN 29 AND 43'))
        
        # Обновляем products
        session.execute(text('UPDATE products SET id = id - 17 WHERE id BETWEEN 29 AND 43'))
        
        # Обновляем ID товаров 27-28 -> 12-13 (ежедневники)
        session.execute(text('UPDATE product_images SET product_id = product_id - 15 WHERE product_id BETWEEN 27 AND 28'))
        session.execute(text('UPDATE price_offers SET product_id = product_id - 15 WHERE product_id BETWEEN 27 AND 28'))
        session.execute(text('UPDATE products SET id = id - 15 WHERE id BETWEEN 27 AND 28'))
        
        session.commit()
        print("✅ Дубликаты удалены, ID товаров обновлены")
        
    finally:
        session.close()

def main():
    print("🔄 Удаление дубликатов товаров...")
    remove_duplicates()
    
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
