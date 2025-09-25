#!/usr/bin/env python3
"""
Проверка уникальности изображений
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def check_image_uniqueness():
    """Проверяет уникальность изображений"""
    print("🔍 Проверка уникальности изображений...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage
        
        # Получаем все изображения
        images = session.query(ProductImage).all()
        print(f"📊 Всего изображений в БД: {len(images)}")
        
        # Проверяем уникальность путей
        paths = [img.local_path for img in images]
        unique_paths = set(paths)
        
        print(f"📊 Уникальных путей: {len(unique_paths)}")
        
        if len(paths) != len(unique_paths):
            print("❌ Найдены дублирующиеся пути!")
            duplicates = []
            for path in paths:
                if paths.count(path) > 1 and path not in duplicates:
                    duplicates.append(path)
            
            for dup in duplicates:
                print(f"  - {dup} (встречается {paths.count(dup)} раз)")
        else:
            print("✅ Все пути уникальны!")
        
        # Проверяем размеры файлов
        print("\n📏 Проверка размеров файлов:")
        broken_count = 0
        for img in images:
            if os.path.exists(img.local_path):
                size = os.path.getsize(img.local_path)
                if size < 1000:  # Меньше 1KB
                    print(f"  ❌ {img.local_path}: {size} байт (битое)")
                    broken_count += 1
                else:
                    print(f"  ✅ {img.local_path}: {size} байт")
            else:
                print(f"  ❌ {img.local_path}: файл не найден")
                broken_count += 1
        
        print(f"\n📊 Битых файлов: {broken_count}")
        
        # Показываем первые 5 товаров
        print("\n🎯 Первые 5 товаров:")
        products = session.query(Product).limit(5).all()
        for product in products:
            product_images = session.query(ProductImage).filter(ProductImage.product_id == product.id).all()
            print(f"\n📦 {product.name} #{product.id}:")
            for img in product_images:
                size = os.path.getsize(img.local_path) if os.path.exists(img.local_path) else 0
                print(f"  - {img.local_path} (тип: {img.image_type}, размер: {size} байт)")

def main():
    """Основная функция"""
    print("🚀 Проверка уникальности изображений")
    print("=" * 50)
    
    check_image_uniqueness()

if __name__ == "__main__":
    main()
