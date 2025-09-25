#!/usr/bin/env python3
"""
Скрипт для парсинга изображений из таблицы "Мерч для Sense"
"""

import os
import sys
import zipfile
import shutil
from PIL import Image
sys.path.append('.')
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

def parse_merch_sense_images():
    """Парсинг изображений из таблицы "Мерч для Sense" """
    
    # Находим самый новый файл "Мерч для Sense"
    merch_files = []
    for file in os.listdir("storage/excel_files"):
        if file.startswith("Мерч для Sense"):
            merch_files.append(file)
    
    if not merch_files:
        print("❌ Не найдены файлы 'Мерч для Sense'")
        return
    
    # Берем самый новый файл
    latest_file = sorted(merch_files)[-1]
    excel_file = f"storage/excel_files/{latest_file}"
    
    print(f"📁 Парсинг изображений из {excel_file}...")
    
    if not os.path.exists(excel_file):
        print(f"❌ Файл не найден: {excel_file}")
        return
    
    # Извлекаем изображения
    extracted_images = []
    try:
        with zipfile.ZipFile(excel_file, 'r') as z:
            for name in z.namelist():
                if name.startswith('xl/media/image'):
                    print(f"  📷 Найдено изображение: {name}")
                    
                    image_data = z.read(name)
                    
                    # Определяем расширение файла
                    if name.lower().endswith('.png'):
                        ext = '.png'
                    elif name.lower().endswith('.gif'):
                        ext = '.gif'
                    else:
                        ext = '.jpg'
                    
                    filename = os.path.basename(name)
                    if not filename.lower().endswith(ext):
                        filename = filename + ext
                    
                    output_path = f"storage/images/products_parsed/{filename}"
                    
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
        return
    
    print(f"✅ Извлечено {len(extracted_images)} изображений")
    
    if not extracted_images:
        print("⚠️  Изображения не найдены в файле. Убедитесь, что изображения добавлены в Google Sheets")
        return
    
    # Привязываем изображения к товарам "Мерч для Sense" (ID 29-43)
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # Получаем товары "Мерч для Sense"
    products = db.get_all_products_with_details()
    merch_products = [(p, po, i) for p, po, i in products if p.id >= 29]
    
    print(f"\n🔗 Привязываем изображения к товарам 'Мерч для Sense'...")
    
    image_index = 0
    for product, price_offers, existing_images in merch_products:
        if image_index < len(extracted_images):
            # Основное изображение
            main_image_path = extracted_images[image_index]
            new_main_name = f"product_{product.id}_main.jpg"
            new_main_path = f"storage/images/products_parsed/{new_main_name}"
            
            try:
                shutil.copy2(main_image_path, new_main_path)
                db.create_product_image(
                    product_id=product.id,
                    image_path=new_main_path,
                    image_type='main'
                )
                print(f"  ✅ {product.name} -> {new_main_name}")
                image_index += 1
                
                # Дополнительные изображения (если есть)
                additional_count = 1
                while image_index < len(extracted_images) and additional_count <= 3:
                    add_image_path = extracted_images[image_index]
                    new_add_name = f"product_{product.id}_additional_{additional_count}.jpg"
                    new_add_path = f"storage/images/products_parsed/{new_add_name}"
                    
                    try:
                        shutil.copy2(add_image_path, new_add_path)
                        db.create_product_image(
                            product_id=product.id,
                            image_path=new_add_path,
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
    
    print(f"\n✅ Изображения 'Мерч для Sense' обработаны!")

def main():
    print("🔄 Парсинг изображений из таблицы 'Мерч для Sense'...")
    parse_merch_sense_images()
    
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