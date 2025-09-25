#!/usr/bin/env python3
"""
Создание уникальных изображений для каждого товара
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL
import shutil
from PIL import Image

def create_unique_images():
    """Создает уникальные изображения для каждого товара"""
    print("🖼️  Создание уникальных изображений...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Получаем все товары
        products = session.query(Product).all()
        print(f"📦 Найдено товаров: {len(products)}")
        
        # Удаляем все существующие изображения
        session.query(ProductImage).delete()
        session.commit()
        print("🗑️  Удалены все записи об изображениях из БД")
        
        # Удаляем папку с изображениями
        import shutil
        image_dir = "storage/images/products_fixed"
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir)
        os.makedirs(image_dir, exist_ok=True)
        print(f"✅ Создана новая папка {image_dir}")
        
        # Собираем все рабочие изображения
        all_images = []
        source_dirs = [
            "storage/images/products",
            "storage/images/products_original_sheet", 
            "storage/images/products_Вторая таблица_1757933430",
            "storage/images/products_Вторая таблица_1757933504"
        ]
        
        for source_dir in source_dirs:
            if os.path.exists(source_dir):
                for filename in os.listdir(source_dir):
                    if filename.endswith('.jpg'):
                        filepath = os.path.join(source_dir, filename)
                        # Проверяем размер файла
                        if os.path.getsize(filepath) > 5000:  # Больше 5KB
                            all_images.append(filepath)
        
        print(f"🖼️  Найдено рабочих изображений: {len(all_images)}")
        
        # Создаем уникальные изображения для каждого товара
        used_images = set()
        
        for i, product in enumerate(products):
            # Выбираем 2 уникальных изображения для товара
            main_image = None
            additional_image = None
            
            # Ищем основное изображение
            for img_path in all_images:
                if img_path not in used_images:
                    main_image = img_path
                    used_images.add(img_path)
                    break
            
            # Ищем дополнительное изображение
            for img_path in all_images:
                if img_path not in used_images:
                    additional_image = img_path
                    used_images.add(img_path)
                    break
            
            # Если не нашли уникальные, используем первые доступные
            if not main_image:
                main_image = all_images[0] if all_images else None
            if not additional_image:
                additional_image = all_images[1] if len(all_images) > 1 else all_images[0] if all_images else None
            
            if main_image and additional_image:
                # Создаем новые имена файлов
                main_filename = f"product_{product.id}_main.jpg"
                additional_filename = f"product_{product.id}_additional.jpg"
                
                main_new_path = os.path.join(image_dir, main_filename)
                additional_new_path = os.path.join(image_dir, additional_filename)
                
                try:
                    # Копируем изображения
                    shutil.copy2(main_image, main_new_path)
                    shutil.copy2(additional_image, additional_new_path)
                    
                    # Создаем записи в БД
                    main_img = ProductImage(
                        product_id=product.id,
                        local_path=main_new_path,
                        image_type='main'
                    )
                    session.add(main_img)
                    
                    additional_img = ProductImage(
                        product_id=product.id,
                        local_path=additional_new_path,
                        image_type='additional'
                    )
                    session.add(additional_img)
                    
                    print(f"  ✅ {product.name} #{product.id}: {main_filename} + {additional_filename}")
                    
                except Exception as e:
                    print(f"  ❌ Ошибка для {product.name} #{product.id}: {e}")
            else:
                print(f"  ❌ Не найдены изображения для {product.name} #{product.id}")
        
        session.commit()
        print(f"✅ Созданы уникальные изображения для {len(products)} товаров")

def main():
    """Основная функция"""
    print("🚀 Создание уникальных изображений")
    print("=" * 50)
    
    create_unique_images()

if __name__ == "__main__":
    main()
