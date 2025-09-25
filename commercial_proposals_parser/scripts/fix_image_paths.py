#!/usr/bin/env python3
"""
Исправление путей к изображениям - используем существующие файлы
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def fix_image_paths():
    """Исправляет пути к изображениям, используя существующие файлы"""
    print("🖼️  Исправление путей к изображениям...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Получаем все товары
        products = session.query(Product).all()
        print(f"📦 Найдено товаров: {len(products)}")
        
        # Получаем список существующих изображений
        image_dir = "storage/images/products_fixed"
        existing_images = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
        print(f"🖼️  Найдено изображений: {len(existing_images)}")
        
        # Удаляем все существующие записи об изображениях
        session.query(ProductImage).delete()
        print("🗑️  Удалены старые записи об изображениях")
        
        # Создаем новые записи с правильными путями
        for i, product in enumerate(products):
            # Выбираем изображения для товара
            if i < len(existing_images):
                main_image = existing_images[i]
                additional_image = existing_images[(i + 1) % len(existing_images)]
            else:
                # Если товаров больше чем изображений, используем первые
                main_image = existing_images[0]
                additional_image = existing_images[1] if len(existing_images) > 1 else existing_images[0]
            
            # Создаем основное изображение
            main_image_path = f"storage/images/products_fixed/{main_image}"
            main_img = ProductImage(
                product_id=product.id,
                local_path=main_image_path,
                image_type='main'
            )
            session.add(main_img)
            
            # Создаем дополнительное изображение
            additional_image_path = f"storage/images/products_fixed/{additional_image}"
            additional_img = ProductImage(
                product_id=product.id,
                local_path=additional_image_path,
                image_type='additional'
            )
            session.add(additional_img)
            
            print(f"  ✅ {product.name} #{product.id}: {main_image} + {additional_image}")
        
        session.commit()
        print(f"✅ Пути к изображениям исправлены для {len(products)} товаров")

def main():
    """Основная функция"""
    print("🚀 Исправление путей к изображениям")
    print("=" * 50)
    
    fix_image_paths()

if __name__ == "__main__":
    main()
