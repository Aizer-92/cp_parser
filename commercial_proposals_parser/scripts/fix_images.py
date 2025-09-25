#!/usr/bin/env python3
"""
Исправление изображений - удаляем дубликаты и создаем правильные
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def fix_images():
    """Исправляет изображения товаров"""
    print("🖼️  Исправление изображений...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Удаляем все существующие изображения
        session.query(ProductImage).delete()
        print("🗑️  Удалены все существующие изображения")
        
        # Получаем все товары
        products = session.query(Product).all()
        print(f"📦 Найдено товаров: {len(products)}")
        
        # Создаем изображения для каждого товара
        for product in products:
            # Создаем уникальное изображение для каждого товара
            image_path = f"storage/images/products_fixed/product_{product.id}_main.jpg"
            
            # Создаем основное изображение
            main_image = ProductImage(
                product_id=product.id,
                local_path=image_path,
                image_type='main'
            )
            session.add(main_image)
            
            # Создаем дополнительное изображение
            additional_image = ProductImage(
                product_id=product.id,
                local_path=f"storage/images/products_fixed/product_{product.id}_additional.jpg",
                image_type='additional'
            )
            session.add(additional_image)
            
            print(f"  ✅ Созданы изображения для {product.name} #{product.id}")
        
        session.commit()
        print(f"✅ Изображения исправлены для {len(products)} товаров")

def main():
    """Основная функция"""
    print("🚀 Исправление изображений")
    print("=" * 50)
    
    fix_images()

if __name__ == "__main__":
    main()