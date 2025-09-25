#!/usr/bin/env python3
"""
Финальное исправление изображений с использованием существующих файлов
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
import shutil
import glob

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

def find_and_map_images():
    """Находит и правильно привязывает изображения"""
    print("🔍 Ищем и привязываем изображения...")
    
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
    
    # Находим все изображения
    image_dirs = [
        'storage/images/products_original_sheet',
        'storage/images/products_Вторая таблица_1757933430',
        'storage/images/products_Вторая таблица_1757933504'
    ]
    
    all_images = []
    for img_dir in image_dirs:
        if os.path.exists(img_dir):
            images = glob.glob(os.path.join(img_dir, "*.jpg")) + glob.glob(os.path.join(img_dir, "*.png"))
            all_images.extend(images)
    
    print(f"🖼️  Найдено изображений: {len(all_images)}")
    
    # Правильная привязка на основе названий товаров
    product_image_mapping = {
        'кардхолдер': ['product_row_4_col_18_3.jpg', 'product_row_4_col_18_4.jpg'],
        'обложка для паспорта': ['product_row_5_col_1_0.jpg', 'product_row_5_col_18_4.jpg'],
        'футляр для очков': ['product_row_6_col_1_1.jpg', 'product_row_6_col_18_16.jpg', 'product_row_6_col_18_17.jpg'],
        'ручка': ['product_row_7_col_1_7.jpg', 'product_row_7_col_18_9.jpg', 'product_row_7_col_18_10.jpg'],
        'таблетница': ['product_row_9_col_1_8.jpg', 'product_row_9_col_18_5.jpg', 'product_row_9_col_18_6.jpg'],
        'набор карандашей 6 цветов': ['product_row_11_col_1_11.jpg', 'product_row_11_col_18_13.jpg'],
        'кружка': ['product_row_13_col_1_12.jpg', 'product_row_13_col_18_14.jpg', 'product_row_13_col_18_15.jpg'],
        'ежедневник': ['product_row_4_col_1_0.jpg', 'product_row_4_col_15_1.jpg', 'product_row_1_col_1_2.jpg']
    }
    
    mapped_count = 0
    
    for normalized_name, image_patterns in product_image_mapping.items():
        if normalized_name in products_by_name:
            products = products_by_name[normalized_name]
            for product in products:
                # Ищем изображения для этого товара
                found_images = []
                for img_path in all_images:
                    img_name = os.path.basename(img_path)
                    for pattern in image_patterns:
                        if pattern in img_name:
                            found_images.append(img_path)
                            break
                
                # Привязываем найденные изображения
                for i, img_path in enumerate(found_images):
                    if os.path.exists(img_path):
                        # Создаем новое имя файла
                        new_name = f"product_{product.id}_{'main' if i == 0 else f'additional_{i}'}.jpg"
                        new_path = os.path.join('storage/images/products_parsed', new_name)
                        
                        # Копируем изображение
                        shutil.copy2(img_path, new_path)
                        
                        # Создаем запись в БД
                        image_type = 'main' if i == 0 else 'additional'
                        db.create_product_image(
                            product_id=product.id,
                            image_path=new_path,
                            image_type=image_type
                        )
                        mapped_count += 1
                        print(f"  ✅ {product.name} -> {new_name} ({image_type})")
    
    print(f"\n✅ Привязано изображений: {mapped_count}")

def main():
    """Основная функция"""
    print("🔧 Финальное исправление изображений")
    print("=" * 50)
    
    # Очищаем все изображения
    clear_all_images()
    
    # Находим и привязываем изображения
    find_and_map_images()
    
    print("\n✅ Исправление завершено!")

if __name__ == "__main__":
    main()
