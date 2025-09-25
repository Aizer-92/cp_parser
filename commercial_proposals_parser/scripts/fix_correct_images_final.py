#!/usr/bin/env python3
"""
Финальное исправление изображений - используем оригинальные изображения
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def clear_existing_images():
    """Очищает существующие изображения в базе данных"""
    print("🧹 Очищаем существующие изображения...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import ProductImage
        
        # Удаляем все записи об изображениях
        session.query(ProductImage).delete()
        session.commit()
        print("✅ Очищены записи об изображениях в БД")
    
    # Очищаем папку с изображениями
    images_dir = "storage/images/products_correct"
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)
        print(f"✅ Очищена папка {images_dir}")
    
    os.makedirs(images_dir, exist_ok=True)
    print(f"✅ Создана новая папка {images_dir}")

def get_original_images_mapping():
    """Создает правильное соответствие товаров и оригинальных изображений"""
    
    # Маппинг товаров и их правильных изображений из оригинальных папок
    product_image_mapping = {
        # Ежедневники (разные тиражи - один товар)
        1: {
            'name': 'Ежедневник',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_1_col_1_18.jpg',  # Основное изображение
                'product_row_1_col_18_19.jpg'  # Дополнительное изображение
            ]
        },
        
        # Худи
        12: {
            'name': 'Худи',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_11_col_1_11.jpg',  # Основное изображение
                'product_row_11_col_18_13.jpg'  # Дополнительное изображение
            ]
        },
        
        # Шапка-бини
        13: {
            'name': 'ШАПКА-БИНИ',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_13_col_1_12.jpg',  # Основное изображение
                'product_row_13_col_18_14.jpg'  # Дополнительное изображение
            ]
        },
        
        # Шоппер
        14: {
            'name': 'ШОППЕР',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_13_col_18_14.jpg',  # Основное изображение
                'product_row_13_col_18_15.jpg'   # Дополнительное изображение
            ]
        },
        
        # Брелоки
        15: {
            'name': 'Брелоки',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_13_col_18_15.jpg',  # Основное изображение
                'product_row_13_col_18_16.jpg'   # Дополнительное изображение
            ]
        },
        
        # Таблетница
        16: {
            'name': 'Таблетница',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_13_col_18_16.jpg',  # Основное изображение
                'product_row_13_col_18_17.jpg'   # Дополнительное изображение
            ]
        },
        
        # Кардхолдер
        17: {
            'name': 'Кардхолдер',
            'source_folder': 'products_original_sheet',
            'images': [
                'product_row_13_col_18_17.jpg',  # Основное изображение
                'product_row_13_col_18_18.jpg'   # Дополнительное изображение
            ]
        },
        
        # Товары из Мерч для Sense
        18: {
            'name': 'Зонт',
            'source_folder': 'products_Мерч для Sense_1757934153',
            'images': [
                'product_row_1_col_1_1.jpg',  # Основное изображение
                'product_row_1_col_1_2.jpg'   # Дополнительное изображение
            ]
        },
        
        19: {
            'name': 'Письменный набор',
            'source_folder': 'products_Мерч для Sense_1757934153',
            'images': [
                'product_row_1_col_1_2.jpg',  # Основное изображение
                'product_row_1_col_1_3.jpg'   # Дополнительное изображение
            ]
        },
        
        20: {
            'name': 'Термокружка',
            'source_folder': 'products_Мерч для Sense_1757934153',
            'images': [
                'product_row_1_col_1_3.jpg',  # Основное изображение
                'product_row_1_col_1_4.jpg'   # Дополнительное изображение
            ]
        },
        
        21: {
            'name': 'Сумка',
            'source_folder': 'products_Мерч для Sense_1757934153',
            'images': [
                'product_row_1_col_1_4.jpg',  # Основное изображение
                'product_row_1_col_1_5.jpg'   # Дополнительное изображение
            ]
        },
        
        22: {
            'name': 'Шоппер',
            'source_folder': 'products_Мерч для Sense_1757934153',
            'images': [
                'product_row_1_col_1_5.jpg',  # Основное изображение
                'product_row_1_col_1_6.jpg'   # Дополнительное изображение
            ]
        },
        
        23: {
            'name': 'Шоппер',
            'source_folder': 'products_Мерч для Sense_1757934153',
            'images': [
                'product_row_1_col_1_6.jpg',  # Основное изображение
                'product_row_1_col_1_7.jpg'   # Дополнительное изображение
            ]
        }
    }
    
    return product_image_mapping

def assign_correct_images():
    """Привязывает правильные изображения к товарам"""
    print("🔗 Привязываем правильные изображения к товарам...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    product_mapping = get_original_images_mapping()
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Получаем все товары
        products = session.query(Product).all()
        print(f"📦 Найдено товаров в БД: {len(products)}")
        
        assigned_count = 0
        
        for product in products:
            if product.id in product_mapping:
                mapping = product_mapping[product.id]
                source_folder = mapping['source_folder']
                print(f"\n📦 {product.name} #{product.id} (из {source_folder}):")
                
                # Копируем и привязываем изображения
                for i, image_name in enumerate(mapping['images']):
                    source_path = f"storage/images/{source_folder}/{image_name}"
                    
                    if os.path.exists(source_path):
                        # Создаем новое имя файла
                        new_image_name = f"product_{product.id}_{i+1}.jpg"
                        new_image_path = f"storage/images/products_correct/{new_image_name}"
                        
                        try:
                            # Копируем изображение
                            shutil.copy2(source_path, new_image_path)
                            
                            # Создаем запись в БД
                            image_type = 'main' if i == 0 else 'additional'
                            product_image = ProductImage(
                                product_id=product.id,
                                local_path=new_image_path,
                                image_type=image_type
                            )
                            session.add(product_image)
                            assigned_count += 1
                            
                            print(f"  ✅ {image_name} -> {new_image_name} ({image_type})")
                            
                        except Exception as e:
                            print(f"  ❌ Ошибка при копировании {image_name}: {e}")
                    else:
                        print(f"  ⚠️  Изображение не найдено: {source_path}")
            else:
                print(f"⚠️  Нет маппинга для товара {product.name} #{product.id}")
        
        session.commit()
        print(f"\n✅ Привязано изображений: {assigned_count}")

def create_unique_fallback_images():
    """Создает уникальные резервные изображения для товаров без изображений"""
    print("🔄 Создаем уникальные резервные изображения...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Получаем товары без изображений
        products_without_images = session.query(Product).outerjoin(ProductImage).filter(ProductImage.id.is_(None)).all()
        
        print(f"📦 Товаров без изображений: {len(products_without_images)}")
        
        # Используем разные изображения как шаблоны
        template_images = [
            "storage/images/products_original_sheet/product_row_1_col_1_18.jpg",
            "storage/images/products_original_sheet/product_row_11_col_1_11.jpg",
            "storage/images/products_original_sheet/product_row_13_col_1_12.jpg",
            "storage/images/products_original_sheet/product_row_13_col_18_14.jpg",
            "storage/images/products_original_sheet/product_row_13_col_18_15.jpg"
        ]
        
        template_index = 0
        
        for product in products_without_images:
            if template_index < len(template_images):
                template_path = template_images[template_index]
                
                if os.path.exists(template_path):
                    new_image_name = f"product_{product.id}_fallback.jpg"
                    new_image_path = f"storage/images/products_correct/{new_image_name}"
                    
                    try:
                        shutil.copy2(template_path, new_image_path)
                        
                        # Создаем запись в БД
                        product_image = ProductImage(
                            product_id=product.id,
                            local_path=new_image_path,
                            image_type='main'
                        )
                        session.add(product_image)
                        
                        print(f"  ✅ {product.name} #{product.id} -> {new_image_name} (fallback)")
                        template_index += 1
                        
                    except Exception as e:
                        print(f"  ❌ Ошибка при создании fallback для {product.name}: {e}")
        
        session.commit()

def main():
    """Основная функция"""
    print("🚀 Финальное исправление изображений с оригинальными файлами")
    
    # Очищаем существующие данные
    clear_existing_images()
    
    # Привязываем правильные изображения к товарам
    assign_correct_images()
    
    # Создаем уникальные резервные изображения
    create_unique_fallback_images()
    
    print("\n✅ Финальное исправление изображений завершено!")
    
    # Показываем статистику
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        total_products = session.query(Product).count()
        total_images = session.query(ProductImage).count()
        products_with_images = session.query(Product).join(ProductImage).distinct().count()
        
        print(f"\n📊 Статистика:")
        print(f"  📦 Всего товаров: {total_products}")
        print(f"  🖼️  Всего изображений: {total_images}")
        print(f"  ✅ Товаров с изображениями: {products_with_images}")

if __name__ == "__main__":
    main()
