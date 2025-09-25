#!/usr/bin/env python3
"""
Восстановление изображений из папки storage/images/products
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL
from pathlib import Path
import re

def restore_images():
    """Восстанавливает изображения из папки storage/images/products"""
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    # Получаем все товары
    with db.get_session() as session:
        from database.models_v4 import Product
        
        products = session.query(Product).all()
        print(f"📦 Найдено товаров: {len(products)}")
        
        # Папка с изображениями
        images_dir = Path("storage/images/products")
        
        if not images_dir.exists():
            print("❌ Папка с изображениями не найдена")
            return
        
        # Получаем список всех изображений
        image_files = list(images_dir.glob("*.jpg"))
        print(f"📸 Найдено изображений: {len(image_files)}")
        
        # Сопоставляем изображения с товарами
        for product in products:
            print(f"\n🔍 Обрабатываем товар: {product.name}")
            
            # Ищем изображения для этого товара
            product_images = []
            
            for image_file in image_files:
                filename = image_file.name
                
                # Пытаемся извлечь номер строки и колонки из имени файла
                # Формат: product_row_X_col_Y_Z.jpg
                match = re.search(r'product_row_(\d+)_col_(\d+)_', filename)
                if match:
                    row_num = int(match.group(1))
                    col_num = int(match.group(2))
                    
                    # Основные изображения находятся в столбце 0 (A)
                    # Сопоставляем номер строки с товаром
                    if product.name == "Кардхолдер" and row_num == 3 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    elif product.name == "Обложка для паспорта" and row_num == 4 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    elif product.name == "Футляр для очков" and row_num == 5 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    elif product.name == "Ручка" and row_num == 6 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    elif product.name == "Таблетница" and row_num == 8 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    elif product.name == "Набор карандашей 6 цветов" and row_num == 10 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    elif product.name == "Кружка" and row_num == 12 and col_num == 0:
                        product_images.append((image_file, 'main'))
                    # Дополнительные изображения (столбец 17)
                    elif product.name == "Обложка для паспорта" and row_num == 4 and col_num == 17:
                        product_images.append((image_file, 'additional'))
                    elif product.name == "Футляр для очков" and row_num == 5 and col_num == 17:
                        product_images.append((image_file, 'additional'))
                    elif product.name == "Ручка" and row_num == 6 and col_num == 17:
                        product_images.append((image_file, 'additional'))
                    elif product.name == "Таблетница" and row_num == 8 and col_num == 17:
                        product_images.append((image_file, 'additional'))
                    elif product.name == "Набор карандашей 6 цветов" and row_num == 10 and col_num == 17:
                        product_images.append((image_file, 'additional'))
                    elif product.name == "Кружка" and row_num == 12 and col_num == 17:
                        product_images.append((image_file, 'additional'))
            
            print(f"  📸 Найдено изображений: {len(product_images)}")
            
            # Сохраняем изображения в базу данных
            for image_file, image_type in product_images:
                # Создаем запись об изображении
                db.create_product_image(
                    product_id=product.id,
                    image_path=str(image_file),
                    image_type=image_type
                )
                
                print(f"    ✅ Сохранено: {image_file.name} ({image_type})")

if __name__ == "__main__":
    restore_images()
