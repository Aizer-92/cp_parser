#!/usr/bin/env python3
"""
Скрипт для извлечения изображений из Excel файла и правильной привязки к товарам в базе v4
"""

import os
import sys
import openpyxl
from openpyxl.drawing.image import Image
from PIL import Image as PILImage
import io
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def extract_images_from_excel(excel_path, output_dir):
    """Извлекает изображения из Excel файла"""
    print(f"Извлекаем изображения из {excel_path}")
    
    # Создаем директорию для изображений
    os.makedirs(output_dir, exist_ok=True)
    
    # Открываем Excel файл
    workbook = openpyxl.load_workbook(excel_path)
    worksheet = workbook.active
    
    extracted_images = []
    
    # Проходим по всем изображениям в листе
    for image in worksheet._images:
        if hasattr(image, 'anchor') and hasattr(image, 'ref'):
            # Получаем ячейку, к которой привязано изображение
            cell_ref = image.anchor._from
            row = cell_ref.row
            col = cell_ref.col
            
            print(f"Найдено изображение в строке {row}, колонке {col}")
            
            # Сохраняем изображение
            image_filename = f"product_{row}_{col}.jpg"
            image_path = os.path.join(output_dir, image_filename)
            
            try:
                # Конвертируем в PIL Image для обработки
                pil_image = PILImage.open(io.BytesIO(image._data()))
                
                # Изменяем размер для оптимизации
                max_size = (800, 800)
                pil_image.thumbnail(max_size, PILImage.Resampling.LANCZOS)
                
                # Сохраняем как JPEG
                pil_image.save(image_path, 'JPEG', quality=85, optimize=True)
                
                extracted_images.append({
                    'filename': image_filename,
                    'path': image_path,
                    'row': row,
                    'col': col
                })
                
                print(f"Сохранено: {image_filename}")
                
            except Exception as e:
                print(f"Ошибка при сохранении изображения: {e}")
                continue
    
    workbook.close()
    return extracted_images

def link_images_to_products(extracted_images, db):
    """Привязывает изображения к товарам в базе данных"""
    print("Привязываем изображения к товарам...")
    
    # Получаем все товары из базы
    products = db.get_all_products_with_details()
    print(f"Найдено товаров в базе: {len(products)}")
    
    # Создаем словарь для сопоставления строк Excel с товарами
    # Предполагаем, что товары идут по порядку, начиная со строки 2 (заголовок в строке 1)
    product_image_map = {}
    
    for i, (product, price_offers, images) in enumerate(products):
        product_name = product.name.strip()
        print(f"Товар {i+1}: {product_name}")
        
        # Ищем изображения для этого товара
        # Предполагаем, что товар в строке i+2 (заголовок в строке 1)
        excel_row = i + 2
        
        matching_images = [img for img in extracted_images if img['row'] == excel_row]
        
        if matching_images:
            print(f"  Найдено {len(matching_images)} изображений для строки {excel_row}")
            
            for j, img_info in enumerate(matching_images):
                # Создаем запись в базе данных
                image_type = 'main' if j == 0 else 'additional'
                
                db.create_image(
                    product_id=product.id,
                    local_path=img_info['path'],
                    image_type=image_type,
                    format='jpg'
                )
                
                print(f"    Добавлено изображение: {img_info['filename']} ({image_type})")
        else:
            print(f"  Изображения не найдены для строки {excel_row}")

def main():
    """Основная функция"""
    print("=== Извлечение изображений из Excel и привязка к товарам v4 ===")
    
    # Пути
    excel_path = "storage/excel_files/original_sheet.xlsx"
    output_dir = "storage/images/products"
    
    # Проверяем существование Excel файла
    if not os.path.exists(excel_path):
        print(f"Ошибка: Excel файл не найден: {excel_path}")
        return
    
    # Подключаемся к базе данных
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    try:
        # Извлекаем изображения из Excel
        extracted_images = extract_images_from_excel(excel_path, output_dir)
        print(f"Извлечено изображений: {len(extracted_images)}")
        
        if extracted_images:
            # Привязываем изображения к товарам
            link_images_to_products(extracted_images, db)
            print("Привязка изображений завершена!")
        else:
            print("Изображения не найдены в Excel файле")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        pass  # db.close() не нужен для SQLAlchemy

if __name__ == "__main__":
    main()
