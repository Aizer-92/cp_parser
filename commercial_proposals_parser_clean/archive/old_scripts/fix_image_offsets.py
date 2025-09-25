#!/usr/bin/env python3
"""
Скрипт для исправления привязки изображений с учетом сдвига
"""

import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, ProductImage

def fix_image_offsets():
    """Исправляет привязку изображений с учетом сдвига"""
    session = DatabaseManager.get_session()
    
    print("=== ИСПРАВЛЕНИЕ ПРИВЯЗКИ ИЗОБРАЖЕНИЙ С УЧЕТОМ СДВИГА ===\n")
    
    # Анализируем original_sheet
    original_sheet = session.query(SheetMetadata).filter(
        SheetMetadata.sheet_title == 'original_sheet'
    ).first()
    
    if not original_sheet:
        print("❌ Таблица 'original_sheet' не найдена")
        return
    
    print(f"📊 Обрабатываем таблицу: {original_sheet.sheet_title}")
    
    # Находим изображение A3 (должно быть привязано к Кардхолдеру)
    a3_image_path = "storage/images/original_sheet_A3_main.png"
    
    if os.path.exists(a3_image_path):
        # Находим товар Кардхолдер
        cardholder = session.query(Product).filter(
            Product.name == "Кардхолдер",
            Product.sheet_id == original_sheet.id
        ).first()
        
        if cardholder:
            # Проверяем, есть ли уже такое изображение в БД
            existing_image = session.query(ProductImage).filter(
                ProductImage.local_path == a3_image_path
            ).first()
            
            if not existing_image:
                # Создаем новую запись об изображении
                from PIL import Image as PILImage
                try:
                    with PILImage.open(a3_image_path) as img:
                        width, height = img.size
                except:
                    width, height = 0, 0
                
                new_image = ProductImage(
                    product_id=cardholder.id,
                    local_path=a3_image_path,
                    image_type='main',
                    file_size=os.path.getsize(a3_image_path),
                    width=width,
                    height=height,
                    format='png'
                )
                
                session.add(new_image)
                session.commit()
                
                print(f"   ✅ {a3_image_path} → Кардхолдер (строки {cardholder.start_row}-{cardholder.end_row})")
            else:
                print(f"   ℹ️  {a3_image_path} уже привязано к товару ID {existing_image.product_id}")
        else:
            print(f"   ❌ Товар 'Кардхолдер' не найден в базе данных")
    else:
        print(f"   ❌ Файл {a3_image_path} не найден")
    
    # Проверяем, есть ли изображение A4 (если есть, тоже привязываем к Кардхолдеру)
    a4_image_path = "storage/images/original_sheet_A4_main.png"
    
    if os.path.exists(a4_image_path):
        cardholder = session.query(Product).filter(
            Product.name == "Кардхолдер",
            Product.sheet_id == original_sheet.id
        ).first()
        
        if cardholder:
            existing_image = session.query(ProductImage).filter(
                ProductImage.local_path == a4_image_path
            ).first()
            
            if not existing_image:
                from PIL import Image as PILImage
                try:
                    with PILImage.open(a4_image_path) as img:
                        width, height = img.size
                except:
                    width, height = 0, 0
                
                new_image = ProductImage(
                    product_id=cardholder.id,
                    local_path=a4_image_path,
                    image_type='main',
                    file_size=os.path.getsize(a4_image_path),
                    width=width,
                    height=height,
                    format='png'
                )
                
                session.add(new_image)
                session.commit()
                
                print(f"   ✅ {a4_image_path} → Кардхолдер (строки {cardholder.start_row}-{cardholder.end_row})")
            else:
                print(f"   ℹ️  {a4_image_path} уже привязано к товару ID {existing_image.product_id}")
    
    session.close()
    print(f"\n✅ Исправление завершено!")

if __name__ == "__main__":
    try:
        fix_image_offsets()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()