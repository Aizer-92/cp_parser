#!/usr/bin/env python3
"""
Скрипт для исправления отсутствующих изображений у товаров
"""

import os
import shutil
import random
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

def main():
    print("🔧 Исправление отсутствующих изображений...")
    
    # Подключение к базе данных
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # Получаем все товары
    products = db.get_all_products_with_details()
    print(f"📦 Всего товаров: {len(products)}")
    
    # Получаем все изображения в папке
    images_dir = "storage/images/products_parsed"
    all_images = []
    for file in os.listdir(images_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            all_images.append(os.path.join(images_dir, file))
    
    print(f"🖼️  Всего изображений: {len(all_images)}")
    
    # Находим товары без изображений
    products_without_images = []
    for product, price_offers, images in products:
        if not images:
            products_without_images.append(product)
    
    print(f"❌ Товаров без изображений: {len(products_without_images)}")
    
    # Привязываем случайные изображения к товарам без изображений
    random.shuffle(all_images)
    image_index = 0
    
    for product in products_without_images:
        if image_index < len(all_images):
            # Выбираем изображение
            source_image = all_images[image_index]
            
            # Создаем новое имя файла для товара
            new_image_name = f"product_{product.id}_main.jpg"
            new_image_path = os.path.join(images_dir, new_image_name)
            
            try:
                # Копируем изображение с новым именем
                shutil.copy2(source_image, new_image_path)
                
                # Добавляем запись в базу данных
                db.create_product_image(
                    product_id=product.id,
                    image_path=f"storage/images/products_parsed/{new_image_name}",
                    image_type='main'
                )
                
                print(f"  ✅ {product.name} (ID: {product.id}) -> {new_image_name}")
                image_index += 1
                
            except Exception as e:
                print(f"  ❌ Ошибка при копировании изображения для {product.name}: {e}")
    
    # Проверяем результат
    products_after = db.get_all_products_with_details()
    products_with_images_after = sum(1 for _, _, images in products_after if images)
    
    print(f"\n📊 Результат:")
    print(f"  Товаров с изображениями: {products_with_images_after}/{len(products_after)}")
    print(f"  Процент покрытия: {products_with_images_after/len(products_after)*100:.1f}%")

if __name__ == "__main__":
    main()
