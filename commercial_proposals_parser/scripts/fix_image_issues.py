#!/usr/bin/env python3
"""
Исправление проблем с изображениями
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
import shutil

def clear_all_images():
    """Очищает все изображения из БД и файловой системы"""
    print("🧹 Очищаем все изображения...")
    
    db = CommercialProposalsDB('sqlite:///commercial_proposals_v4.db')
    
    # Удаляем записи из БД
    with db.get_session() as session:
        from database.models_v4 import ProductImage
        deleted_count = session.query(ProductImage).count()
        session.query(ProductImage).delete()
        session.commit()
        print(f"✅ Удалено записей об изображениях из БД: {deleted_count}")
    
    # Очищаем папку с изображениями
    if os.path.exists('storage/images/products_parsed'):
        shutil.rmtree('storage/images/products_parsed')
        print("✅ Очищена папка storage/images/products_parsed")
    
    os.makedirs('storage/images/products_parsed', exist_ok=True)
    print("✅ Создана новая папка storage/images/products_parsed")

def create_correct_image_mapping():
    """Создает правильную привязку изображений к товарам"""
    print("🔗 Создаем правильную привязку изображений...")
    
    db = CommercialProposalsDB('sqlite:///commercial_proposals_v4.db')
    
    # Получаем все товары
    products = db.get_all_products_with_details(limit=1000)
    products_by_name = {}
    
    for product, _, _ in products:
        normalized_name = product.name.lower().strip()
        if normalized_name not in products_by_name:
            products_by_name[normalized_name] = []
        products_by_name[normalized_name].append(product)
    
    print(f"📦 Найдено товаров: {len(products)}")
    
    # Правильная привязка изображений на основе названий товаров
    image_mappings = {
        'кардхолдер': {
            'main_image': 'storage/images/products_parsed/product_1_main.jpg',
            'additional_images': []
        },
        'обложка для паспорта': {
            'main_image': 'storage/images/products_parsed/product_2_main.jpg',
            'additional_images': []
        },
        'футляр для очков': {
            'main_image': 'storage/images/products_parsed/product_3_main.jpg',
            'additional_images': []
        },
        'ручка': {
            'main_image': 'storage/images/products_parsed/product_4_main.jpg',
            'additional_images': []
        },
        'таблетница': {
            'main_image': 'storage/images/products_parsed/product_5_main.jpg',
            'additional_images': []
        },
        'набор карандашей 6 цветов': {
            'main_image': 'storage/images/products_parsed/product_6_main.jpg',
            'additional_images': []
        },
        'кружка': {
            'main_image': 'storage/images/products_parsed/product_7_main.jpg',
            'additional_images': []
        },
        'ежедневник': {
            'main_image': 'storage/images/products_parsed/product_8_main.jpg',
            'additional_images': ['storage/images/products_parsed/product_8_additional_1.jpg']
        }
    }
    
    # Копируем изображения из существующих файлов
    source_images = {
        'кардхолдер': 'storage/images/products_parsed/product_1_original_sheet_3.jpg',
        'обложка для паспорта': 'storage/images/products_parsed/product_2_original_sheet_1.jpg',
        'футляр для очков': 'storage/images/products_parsed/product_3_original_sheet_2.jpg',
        'ручка': 'storage/images/products_parsed/product_4_original_sheet_8.jpg',
        'таблетница': 'storage/images/products_parsed/product_5_original_sheet_9.jpg',
        'набор карандашей 6 цветов': 'storage/images/products_parsed/product_6_original_sheet_12.jpg',
        'кружка': 'storage/images/products_parsed/product_7_original_sheet_13.jpg',
        'ежедневник': 'storage/images/products_parsed/product_8_Вторая таблица_1757933430_19.jpg'
    }
    
    mapped_count = 0
    
    for normalized_name, mapping in image_mappings.items():
        if normalized_name in products_by_name:
            products = products_by_name[normalized_name]
            for product in products:
                # Создаем основное изображение
                if normalized_name in source_images and os.path.exists(source_images[normalized_name]):
                    main_image_path = mapping['main_image']
                    shutil.copy2(source_images[normalized_name], main_image_path)
                    
                    db.create_product_image(
                        product_id=product.id,
                        image_path=main_image_path,
                        image_type='main'
                    )
                    mapped_count += 1
                    print(f"  ✅ {product.name} -> {main_image_path} (main)")
                
                # Создаем дополнительные изображения
                for i, additional_path in enumerate(mapping['additional_images']):
                    if os.path.exists(additional_path):
                        db.create_product_image(
                            product_id=product.id,
                            image_path=additional_path,
                            image_type='additional'
                        )
                        mapped_count += 1
                        print(f"  ✅ {product.name} -> {additional_path} (additional)")
    
    print(f"\n✅ Привязано изображений: {mapped_count}")

def main():
    """Основная функция"""
    print("🔧 Исправление проблем с изображениями")
    print("=" * 50)
    
    # Очищаем все изображения
    clear_all_images()
    
    # Создаем правильную привязку
    create_correct_image_mapping()
    
    print("\n✅ Исправление завершено!")

if __name__ == "__main__":
    main()
