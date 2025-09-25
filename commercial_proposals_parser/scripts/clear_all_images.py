#!/usr/bin/env python3
"""
Очистка всех изображений и записей в БД
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def clear_all_images():
    """Очищает все изображения и записи в БД"""
    print("🗑️  Очистка всех изображений...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import ProductImage
        
        # Удаляем все записи об изображениях из БД
        session.query(ProductImage).delete()
        session.commit()
        print("✅ Удалены все записи об изображениях из БД")
    
    # Удаляем папку с изображениями
    import shutil
    image_dir = "storage/images/products_fixed"
    if os.path.exists(image_dir):
        shutil.rmtree(image_dir)
        print(f"✅ Удалена папка {image_dir}")
    
    # Создаем новую папку
    os.makedirs(image_dir, exist_ok=True)
    print(f"✅ Создана новая папка {image_dir}")

def main():
    """Основная функция"""
    print("🚀 Очистка всех изображений")
    print("=" * 50)
    
    clear_all_images()

if __name__ == "__main__":
    main()
