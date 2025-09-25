import os
import re
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata

def extract_position_from_filename(filename):
    """Извлекает позицию (row, column) из имени файла изображения"""
    # Паттерны для разных форматов имен файлов
    patterns = [
        # Формат: {sheet_title}_{col_letter}{row_idx}_{image_type}.png
        r'(.+)_([A-Z]+)(\d+)_(main|additional)\.png',
        # Формат: {sheet_title}_{col_letter}{row_idx}_{image_type}.png (с timestamp)
        r'(.+)_\d+_([A-Z]+)(\d+)_(main|additional)\.png',
        # Формат: original_sheet_{col_letter}{row_idx}_{image_type}.png
        r'original_sheet_([A-Z]+)(\d+)_(main|additional)\.png',
        # Формат: {sheet_title}_{col_letter}{row_idx}_{image_type}.png (с timestamp в конце)
        r'(.+)_([A-Z]+)(\d+)_(main|additional)_\d+\.png',
        # Формат: {sheet_title}_{timestamp}_{col_letter}{row_idx}_{image_type}.png
        r'(.+)_\d+_([A-Z]+)(\d+)_(main|additional)\.png',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups) >= 3:
                # Определяем, где находятся column и row
                if groups[0] == 'original_sheet':
                    # Для original_sheet формат: original_sheet_{col}{row}_{type}.png
                    col_letter = groups[1]
                    row_idx = int(groups[2])
                    image_type = groups[3]
                elif len(groups) == 4:
                    # Обычный формат: {sheet}_{col}{row}_{type}.png
                    col_letter = groups[1]
                    row_idx = int(groups[2])
                    image_type = groups[3]
                else:
                    # Формат с timestamp: {sheet}_{timestamp}_{col}{row}_{type}.png
                    col_letter = groups[1]
                    row_idx = int(groups[2])
                    image_type = groups[3]
                
                # Проверяем, что col_letter содержит только буквы A-Z
                if col_letter and col_letter.isalpha() and col_letter.isupper():
                    return col_letter, row_idx, image_type
    
    return None, None, None

def fix_image_positions():
    """Исправляет позиции изображений, извлекая их из имен файлов"""
    db_manager = DatabaseManager
    session = db_manager.get_session()

    print("\n=== ИСПРАВЛЕНИЕ ПОЗИЦИЙ ИЗОБРАЖЕНИЙ ===")

    # Получаем все изображения
    images = session.query(ProductImage).all()
    
    fixed_count = 0
    error_count = 0

    for image in images:
        filename = Path(image.local_path).name
        
        # Извлекаем позицию из имени файла
        col_letter, row_idx, image_type = extract_position_from_filename(filename)
        
        if col_letter and row_idx and image_type:
            # Обновляем позицию в БД
            image.row = row_idx
            image.column = col_letter
            image.image_type = image_type
            session.add(image)
            fixed_count += 1
            
            if fixed_count % 50 == 0:
                print(f"   Обработано: {fixed_count} изображений")
        else:
            error_count += 1
            if error_count <= 10:  # Показываем первые 10 ошибок
                print(f"   ❌ Не удалось извлечь позицию из: {filename}")

    session.commit()
    session.close()

    print(f"\n=== СТАТИСТИКА ===")
    print(f"Исправлено позиций: {fixed_count}")
    print(f"Ошибок: {error_count}")
    print(f"✅ Исправление завершено!")

if __name__ == "__main__":
    fix_image_positions()
