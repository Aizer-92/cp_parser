#!/usr/bin/env python3
"""
Скрипт для полной очистки всех изображений из базы данных и файловой системы
"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from database.manager_v4 import DatabaseManager
from database.models_v4 import ProductImage

def clean_all_images():
    """Удаляет все изображения из базы данных и файловой системы"""
    session = DatabaseManager.get_session()
    
    print("=== ОЧИСТКА ВСЕХ ИЗОБРАЖЕНИЙ ===\n")
    
    # Получаем все изображения
    images = session.query(ProductImage).all()
    print(f"Найдено изображений в базе данных: {len(images)}")
    
    # Удаляем файлы изображений
    deleted_files = 0
    for image in images:
        if image.local_path and os.path.exists(image.local_path):
            try:
                os.remove(image.local_path)
                deleted_files += 1
                print(f"Удален файл: {image.local_path}")
            except Exception as e:
                print(f"Ошибка при удалении файла {image.local_path}: {e}")
    
    # Удаляем все записи изображений из базы данных
    session.query(ProductImage).delete()
    session.commit()
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Удалено файлов: {deleted_files}")
    print(f"Удалено записей из БД: {len(images)}")
    
    return deleted_files, len(images)

if __name__ == "__main__":
    try:
        deleted_files, deleted_records = clean_all_images()
        print(f"\n✅ Очистка завершена!")
        print(f"   - Удалено файлов: {deleted_files}")
        print(f"   - Удалено записей из БД: {deleted_records}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'session' in locals():
            session.close()

