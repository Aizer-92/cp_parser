#!/usr/bin/env python3
"""
Скрипт для правильной привязки изображений к товарам
"""

import os
import sys
import zipfile
import shutil
from PIL import Image
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

def extract_images_from_excel(excel_file, output_dir):
    """Извлечение изображений из Excel файла с правильной привязкой к товарам"""
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

def map_images_to_products_correctly():
    """Правильная привязка изображений к товарам"""
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # Очищаем папку для изображений
    images_dir = "storage/images/products_parsed"
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)
    os.makedirs(images_dir, exist_ok=True)
    print(f"✅ Очищена папка: {images_dir}")
    
    # Извлекаем изображения из Excel файлов
    excel_files = [
        "storage/excel_files/original_sheet.xlsx",
        "storage/excel_files/Вторая таблица_1757933430.xlsx",
        "storage/excel_files/Вторая таблица_1757933504.xlsx"
    ]
    
    all_images = []
    for excel_file in excel_files:
        if os.path.exists(excel_file):
            images = extract_images_from_excel(excel_file, images_dir)
            all_images.extend(images)
    
    print(f"\n📊 Итого извлечено {len(all_images)} изображений")
    
    # Получаем товары из основной таблицы (ID 1-28)
    products = db.get_all_products_with_details()
    main_products = [(p, po, i) for p, po, i in products if p.id <= 28]
    
    print(f"\n🔗 Привязываем изображения к товарам основной таблицы...")
    
    # Привязываем изображения к товарам по порядку
    image_index = 0
    for product, price_offers, existing_images in main_products:
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
                
                # Дополнительные изображения (если есть)
                additional_count = 1
                while image_index < len(all_images) and additional_count <= 5:
                    add_image_path = all_images[image_index]
                    new_add_name = f"product_{product.id}_additional_{additional_count}.jpg"
                    new_add_path = os.path.join(images_dir, new_add_name)
                    
                    try:
                        shutil.copy2(add_image_path, new_add_path)
                        db.create_product_image(
                            product_id=product.id,
                            image_path=f"storage/images/products_parsed/{new_add_name}",
                            image_type='additional'
                        )
                        print(f"    📷 Доп. изображение {additional_count}: {new_add_name}")
                        image_index += 1
                        additional_count += 1
                    except Exception as e:
                        print(f"    ❌ Ошибка при копировании доп. изображения: {e}")
                        break
                        
            except Exception as e:
                print(f"  ❌ Ошибка при копировании изображения для {product.name}: {e}")
    
    print(f"\n✅ Изображения правильно привязаны!")

def main():
    print("🔄 Исправление привязки изображений к товарам...")
    map_images_to_products_correctly()
    
    # Проверяем результат
    db = CommercialProposalsDB(DATABASE_URL_V4)
    products = db.get_all_products_with_details()
    
    print(f"\n📊 Проверяем результат:")
    for product, price_offers, images in products:
        if images:
            print(f"  {product.name} (ID: {product.id}) - {len(images)} изображений")
        else:
            print(f"  {product.name} (ID: {product.id}) - НЕТ изображений")

if __name__ == "__main__":
    main()
