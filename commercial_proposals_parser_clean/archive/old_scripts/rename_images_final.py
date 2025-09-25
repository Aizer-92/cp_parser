#!/usr/bin/env python3
"""
Финальный скрипт для переименования изображений с правильной позицией
"""

import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage

def rename_images_final():
    """Переименовывает изображения с правильной позицией"""
    session = DatabaseManager.get_session()
    
    print("=== ФИНАЛЬНОЕ ПЕРЕИМЕНОВАНИЕ ИЗОБРАЖЕНИЙ ===\n")
    
    # Получаем все изображения
    images = session.query(ProductImage).all()
    
    renamed_count = 0
    error_count = 0
    
    for image in images:
        try:
            old_path = image.local_path
            
            # Получаем информацию о товаре
            product = session.query(Product).filter(Product.id == image.product_id).first()
            if not product:
                print(f"⚠️  Товар не найден для изображения: {old_path}")
                error_count += 1
                continue
            
            # Извлекаем позицию из имени файла
            filename = os.path.basename(old_path)
            
            # Ищем паттерн A{number} или B{number} в имени файла
            match = re.search(r'([AB])(\d+)_(main|additional)', filename)
            if not match:
                print(f"⚠️  Не удалось извлечь позицию из: {filename}")
                error_count += 1
                continue
            
            column_letter = match.group(1)
            row_number = int(match.group(2))
            image_type = match.group(3)
            
            # Формируем новое имя файла с правильной позицией
            product_name = product.name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
            new_filename = f"{product_name}_{column_letter}{row_number}_{image_type}_{product.start_row}-{product.end_row}.png"
            
            # Создаем новый путь
            directory = os.path.dirname(old_path)
            new_path = os.path.join(directory, new_filename)
            
            # Переименовываем файл
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                image.local_path = new_path
                session.add(image)
                renamed_count += 1
                print(f"✅ {filename} → {new_filename}")
            else:
                print(f"⚠️  Файл не найден: {old_path}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Ошибка при переименовании {old_path}: {e}")
            error_count += 1
    
    session.commit()
    session.close()
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Переименовано изображений: {renamed_count}")
    print(f"Ошибок: {error_count}")
    print(f"\n✅ Переименование завершено!")

if __name__ == "__main__":
    try:
        rename_images_final()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

