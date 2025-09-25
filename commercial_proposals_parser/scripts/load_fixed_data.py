#!/usr/bin/env python3
"""
Загрузка исправленных данных с правильными тиражами
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import shutil
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

def copy_existing_images():
    """Копирует существующие изображения в правильную структуру"""
    print("🖼️  Копирование существующих изображений...")
    
    # Создаем папку для изображений
    images_dir = "storage/images/products_fixed"
    os.makedirs(images_dir, exist_ok=True)
    
    # Копируем изображения из существующих папок
    source_dirs = [
        "storage/images/products",
        "storage/images/products_original_sheet",
        "storage/images/products_Вторая таблица_1757933430"
    ]
    
    copied_count = 0
    for source_dir in source_dirs:
        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                if filename.endswith('.jpg'):
                    source_path = os.path.join(source_dir, filename)
                    dest_path = os.path.join(images_dir, filename)
                    
                    try:
                        shutil.copy2(source_path, dest_path)
                        copied_count += 1
                        print(f"  ✅ Скопировано: {filename}")
                    except Exception as e:
                        print(f"  ❌ Ошибка копирования {filename}: {e}")
    
    print(f"✅ Скопировано изображений: {copied_count}")

def load_products():
    """Загружает товары из всех источников"""
    print("📦 Загрузка товаров...")
    
    # Загружаем исправленную оригинальную таблицу
    with open('correct_parsed_products.json', 'r', encoding='utf-8') as f:
        original_products = json.load(f)
    
    # Загружаем товары из Мерч для Sense
    with open('merch_sense_products.json', 'r', encoding='utf-8') as f:
        merch_products = json.load(f)
    
    # Добавляем source_file для товаров из Мерч для Sense
    for product in merch_products:
        product['source_file'] = 'Мерч для Sense_1757934153.xlsx'
    
    # Загружаем ежедневники из Вторая таблица
    with open('parsed_products.json', 'r', encoding='utf-8') as f:
        all_products = json.load(f)
    
    daily_planner_products = [p for p in all_products if 'Вторая таблица' in p['source_file']]
    
    # Объединяем все товары
    all_products = original_products + daily_planner_products + merch_products
    
    print(f"  - Оригинальная таблица (исправленная): {len(original_products)} товаров")
    print(f"  - Вторая таблица (ежедневники): {len(daily_planner_products)} товаров")
    print(f"  - Мерч для Sense: {len(merch_products)} товаров")
    print(f"  - Всего: {len(all_products)} товаров")
    
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
            
            # Ищем изображения в папке products_fixed
            image_dir = "storage/images/products_fixed"
            if os.path.exists(image_dir):
                for filename in os.listdir(image_dir):
                    if filename.endswith('.jpg'):
                        # Простая привязка по названию товара
                        if any(keyword in filename.lower() for keyword in product.name.lower().split()):
                            full_path = f"storage/images/products_fixed/{filename}"
                            image_files.append(full_path)
            
            # Если не нашли по названию, берем первые доступные
            if not image_files and os.path.exists(image_dir):
                available_images = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
                if available_images:
                    # Берем первые 2 изображения
                    for i, filename in enumerate(available_images[:2]):
                        full_path = f"storage/images/products_fixed/{filename}"
                        image_files.append(full_path)
            
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
    print("🚀 Загрузка исправленных данных")
    print("=" * 50)
    
    # Очищаем базу данных
    clear_database()
    
    # Копируем изображения
    copy_existing_images()
    
    # Загружаем товары
    load_products()
    
    # Добавляем изображения
    add_images()
    
    print("\n✅ Процесс завершен!")

if __name__ == "__main__":
    main()
