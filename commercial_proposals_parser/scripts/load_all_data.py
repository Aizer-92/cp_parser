#!/usr/bin/env python3
"""
Загрузка всех данных в базу данных
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def clear_database():
    """Очищает базу данных"""
    print("🗑️  Очистка базы данных...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, PriceOffer, ProductImage, SheetMetadata
        
        # Удаляем все данные
        session.query(ProductImage).delete()
        session.query(PriceOffer).delete()
        session.query(Product).delete()
        session.query(SheetMetadata).delete()
        session.commit()
        
        print("✅ База данных очищена")

def load_products_from_json():
    """Загружает товары из JSON файла"""
    print("📦 Загрузка товаров из parsed_products.json...")
    
    with open('parsed_products.json', 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    # Загружаем товары из Мерч для Sense
    with open('merch_sense_products.json', 'r', encoding='utf-8') as f:
        merch_products = json.load(f)
    
    # Добавляем source_file для товаров из Мерч для Sense
    for product in merch_products:
        product['source_file'] = 'Мерч для Sense_1757934153.xlsx'
    
    # Объединяем все товары
    all_products = products_data + merch_products
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    # Создаем записи о таблицах
    sheet_metadata = {}
    
    for product_data in all_products:
        source_file = product_data['source_file']
        
        # Создаем метаданные таблицы если их нет
        if source_file not in sheet_metadata:
            # Создаем уникальный sheet_id для каждого файла
            sheet_id = f"sheet_{len(sheet_metadata) + 1}_{source_file.replace('.xlsx', '')}"
            sheet_meta = db.create_sheet_metadata(
                sheet_url=f"https://docs.google.com/spreadsheets/d/{sheet_id}",
                sheet_title=source_file.replace('.xlsx', '')
            )
            sheet_metadata[source_file] = sheet_meta
        
        # Создаем товар
        product = db.create_product(
            name=product_data['name'],
            description=product_data['characteristics'],
            custom_design=product_data['custom_design'],
            sheet_id=sheet_metadata[source_file]
        )
        
        print(f"  ✅ Создан товар: {product.name} (ID: {product.id})")
        
        # Создаем ценовые предложения
        for price_offer_data in product_data['price_offers']:
            db.create_price_offer(
                product_id=product.id,
                route_name=price_offer_data['route_name'],
                quantity=price_offer_data['quantity'],
                price_usd=price_offer_data['price_usd'],
                price_rub=price_offer_data['price_rub'],
                delivery_time=price_offer_data['delivery_time'],
                is_sample=price_offer_data['is_sample'],
                sample_price=price_offer_data.get('sample_price'),
                sample_time=price_offer_data.get('delivery_time') if price_offer_data['is_sample'] else None,
                sample_price_currency='RUB' if price_offer_data['is_sample'] else None
            )
        
        # Создаем изображения (пока заглушки)
        # TODO: Добавить реальные изображения
        
    print(f"✅ Загружено товаров: {len(all_products)}")

def main():
    """Основная функция"""
    print("🚀 Очистка и перезагрузка базы данных")
    print("=" * 50)
    
    # Очищаем базу данных
    clear_database()
    
    # Загружаем новые данные
    load_products_from_json()
    
    print("\n✅ Процесс завершен!")

if __name__ == "__main__":
    main()
