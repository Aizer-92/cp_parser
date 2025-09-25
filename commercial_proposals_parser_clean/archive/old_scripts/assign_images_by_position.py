#!/usr/bin/env python3
"""
Скрипт для привязки изображений по позициям (строка и столбец)
"""

import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, ProductImage

def extract_position_from_filename(filename):
    """Извлекает позицию (строка, столбец) из имени файла"""
    # Примеры: original_sheet_A4_main.png, Мерч для Sense_1758096973_A13_main.png
    match = re.search(r'([A-Z]+)(\d+)', filename)
    if match:
        column = match.group(1)
        row = int(match.group(2))
        return row, column
    return None, None

def assign_images_by_position():
    """Привязывает изображения к товарам по позициям"""
    session = DatabaseManager.get_session()
    
    print("=== ПРИВЯЗКА ИЗОБРАЖЕНИЙ ПО ПОЗИЦИЯМ ===\n")
    
    # Получаем все изображения из файловой системы
    images_dir = Path("storage/images")
    all_images = list(images_dir.glob("*.png"))
    
    print(f"📥 Найдено изображений в файловой системе: {len(all_images)}")
    
    assigned_count = 0
    skipped_count = 0
    
    for image_path in all_images:
        filename = image_path.name
        
        # Пропускаем логотипы (A1)
        if 'A1' in filename:
            print(f"   ⏭️  Пропускаем логотип: {filename}")
            skipped_count += 1
            continue
        
        # Извлекаем позицию
        row, column = extract_position_from_filename(filename)
        
        if not row or not column:
            print(f"   ⚠️  Не удалось извлечь позицию из: {filename}")
            continue
        
        # Определяем тип изображения: main если из столбца A, additional иначе
        image_type = 'main' if column == 'A' else 'additional'
        
        # Находим товар, в диапазон строк которого попадает изображение
        products = session.query(Product).filter(
            Product.start_row.isnot(None),
            Product.end_row.isnot(None)
        ).all()
        
        correct_product = None
        for product in products:
            if product.start_row <= row <= product.end_row:
                correct_product = product
                break
        
        if not correct_product:
            print(f"   ⚠️  Не найден товар для позиции {column}{row}: {filename}")
            continue
        
        # Проверяем, есть ли уже такое изображение в БД
        existing_image = session.query(ProductImage).filter(
            ProductImage.local_path == str(image_path)
        ).first()
        
        if existing_image:
            # Обновляем существующее изображение
            existing_image.product_id = correct_product.id
            existing_image.image_type = image_type
            existing_image.row = row
            existing_image.column = column
            session.add(existing_image)
            print(f"   🔄 Обновлено: {filename} → {correct_product.name} ({column}{row}, {image_type})")
        else:
            # Создаем новую запись
            try:
                from PIL import Image as PILImage
                with PILImage.open(image_path) as img:
                    width, height = img.size
            except:
                width, height = 0, 0
            
            new_image = ProductImage(
                product_id=correct_product.id,
                local_path=str(image_path),
                image_type=image_type,
                file_size=image_path.stat().st_size,
                width=width,
                height=height,
                format='png',
                row=row,
                column=column
            )
            
            session.add(new_image)
            print(f"   ✅ Создано: {filename} → {correct_product.name} ({column}{row}, {image_type})")
        
        assigned_count += 1
    
    session.commit()
    session.close()
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Обработано изображений: {assigned_count}")
    print(f"Пропущено логотипов: {skipped_count}")
    print(f"✅ Привязка завершена!")

if __name__ == "__main__":
    try:
        assign_images_by_position()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

