#!/usr/bin/env python3
"""
Скрипт для правильного извлечения изображений из Excel файлов
"""

import os
import sys
import zipfile
import shutil
from PIL import Image
import io
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

def extract_images_from_excel(excel_file, output_dir):
    """Извлечение изображений из Excel файла"""
    print(f"📁 Извлекаем изображения из {excel_file}...")
    
    if not os.path.exists(excel_file):
        print(f"❌ Файл не найден: {excel_file}")
        return []
    
    extracted_images = []
    
    try:
        with zipfile.ZipFile(excel_file, 'r') as z:
            # Ищем файлы рисунков
            for name in z.namelist():
                if name.startswith('xl/media/image'):
                    print(f"  📷 Найдено изображение: {name}")
                    
                    # Читаем данные изображения
                    image_data = z.read(name)
                    
                    # Определяем расширение файла
                    if name.lower().endswith('.png'):
                        ext = '.png'
                    elif name.lower().endswith('.gif'):
                        ext = '.gif'
                    else:
                        ext = '.jpg'
                    
                    # Создаем имя файла
                    filename = os.path.basename(name)
                    if not filename.lower().endswith(ext):
                        filename = filename + ext
                    
                    output_path = os.path.join(output_dir, filename)
                    
                    # Сохраняем изображение
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    # Проверяем, что изображение корректное
                    try:
                        with Image.open(output_path) as img:
                            img.verify()
                        print(f"    ✅ {filename} - корректное изображение")
                        extracted_images.append(output_path)
                    except Exception as e:
                        print(f"    ❌ {filename} - поврежденное изображение: {e}")
                        os.remove(output_path)
    
    except zipfile.BadZipFile:
        print(f"❌ Файл {excel_file} не является корректным ZIP-архивом")
        return []
    
    print(f"✅ Извлечено {len(extracted_images)} изображений")
    return extracted_images

def main():
    print("🔄 Исправление изображений...")
    
    # Очищаем папку для изображений
    images_dir = "storage/images/products_parsed"
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)
    os.makedirs(images_dir, exist_ok=True)
    print(f"✅ Очищена папка: {images_dir}")
    
    # Извлекаем изображения из всех Excel файлов
    excel_files = [
        "storage/excel_files/original_sheet.xlsx",
        "storage/excel_files/Вторая таблица_1757933430.xlsx",
        "storage/excel_files/Вторая таблица_1757933504.xlsx",
        "storage/excel_files/Мерч для Sense_1757934153.xlsx"
    ]
    
    all_images = []
    for excel_file in excel_files:
        if os.path.exists(excel_file):
            images = extract_images_from_excel(excel_file, images_dir)
            all_images.extend(images)
    
    print(f"\n📊 Итого извлечено {len(all_images)} изображений")
    
    # Теперь нужно привязать изображения к товарам
    # Это упрощенная версия - просто привязываем по порядку
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # Получаем все товары
    products = db.get_all_products_with_details()
    
    print(f"\n🔗 Привязываем изображения к товарам...")
    
    image_index = 0
    for product, price_offers, existing_images in products:
        if image_index < len(all_images):
            # Основное изображение
            main_image_path = all_images[image_index]
            new_main_name = f"product_{product.id}_main.jpg"
            new_main_path = os.path.join(images_dir, new_main_name)
            
            try:
                shutil.copy2(main_image_path, new_main_path)
                db.create_product_image(
                    product_id=product.id,
                    image_path=f"storage/images/products_parsed/{new_main_name}",
                    image_type='main'
                )
                print(f"  ✅ {product.name} -> {new_main_name}")
                image_index += 1
            except Exception as e:
                print(f"  ❌ Ошибка при копировании изображения для {product.name}: {e}")
    
    print(f"\n✅ Изображения исправлены!")

if __name__ == "__main__":
    main()
