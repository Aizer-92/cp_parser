#!/usr/bin/env python3
"""
Скрипт для правильной перезагрузки данных в базу данных
с учетом структуры: одна строка = один товар с изображениями и вариантами цен
"""

import json
import os
import sys
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def clear_database():
    """Очистка базы данных"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    try:
        # Удаляем все данные
        session.execute(text('DELETE FROM product_images'))
        session.execute(text('DELETE FROM price_offers'))
        session.execute(text('DELETE FROM products'))
        session.execute(text('DELETE FROM sheets_metadata'))
        session.commit()
        print("✅ База данных очищена")
    finally:
        session.close()

def load_products_from_json():
    """Загрузка товаров из JSON файла"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # Создаем метаданные листа
    sheet_id = db.create_sheet_metadata(
        sheet_url="https://docs.google.com/spreadsheets/d/example",
        sheet_title="Основная таблица"
    )
    
    with open('parsed_products.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📦 Загружаем {len(data)} товаров...")
    
    for i, item in enumerate(data, 1):
        print(f"\n{i}. {item['name']}")
        
        # Создаем товар
        product = db.create_product(
            name=item['name'],
            characteristics=item.get('characteristics', ''),
            custom_design=item.get('custom_design', ''),
            sheet_id=sheet_id
        )
        
        print(f"   ✅ Товар создан (ID: {product.id})")
        print(f"   📝 Характеристики: {item.get('characteristics', '')[:50]}...")
        print(f"   🎨 Кастом: {item.get('custom_design', '')}")
        
        # Создаем варианты цен
        price_offers = item.get('price_offers', [])
        print(f"   💰 Варианты цен: {len(price_offers)}")
        
        for offer in price_offers:
            db.create_price_offer(
                product_id=product.id,
                route_name=offer.get('route_name', ''),
                quantity=offer.get('quantity'),
                price_usd=offer.get('price_usd'),
                price_rub=offer.get('price_rub'),
                delivery_time=offer.get('delivery_time'),
                sample_price=offer.get('sample_price'),
                sample_time=offer.get('sample_time'),
                is_sample=offer.get('is_sample', False)
            )
            print(f"     - {offer.get('route_name', '')}: тираж {offer.get('quantity')}, USD {offer.get('price_usd')}, RUB {offer.get('price_rub')}")
        
        # Создаем изображения (пока заглушки, потом добавим реальные)
        # Основное изображение
        main_image_path = f"storage/images/products_parsed/product_{product.id}_main.jpg"
        if os.path.exists(main_image_path):
            db.create_product_image(
                product_id=product.id,
                image_path=main_image_path,
                image_type='main'
            )
            print(f"   🖼️  Основное изображение: {main_image_path}")
        
        # Дополнительные изображения
        additional_count = 1
        while True:
            add_image_path = f"storage/images/products_parsed/product_{product.id}_additional_{additional_count}.jpg"
            if os.path.exists(add_image_path):
                db.create_product_image(
                    product_id=product.id,
                    image_path=add_image_path,
                    image_type='additional'
                )
                print(f"   🖼️  Доп. изображение {additional_count}: {add_image_path}")
                additional_count += 1
            else:
                break

def main():
    print("🔄 Перезагрузка данных в базу данных...")
    
    # Очищаем базу данных
    clear_database()
    
    # Загружаем товары
    load_products_from_json()
    
    # Проверяем результат
    db = CommercialProposalsDB(DATABASE_URL_V4)
    stats = db.get_statistics()
    print(f"\n📊 Итоговая статистика:")
    print(f"   Товаров: {stats['total_products']}")
    print(f"   Вариантов цен: {stats['total_price_offers']}")
    print(f"   Изображений: {stats['total_images']}")

if __name__ == "__main__":
    main()
