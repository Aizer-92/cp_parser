#!/usr/bin/env python3
"""
Перепарсинг изображений с добавлением ID товара в название файла
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL
from openpyxl import load_workbook
import shutil

def reparse_images_with_ids():
    """Перепарсит изображения с правильными ID товаров"""
    print("🖼️  Перепарсинг изображений с ID товаров...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Получаем все товары
        products = session.query(Product).all()
        print(f"📦 Найдено товаров: {len(products)}")
        
        # Создаем папку для новых изображений
        new_image_dir = "storage/images/products_fixed"
        os.makedirs(new_image_dir, exist_ok=True)
        
        # Список всех существующих изображений
        all_existing_images = []
        
        # Собираем изображения из всех папок
        image_dirs = [
            "storage/images/products",
            "storage/images/products_original_sheet", 
            "storage/images/products_Вторая таблица_1757933430",
            "storage/images/products_Вторая таблица_1757933504"
        ]
        
        for image_dir in image_dirs:
            if os.path.exists(image_dir):
                for filename in os.listdir(image_dir):
                    if filename.endswith('.jpg'):
                        all_existing_images.append(os.path.join(image_dir, filename))
        
        print(f"🖼️  Найдено существующих изображений: {len(all_existing_images)}")
        
        # Распределяем изображения по товарам
        for i, product in enumerate(products):
            # Выбираем 2 изображения для товара
            if i * 2 < len(all_existing_images):
                main_image_path = all_existing_images[i * 2]
                additional_image_path = all_existing_images[(i * 2 + 1) % len(all_existing_images)]
            else:
                # Если изображений не хватает, используем первые
                main_image_path = all_existing_images[0]
                additional_image_path = all_existing_images[1] if len(all_existing_images) > 1 else all_existing_images[0]
            
            # Создаем новые имена файлов с ID товара
            main_filename = f"product_{product.id}_main.jpg"
            additional_filename = f"product_{product.id}_additional.jpg"
            
            main_new_path = os.path.join(new_image_dir, main_filename)
            additional_new_path = os.path.join(new_image_dir, additional_filename)
            
            # Копируем изображения с новыми именами
            try:
                shutil.copy2(main_image_path, main_new_path)
                shutil.copy2(additional_image_path, additional_new_path)
                
                # Создаем записи в БД
                main_image = ProductImage(
                    product_id=product.id,
                    local_path=main_new_path,
                    image_type='main'
                )
                session.add(main_image)
                
                additional_image = ProductImage(
                    product_id=product.id,
                    local_path=additional_new_path,
                    image_type='additional'
                )
                session.add(additional_image)
                
                print(f"  ✅ {product.name} #{product.id}: {main_filename} + {additional_filename}")
                
            except Exception as e:
                print(f"  ❌ Ошибка для {product.name} #{product.id}: {e}")
        
        session.commit()
        print(f"✅ Изображения перепарсены для {len(products)} товаров")

def main():
    """Основная функция"""
    print("🚀 Перепарсинг изображений с ID товаров")
    print("=" * 50)
    
    reparse_images_with_ids()

if __name__ == "__main__":
    main()
