#!/usr/bin/env python3
"""
Правильная привязка изображений к товарам по таблицам
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL
import shutil

def fix_correct_image_mapping():
    """Исправляет привязку изображений, используя правильные таблицы"""
    print("🔧 Правильная привязка изображений...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, ProductImage, SheetMetadata
        
        # Получаем все товары с информацией о таблицах
        products = session.query(Product).all()
        print(f"📦 Найдено товаров: {len(products)}")
        
        # Удаляем все существующие изображения
        session.query(ProductImage).delete()
        session.commit()
        print("🗑️  Удалены все записи об изображениях из БД")
        
        # Удаляем папку с изображениями
        image_dir = "storage/images/products_fixed"
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir)
        os.makedirs(image_dir, exist_ok=True)
        print(f"✅ Создана новая папка {image_dir}")
        
        # Собираем изображения по таблицам
        table_images = {
            'original_sheet': [],
            'Вторая таблица_1757933430': [],
            'Вторая таблица_1757933504': [],
            'Мерч для Sense_1757934153': []
        }
        
        source_dirs = {
            'original_sheet': 'storage/images/products_original_sheet',
            'Вторая таблица_1757933430': 'storage/images/products_Вторая таблица_1757933430',
            'Вторая таблица_1757933504': 'storage/images/products_Вторая таблица_1757933504',
            'Мерч для Sense_1757934153': 'storage/images/products'
        }
        
        for table_name, source_dir in source_dirs.items():
            if os.path.exists(source_dir):
                for filename in os.listdir(source_dir):
                    if filename.endswith('.jpg'):
                        filepath = os.path.join(source_dir, filename)
                        if os.path.getsize(filepath) > 5000:  # Больше 5KB
                            table_images[table_name].append(filepath)
                print(f"  📊 {table_name}: {len(table_images[table_name])} изображений")
        
        # Привязываем изображения к товарам по таблицам
        for product in products:
            # Получаем информацию о таблице
            sheet_metadata = session.query(SheetMetadata).filter(SheetMetadata.id == product.sheet_id).first()
            if not sheet_metadata:
                print(f"  ❌ Нет информации о таблице для {product.name} #{product.id}")
                continue
            
            table_name = sheet_metadata.sheet_title
            if table_name not in table_images or not table_images[table_name]:
                print(f"  ❌ Нет изображений для таблицы {table_name} ({product.name} #{product.id})")
                continue
            
            # Выбираем 2 изображения из правильной таблицы
            main_image = table_images[table_name][0] if table_images[table_name] else None
            additional_image = table_images[table_name][1] if len(table_images[table_name]) > 1 else table_images[table_name][0] if table_images[table_name] else None
            
            if main_image and additional_image:
                # Создаем новые имена файлов
                main_filename = f"product_{product.id}_main.jpg"
                additional_filename = f"product_{product.id}_additional.jpg"
                
                main_new_path = os.path.join(image_dir, main_filename)
                additional_new_path = os.path.join(image_dir, additional_filename)
                
                try:
                    # Копируем изображения
                    shutil.copy2(main_image, main_new_path)
                    shutil.copy2(additional_image, additional_new_path)
                    
                    # Создаем записи в БД
                    main_img = ProductImage(
                        product_id=product.id,
                        local_path=main_new_path,
                        image_type='main'
                    )
                    session.add(main_img)
                    
                    additional_img = ProductImage(
                        product_id=product.id,
                        local_path=additional_new_path,
                        image_type='additional'
                    )
                    session.add(additional_img)
                    
                    print(f"  ✅ {product.name} #{product.id} (из {table_name}): {main_filename} + {additional_filename}")
                    
                except Exception as e:
                    print(f"  ❌ Ошибка для {product.name} #{product.id}: {e}")
            else:
                print(f"  ❌ Не найдены изображения для {product.name} #{product.id} из {table_name}")
        
        session.commit()
        print(f"✅ Привязка изображений исправлена для {len(products)} товаров")

def main():
    """Основная функция"""
    print("🚀 Правильная привязка изображений")
    print("=" * 50)
    
    fix_correct_image_mapping()

if __name__ == "__main__":
    main()
