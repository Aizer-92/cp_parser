#!/usr/bin/env python3
"""
Скрипт для переименования изображений с добавлением номера строки ячейки.
Это поможет проверить правильность привязки изображений к товарам.
"""

import sys
import os
import shutil
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

def rename_images_with_cell_position():
    """Переименовывает изображения, добавляя номер строки ячейки"""
    session = DatabaseManager.get_session()
    
    print("=== ПЕРЕИМЕНОВАНИЕ ИЗОБРАЖЕНИЙ С ПОЗИЦИЕЙ ЯЧЕЙКИ ===\n")
    
    # Получаем все изображения
    images = session.query(ProductImage).all()
    print(f"Найдено изображений: {len(images)}\n")
    
    renamed_count = 0
    errors = []
    
    for image in images:
        # Извлекаем номер строки из пути к изображению
        image_row = extract_row_from_image_path(image.local_path)
        
        if image_row is None:
            print(f"⚠️  Не удалось извлечь номер строки из: {image.local_path}")
            continue
        
        # Получаем информацию о товаре
        product = session.query(Product).filter(Product.id == image.product_id).first()
        product_name = product.name if product else "Неизвестный товар"
        product_range = f"{product.start_row}-{product.end_row}" if product and product.start_row and product.end_row else "Нет диапазона"
        
        # Создаем новое имя файла
        old_path = Path(image.local_path)
        old_name = old_path.stem  # имя без расширения
        extension = old_path.suffix  # расширение
        
        # Новое имя: старое_имя_A{номер_строки}_{тип}_{товар}_{диапазон}
        new_name = f"{old_name}_A{image_row}_{image.image_type}_{product_name.replace(' ', '_')}_{product_range}{extension}"
        
        # Создаем новый путь
        new_path = old_path.parent / new_name
        
        try:
            # Переименовываем файл
            if old_path.exists():
                shutil.move(str(old_path), str(new_path))
                
                # Обновляем путь в базе данных
                image.local_path = str(new_path)
                
                print(f"✅ Переименовано: {old_path.name}")
                print(f"   → {new_name}")
                print(f"   Товар: {product_name} (строки {product_range})")
                print(f"   Тип: {image.image_type}")
                print()
                
                renamed_count += 1
            else:
                errors.append(f"Файл не найден: {old_path}")
                print(f"❌ Файл не найден: {old_path}")
                
        except Exception as e:
            errors.append(f"Ошибка при переименовании {old_path}: {e}")
            print(f"❌ Ошибка при переименовании {old_path}: {e}")
    
    session.commit()
    
    print(f"=== СТАТИСТИКА ===")
    print(f"Переименовано изображений: {renamed_count}")
    print(f"Ошибок: {len(errors)}")
    
    if errors:
        print(f"\n=== ОШИБКИ ===")
        for error in errors:
            print(f"  - {error}")
    
    return renamed_count

if __name__ == "__main__":
    try:
        renamed = rename_images_with_cell_position()
        print(f"\n✅ Переименовано {renamed} изображений!")
        print("\nТеперь можно проверить в папке storage/images/ правильность привязки изображений к товарам.")
        print("Формат имени: старое_имя_A{номер_строки}_{тип}_{товар}_{диапазон}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'session' in locals():
            session.close()

