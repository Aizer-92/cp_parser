#!/usr/bin/env python3
"""
Скрипт для правильной классификации изображений:
- Главные изображения (main) - только из столбца A
- Дополнительные изображения (additional) - из других столбцов
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage
import re

def extract_row_from_image_path(image_path):
    """Извлекает номер строки из пути к изображению"""
    if not image_path:
        return None
    
    # Ищем паттерн _image\d+ или _row\d+ в пути
    patterns = [
        r'_image(\d+)',
        r'_row(\d+)',
        r'image(\d+)',
        r'row(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, image_path)
        if match:
            return int(match.group(1))
    
    return None

def fix_image_classification():
    """Исправляет классификацию изображений на основе их позиции"""
    session = DatabaseManager.get_session()
    
    print("=== ИСПРАВЛЕНИЕ КЛАССИФИКАЦИИ ИЗОБРАЖЕНИЙ ===\n")
    
    # Получаем все товары с их диапазонами строк
    products = session.query(Product).filter(
        Product.start_row.isnot(None),
        Product.end_row.isnot(None)
    ).all()
    
    print(f"Найдено товаров с диапазонами строк: {len(products)}")
    
    # Получаем все изображения
    images = session.query(ProductImage).all()
    print(f"Найдено изображений: {len(images)}\n")
    
    fixed_count = 0
    main_images_count = 0
    additional_images_count = 0
    
    for image in images:
        # Извлекаем номер строки из пути к изображению
        image_row = extract_row_from_image_path(image.local_path)
        
        if image_row is None:
            print(f"⚠️  Не удалось извлечь номер строки из: {image.local_path}")
            continue
        
        # Ищем товар, в диапазон строк которого попадает изображение
        correct_product = None
        for product in products:
            if product.start_row <= image_row <= product.end_row:
                correct_product = product
                break
        
        if correct_product is None:
            print(f"⚠️  Изображение {image.local_path} (строка {image_row}) не попадает ни в один диапазон товаров")
            continue
        
        # Определяем, является ли изображение главным (из столбца A)
        # Предполагаем, что изображения из столбца A имеют определенные паттерны в названии
        is_main_image = False
        
        # Проверяем различные паттерны для изображений из столбца A
        main_patterns = [
            r'original_sheet_image\d+',  # original_sheet_image2.png
            r'sheet_\w+_public_image\d+',  # sheet_1SD3YfSQ_public_image13.png
            r'sheet_\w+_\d+_image\d+',  # sheet_1FIAT6ri_1758278199_image7.png
        ]
        
        for pattern in main_patterns:
            if re.search(pattern, image.local_path):
                is_main_image = True
                break
        
        # Если не нашли по паттернам, считаем главным если это первое изображение в диапазоне строк товара
        if not is_main_image:
            # Проверяем, есть ли уже главное изображение для этого товара
            existing_main = session.query(ProductImage).filter(
                ProductImage.product_id == correct_product.id,
                ProductImage.image_type == 'main'
            ).first()
            
            if not existing_main:
                is_main_image = True
        
        # Обновляем привязку к товару и тип изображения
        old_product_id = image.product_id
        old_image_type = image.image_type
        
        image.product_id = correct_product.id
        image.image_type = 'main' if is_main_image else 'additional'
        
        if old_product_id != correct_product.id or old_image_type != image.image_type:
            print(f"Исправлено: {image.local_path} (строка {image_row})")
            print(f"  - Товар: {old_product_id} → {correct_product.id} '{correct_product.name}'")
            print(f"  - Тип: {old_image_type} → {image.image_type}")
            fixed_count += 1
        
        if image.image_type == 'main':
            main_images_count += 1
        else:
            additional_images_count += 1
    
    session.commit()
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Исправлено изображений: {fixed_count}")
    print(f"Главных изображений: {main_images_count}")
    print(f"Дополнительных изображений: {additional_images_count}")
    
    return fixed_count

if __name__ == "__main__":
    try:
        fixed = fix_image_classification()
        print(f"\n✅ Исправлено {fixed} изображений!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'session' in locals():
            session.close()

