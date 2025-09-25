#!/usr/bin/env python3
"""
Полная очистка всех изображений и записей в БД
"""

import os
import sys
import shutil

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def clear_all_images():
    """Полностью очищает все изображения"""
    print("🧹 Полная очистка всех изображений...")
    
    # Очищаем БД
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import ProductImage
        
        # Удаляем все записи об изображениях
        deleted_count = session.query(ProductImage).count()
        session.query(ProductImage).delete()
        session.commit()
        print(f"✅ Удалено записей об изображениях из БД: {deleted_count}")
    
    # Очищаем все папки с изображениями
    image_dirs = [
        "storage/images/products",
        "storage/images/products_fixed", 
        "storage/images/products_correct",
        "storage/images/products_original_sheet",
        "storage/images/products_Мерч для Sense_1757934153",
        "storage/images/products_Вторая таблица_1757933430",
        "storage/images/products_Вторая таблица_1757933504",
        "storage/images/products_test_sheet_2_1757932871",
        "storage/images/products_daily",
        "storage/images/products_new",
        "storage/images/thumbnails"
    ]
    
    for image_dir in image_dirs:
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir)
            print(f"✅ Удалена папка: {image_dir}")
    
    # Создаем чистую папку для новых изображений
    os.makedirs("storage/images/products_parsed", exist_ok=True)
    print("✅ Создана чистая папка: storage/images/products_parsed")
    
    print("\n✅ Полная очистка завершена!")

if __name__ == "__main__":
    clear_all_images()
