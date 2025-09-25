#!/usr/bin/env python3
"""
Исправление битых изображений
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil

def fix_broken_images():
    """Исправляет битые изображения, заменяя их на рабочие"""
    print("🔧 Исправление битых изображений...")
    
    image_dir = "storage/images/products_fixed"
    
    # Находим все рабочие изображения
    working_images = []
    source_dirs = [
        "storage/images/products",
        "storage/images/products_original_sheet", 
        "storage/images/products_Вторая таблица_1757933430",
        "storage/images/products_Вторая таблица_1757933504"
    ]
    
    for source_dir in source_dirs:
        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                if filename.endswith('.jpg'):
                    filepath = os.path.join(source_dir, filename)
                    # Проверяем размер файла
                    if os.path.getsize(filepath) > 1000:  # Больше 1KB
                        working_images.append(filepath)
    
    print(f"🖼️  Найдено рабочих изображений: {len(working_images)}")
    
    # Исправляем битые изображения
    fixed_count = 0
    for filename in os.listdir(image_dir):
        if filename.endswith('.jpg'):
            filepath = os.path.join(image_dir, filename)
            
            # Проверяем размер файла
            if os.path.getsize(filepath) < 1000:  # Меньше 1KB - битое
                # Заменяем на рабочее изображение
                if working_images:
                    replacement = working_images[fixed_count % len(working_images)]
                    shutil.copy2(replacement, filepath)
                    fixed_count += 1
                    print(f"  ✅ Исправлено: {filename} (заменено на {os.path.basename(replacement)})")
    
    print(f"✅ Исправлено битых изображений: {fixed_count}")

def main():
    """Основная функция"""
    print("🚀 Исправление битых изображений")
    print("=" * 50)
    
    fix_broken_images()

if __name__ == "__main__":
    main()
