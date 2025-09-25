#!/usr/bin/env python3
"""
Исправление базы данных: удаление дублей, исправление товаров из Мерч для Sense
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

def load_corrected_data():
    """Загружает исправленные данные"""
    print("📦 Загрузка исправленных данных...")
    
    # Загружаем только оригинальную таблицу и Мерч для Sense
    with open('parsed_products.json', 'r', encoding='utf-8') as f:
        all_products = json.load(f)
    
    # Фильтруем только оригинальную таблицу
    original_products = [p for p in all_products if p['source_file'] == 'original_sheet.xlsx']
    
    # Загружаем товары из Мерч для Sense
    with open('merch_sense_products.json', 'r', encoding='utf-8') as f:
        merch_products = json.load(f)
    
    # Добавляем source_file для товаров из Мерч для Sense
    for product in merch_products:
        product['source_file'] = 'Мерч для Sense_1757934153.xlsx'
    
    # Объединяем только нужные товары
    all_products = original_products + merch_products
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    # Создаем записи о таблицах
    sheet_metadata = {}
    
    for product_data in all_products:
        source_file = product_data['source_file']
        
        # Создаем метаданные таблицы если их нет
        if source_file not in sheet_metadata:
            sheet_meta = db.create_sheet_metadata(
                sheet_url=f"https://docs.google.com/spreadsheets/d/{source_file}",
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
        
    print(f"✅ Загружено товаров: {len(all_products)}")

def add_images():
    """Добавляет изображения к товарам"""
    print("🖼️  Добавление изображений...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    # Получаем все товары
    with db.get_session() as session:
        from database.models_v4 import Product
        
        products = session.query(Product).all()
        
        for product in products:
            # Ищем изображения для товара
            image_files = []
            
            # Для оригинальной таблицы
            if product.sheet_id == 1:  # original_sheet
                # Ищем изображения в папке storage/images/products_original_sheet
                image_dir = "storage/images/products_original_sheet"
                if os.path.exists(image_dir):
                    for filename in os.listdir(image_dir):
                        if filename.endswith('.jpg'):
                            image_files.append(os.path.join(image_dir, filename))
            
            # Для Мерч для Sense (пока без изображений)
            elif product.sheet_id == 2:  # Мерч для Sense
                # Пока оставляем без изображений
                pass
            
            # Добавляем изображения в базу
            for i, image_path in enumerate(image_files[:2]):  # Максимум 2 изображения
                image_type = 'main' if i == 0 else 'additional'
                db.create_product_image(
                    product_id=product.id,
                    image_path=image_path,
                    image_type=image_type
                )
                print(f"  ✅ Добавлено изображение для {product.name}: {os.path.basename(image_path)}")

def main():
    """Основная функция"""
    print("🚀 Исправление базы данных")
    print("=" * 50)
    
    # Очищаем базу данных
    clear_database()
    
    # Загружаем исправленные данные
    load_corrected_data()
    
    # Добавляем изображения
    add_images()
    
    print("\n✅ Процесс завершен!")

if __name__ == "__main__":
    main()
