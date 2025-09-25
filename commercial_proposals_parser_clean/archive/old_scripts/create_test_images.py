#!/usr/bin/env python3
"""
Скрипт для создания тестовых изображений с правильной привязкой к товарам
"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage

def create_test_image(image_path, content="Test Image"):
    """Создает тестовое изображение"""
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, 'w') as f:
        f.write(content)

def create_test_images_with_correct_positioning():
    """Создает тестовые изображения с правильной привязкой к товарам"""
    session = DatabaseManager.get_session()
    
    print("=== СОЗДАНИЕ ТЕСТОВЫХ ИЗОБРАЖЕНИЙ С ПРАВИЛЬНОЙ ПРИВЯЗКОЙ ===\n")
    
    # Получаем все товары
    products = session.query(Product).all()
    
    total_created = 0
    
    for product in products:
        print(f"📦 Обрабатываем товар: {product.name}")
        print(f"   Диапазон строк: {product.start_row}-{product.end_row}")
        
        if not product.start_row or not product.end_row:
            print(f"   ⚠️  У товара не определен диапазон строк")
            continue
        
        # Создаем главное изображение для строки start_row
        main_image_path = f"storage/images/{product.sheet_id}_{product.id}_A{product.start_row}_main_{product.name.replace(' ', '_')}.png"
        create_test_image(main_image_path, f"Main image for {product.name} (row {product.start_row})")
        
        # Создаем запись об изображении
        main_image = ProductImage(
            product_id=product.id,
            local_path=main_image_path,
            image_type='main',
            file_size=len(f"Main image for {product.name} (row {product.start_row})"),
            width=100,
            height=100,
            format='png'
        )
        session.add(main_image)
        total_created += 1
        
        print(f"   ✅ Создано главное изображение: A{product.start_row}")
        
        # Создаем дополнительные изображения для других строк в диапазоне
        for row in range(product.start_row + 1, min(product.end_row + 1, product.start_row + 4)):  # Максимум 3 дополнительных
            additional_image_path = f"storage/images/{product.sheet_id}_{product.id}_B{row}_additional_{product.name.replace(' ', '_')}.png"
            create_test_image(additional_image_path, f"Additional image for {product.name} (row {row})")
            
            # Создаем запись об изображении
            additional_image = ProductImage(
                product_id=product.id,
                local_path=additional_image_path,
                image_type='additional',
                file_size=len(f"Additional image for {product.name} (row {row})"),
                width=100,
                height=100,
                format='png'
            )
            session.add(additional_image)
            total_created += 1
            
            print(f"   ✅ Создано дополнительное изображение: B{row}")
    
    session.commit()
    session.close()
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Создано изображений: {total_created}")
    print(f"\n✅ Создание тестовых изображений завершено!")

if __name__ == "__main__":
    try:
        create_test_images_with_correct_positioning()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

