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

def extract_sheet_and_position_from_filename(filename):
    """Извлекает название таблицы и позицию (row, column) из имени файла изображения"""
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
    ]
    
    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            groups = match.groups()
            if len(groups) >= 3:
                # Определяем, где находятся column и row
                if groups[0] == 'original_sheet':
                    # Для original_sheet формат: original_sheet_{col}{row}_{type}.png
                    sheet_title = 'original_sheet'
                    col_letter = groups[1]
                    row_idx = int(groups[2])
                    image_type = groups[3]
                elif len(groups) == 4:
                    # Обычный формат: {sheet}_{col}{row}_{type}.png
                    sheet_title = groups[0]
                    col_letter = groups[1]
                    row_idx = int(groups[2])
                    image_type = groups[3]
                else:
                    # Формат с timestamp: {sheet}_{timestamp}_{col}{row}_{type}.png
                    sheet_title = groups[0]
                    col_letter = groups[1]
                    row_idx = int(groups[2])
                    image_type = groups[3]
                
                # Проверяем, что col_letter содержит только буквы A-Z
                if col_letter and col_letter.isalpha() and col_letter.isupper():
                    return sheet_title, col_letter, row_idx, image_type
    
    return None, None, None, None

def assign_images_by_sheet_and_row():
    """Привязывает изображения к товарам по ID таблицы и строке"""
    db_manager = DatabaseManager
    session = db_manager.get_session()

    print("\n=== ПРИВЯЗКА ИЗОБРАЖЕНИЙ ПО ТАБЛИЦЕ И СТРОКЕ ===")

    # Получаем все изображения
    images = session.query(ProductImage).all()
    
    assigned_count = 0
    error_count = 0
    skipped_logos = 0

    for image in images:
        filename = Path(image.local_path).name
        
        # Извлекаем информацию из имени файла
        sheet_title, col_letter, row_idx, image_type = extract_sheet_and_position_from_filename(filename)
        
        if not all([sheet_title, col_letter, row_idx, image_type]):
            error_count += 1
            if error_count <= 10:  # Показываем первые 10 ошибок
                print(f"   ❌ Не удалось извлечь данные из: {filename}")
            continue

        # Пропускаем логотип (A1)
        if row_idx == 1 and col_letter == 'A':
            skipped_logos += 1
            continue

        # Находим таблицу по названию
        sheet_metadata = session.query(SheetMetadata).filter_by(sheet_title=sheet_title).first()
        if not sheet_metadata:
            error_count += 1
            if error_count <= 10:
                print(f"   ❌ Таблица '{sheet_title}' не найдена для: {filename}")
            continue

        # Ищем товар в этой таблице по строке
        target_product = session.query(Product).filter(
            Product.sheet_id == sheet_metadata.id,
            Product.start_row <= row_idx,
            Product.end_row >= row_idx
        ).first()

        if not target_product:
            error_count += 1
            if error_count <= 10:
                print(f"   ❌ Товар не найден для позиции {col_letter}{row_idx} в таблице '{sheet_title}': {filename}")
            continue

        # Обновляем привязку изображения
        image.product_id = target_product.id
        image.sheet_id = sheet_metadata.id
        image.row = row_idx
        image.column = col_letter
        image.image_type = image_type
        session.add(image)
        
        assigned_count += 1
        
        if assigned_count % 50 == 0:
            print(f"   Обработано: {assigned_count} изображений")

    session.commit()
    session.close()

    print(f"\n=== СТАТИСТИКА ===")
    print(f"Привязано изображений: {assigned_count}")
    print(f"Пропущено логотипов: {skipped_logos}")
    print(f"Ошибок: {error_count}")
    print(f"✅ Привязка завершена!")

if __name__ == "__main__":
    assign_images_by_sheet_and_row()

