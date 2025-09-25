#!/usr/bin/env python3
"""
Финальная правильная привязка изображений к товарам
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from openpyxl import load_workbook
import shutil
from PIL import Image
import io

sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
from sqlalchemy import text

def fix_image_mapping_final():
    """Финальная правильная привязка изображений к товарам"""
    
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # 1. Очищаем существующие изображения для товаров "Мерч для Sense"
    print("🧹 Очищаем существующие изображения для товаров 'Мерч для Sense'...")
    session = db.get_session()
    try:
        session.execute(text('DELETE FROM product_images WHERE product_id >= 29'))
        session.commit()
        print("✅ Очищены изображения для товаров 'Мерч для Sense'")
    finally:
        session.close()
    
    # 2. Очищаем папку для изображений
    images_output_dir = "storage/images/products_parsed"
    if os.path.exists(images_output_dir):
        # Удаляем только изображения товаров "Мерч для Sense"
        for file in os.listdir(images_output_dir):
            if file.startswith('product_') and any(name in file for name in ['Худи', 'ШАПКА', 'ШОППЕР', 'Брелоки', 'ДУТЫЙ', 'Зонт', 'Письменный', 'Термокружка', 'Сумка', 'Шоппер']):
                os.remove(os.path.join(images_output_dir, file))
        print(f"✅ Очищены изображения товаров 'Мерч для Sense' из папки")
    
    # 3. Правильная привязка изображений к товарам
    print(f"\n🔗 Создаем правильную привязку изображений...")
    
    # Маппинг товаров к их изображениям (на основе анализа)
    product_image_mapping = {
        'Худи': {
            'main': ['image_01_image24.jpg'],
            'additional': []
        },
        'ШАПКА-БИНИ': {
            'main': ['image_02_image9.png'],
            'additional': ['image_03_image37.jpg', 'image_04_image29.png', 'image_05_image16.png', 'image_06_image12.png']
        },
        'ШОППЕР': {
            'main': ['image_07_image25.png'],
            'additional': ['image_08_image32.png', 'image_09_image34.png', 'image_10_image4.png', 'image_11_image41.jpg']
        },
        'ДУТЫЙ ЧЕХОЛ ДЛЯ НОУТБУКА': {
            'main': ['image_12_image15.png'],
            'additional': ['image_13_image20.jpg']
        },
        'Зонт': {
            'main': ['image_14_image28.png'],
            'additional': ['image_15_image38.jpg', 'image_16_image33.jpg', 'image_17_image11.png']
        },
        'Письменный набор': {
            'main': ['image_18_image8.jpg'],
            'additional': ['image_19_image3.png', 'image_20_image42.jpg', 'image_21_image27.png', 'image_22_image2.png']
        },
        'Термокружка': {
            'main': ['image_23_image18.jpg'],
            'additional': ['image_24_image7.png', 'image_25_image22.jpg', 'image_26_image21.jpg', 'image_27_image35.jpg']
        },
        'Сумка': {
            'main': ['image_28_image30.png'],
            'additional': []
        },
        'Шоппер': {
            'main': ['image_29_image26.jpg', 'image_30_image19.jpg'],
            'additional': ['image_31_image6.png', 'image_32_image23.png', 'image_33_image36.png', 'image_34_image39.png', 'image_35_image10.png']
        },
        'сумка  дутая': {
            'main': ['image_36_image17.png'],
            'additional': []
        },
        'Косметичка': {
            'main': ['image_37_image5.png'],
            'additional': []
        },
        'Брелоки': {
            'main': ['image_38_image40.jpg', 'image_39_image13.png'],
            'additional': ['image_40_image31.png', 'image_41_image1.png']
        },
        'Футболка': {
            'main': ['image_42_image14.jpg'],
            'additional': []
        }
    }
    
    # 4. Получаем товары из БД
    products_with_details = db.get_all_products_with_details(limit=50)
    merch_sense_products = [(p, po, im) for p, po, im in products_with_details if p.id >= 29]
    
    # Создаем словарь для сопоставления имен товаров
    product_name_map = {}
    for product, price_offers, images in merch_sense_products:
        product_name_map[product.name.strip().lower()] = product
    
    print(f"📦 Товары 'Мерч для Sense' в БД:")
    for product, price_offers, images in merch_sense_products:
        print(f"  {product.id}. {product.name}")
    
    # 5. Привязываем изображения к товарам
    mapped_count = 0
    
    for product_name, images_info in product_image_mapping.items():
        product_name_lower = product_name.strip().lower()
        
        if product_name_lower in product_name_map:
            product = product_name_map[product_name_lower]
            
            print(f"\n📦 {product.name} (ID: {product.id}):")
            
            # Основные изображения
            for i, image_name in enumerate(images_info['main']):
                original_path = os.path.join(images_output_dir, image_name)
                if os.path.exists(original_path):
                    new_image_name = f"product_{product.id}_main_{i+1}.jpg"
                    new_image_path = os.path.join(images_output_dir, new_image_name)
                    
                    # Копируем изображение
                    shutil.copy2(original_path, new_image_path)
                    
                    # Сохраняем в БД
                    db.create_product_image(
                        product_id=product.id,
                        image_path=f"storage/images/products_parsed/{new_image_name}",
                        image_type='main'
                    )
                    
                    print(f"  ✅ Основное {i+1}: {new_image_name}")
                    mapped_count += 1
                else:
                    print(f"  ❌ Изображение не найдено: {original_path}")
            
            # Дополнительные изображения
            for i, image_name in enumerate(images_info['additional']):
                original_path = os.path.join(images_output_dir, image_name)
                if os.path.exists(original_path):
                    new_image_name = f"product_{product.id}_additional_{i+1}.jpg"
                    new_image_path = os.path.join(images_output_dir, new_image_name)
                    
                    # Копируем изображение
                    shutil.copy2(original_path, new_image_path)
                    
                    # Сохраняем в БД
                    db.create_product_image(
                        product_id=product.id,
                        image_path=f"storage/images/products_parsed/{new_image_name}",
                        image_type='additional'
                    )
                    
                    print(f"  ✅ Дополнительное {i+1}: {new_image_name}")
                    mapped_count += 1
                else:
                    print(f"  ❌ Изображение не найдено: {original_path}")
        else:
            print(f"  ⚠️ Товар '{product_name}' не найден в БД")
    
    print(f"\n✅ Финальная привязка завершена! Привязано {mapped_count} изображений.")
    
    # 6. Проверяем результат
    print(f"\n📊 Проверяем результат:")
    for product, price_offers, images in merch_sense_products:
        main_images = [img for img in images if img.image_type == 'main']
        additional_images = [img for img in images if img.image_type == 'additional']
        print(f"  {product.name} (ID: {product.id}) - {len(main_images)} основных, {len(additional_images)} дополнительных")

if __name__ == "__main__":
    fix_image_mapping_final()