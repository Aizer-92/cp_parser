#!/usr/bin/env python3
"""
Скрипт для проверки соответствия изображений товарам по диапазонам строк.
Изображение из ячейки A4 должно быть привязано к товару, у которого start_row <= 4 <= end_row.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata
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

def check_image_product_mapping():
    """Проверяет соответствие изображений товарам по диапазонам строк"""
    session = DatabaseManager.get_session()
    
    print("=== ПРОВЕРКА СООТВЕТСТВИЯ ИЗОБРАЖЕНИЙ ТОВАРАМ ===\n")
    
    # Получаем все товары с их диапазонами строк
    products = session.query(Product).filter(
        Product.start_row.isnot(None),
        Product.end_row.isnot(None)
    ).all()
    
    print(f"Найдено товаров с диапазонами строк: {len(products)}")
    
    # Получаем все изображения
    images = session.query(ProductImage).all()
    print(f"Найдено изображений: {len(images)}\n")
    
    mismatched_images = []
    correct_mappings = []
    
    for image in images:
        # Извлекаем номер строки из пути к изображению
        image_row = extract_row_from_image_path(image.local_path)
        
        if image_row is None:
            print(f"⚠️  Не удалось извлечь номер строки из: {image.local_path}")
            continue
        
        # Ищем товар, в диапазон строк которого попадает изображение
        correct_product = None
        for product in products:
            if product.start_row and product.end_row and product.start_row <= image_row <= product.end_row:
                correct_product = product
                break
        
        if correct_product is None:
            print(f"❌ Изображение {image.local_path} (строка {image_row}) не попадает ни в один диапазон товаров")
            mismatched_images.append(image)
        elif image.product_id != correct_product.id:
            # Получаем текущий товар изображения
            current_product = session.query(Product).filter(Product.id == image.product_id).first()
            current_name = current_product.name if current_product else "Неизвестный товар"
            
            print(f"❌ НЕПРАВИЛЬНО: {image.local_path} (строка {image_row}) привязано к товару ID {image.product_id} '{current_name}', но должно быть к ID {correct_product.id} '{correct_product.name}' (диапазон {correct_product.start_row}-{correct_product.end_row})")
            mismatched_images.append((image, correct_product))
        else:
            print(f"✅ ПРАВИЛЬНО: {image.local_path} (строка {image_row}) привязано к товару '{correct_product.name}' (диапазон {correct_product.start_row}-{correct_product.end_row})")
            correct_mappings.append(image)
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Правильных привязок: {len(correct_mappings)}")
    print(f"Неправильных привязок: {len(mismatched_images)}")
    
    return mismatched_images, correct_mappings

def fix_image_assignments(mismatched_images):
    """Исправляет неправильные привязки изображений к товарам"""
    if not mismatched_images:
        print("Нет неправильных привязок для исправления")
        return
    
    session = DatabaseManager.get_session()
    
    print(f"\n=== ИСПРАВЛЕНИЕ {len(mismatched_images)} НЕПРАВИЛЬНЫХ ПРИВЯЗОК ===")
    
    for item in mismatched_images:
        if isinstance(item, tuple):
            image, correct_product = item
        else:
            # Для изображений без правильного товара - пропускаем
            print(f"⚠️  Пропускаем {item.local_path} - не найден подходящий товар")
            continue
        
        old_product_id = image.product_id
        image.product_id = correct_product.id
        
        print(f"Исправлено: {image.local_path} перенесено с товара ID {old_product_id} на товар ID {correct_product.id} '{correct_product.name}'")
    
    session.commit()
    print(f"\n✅ Исправлено {len([item for item in mismatched_images if isinstance(item, tuple)])} привязок")

if __name__ == "__main__":
    try:
        mismatched, correct = check_image_product_mapping()
        
        if mismatched:
            print(f"\nНайдено {len(mismatched)} неправильных привязок.")
            response = input("Исправить их? (y/n): ").lower().strip()
            if response == 'y':
                fix_image_assignments(mismatched)
            else:
                print("Исправление отменено")
        else:
            print("\n✅ Все изображения правильно привязаны к товарам!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'session' in locals():
            session.close()
