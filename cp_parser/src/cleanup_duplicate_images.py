#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов изображений.
Находит изображения с одинаковым содержимым и удаляет дубли.
"""

import os
import hashlib
from pathlib import Path
from collections import defaultdict
import sys

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from database import db_manager, image_service
from loguru import logger

class ImageDuplicateRemover:
    """Класс для удаления дубликатов изображений"""
    
    def __init__(self):
        self.images_dir = Path(__file__).parent.parent / "storage" / "images"
        self.logger = logger
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """Вычисляет MD5 хеш файла"""
        if not file_path.exists():
            return ""
            
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return ""
    
    def find_duplicate_images(self):
        """Находит дубликаты изображений по содержимому"""
        self.logger.info("🔍 Поиск дубликатов изображений...")
        
        # Получаем все изображения из БД
        all_images = image_service.get_all_images()
        self.logger.info(f"Найдено {len(all_images)} изображений в БД")
        
        # Группируем по хешу содержимого
        hash_groups = defaultdict(list)
        missing_files = []
        
        for image in all_images:
            file_path = Path(image.local_path)
            
            if not file_path.exists():
                missing_files.append(image)
                continue
                
            file_hash = self.calculate_file_hash(file_path)
            if file_hash:
                hash_groups[file_hash].append(image)
        
        # Находим группы с дубликатами
        duplicates = {hash_val: images for hash_val, images in hash_groups.items() if len(images) > 1}
        
        self.logger.info(f"📊 Статистика:")
        self.logger.info(f"  • Уникальных изображений: {len(hash_groups)}")
        self.logger.info(f"  • Групп с дубликатами: {len(duplicates)}")
        self.logger.info(f"  • Отсутствующих файлов: {len(missing_files)}")
        
        total_duplicates = sum(len(images) - 1 for images in duplicates.values())
        self.logger.info(f"  • Всего дубликатов к удалению: {total_duplicates}")
        
        return duplicates, missing_files
    
    def remove_duplicates(self, duplicates: dict, dry_run: bool = True):
        """Удаляет дубликаты, оставляя самое раннее изображение"""
        removed_count = 0
        freed_space = 0
        
        for file_hash, images in duplicates.items():
            # Сортируем по ID (самое раннее - с меньшим ID)
            images.sort(key=lambda x: x.id)
            keep_image = images[0]  # Оставляем первое (самое раннее)
            remove_images = images[1:]  # Удаляем остальные
            
            self.logger.info(f"\n📁 Группа дубликатов (hash: {file_hash[:8]}...):")
            self.logger.info(f"  ✅ Оставляем: {keep_image.image_filename} (ID: {keep_image.id})")
            
            for image in remove_images:
                file_path = Path(image.local_path)
                file_size = file_path.stat().st_size if file_path.exists() else 0
                
                self.logger.info(f"  🗑️  Удаляем: {image.image_filename} (ID: {image.id}) - {file_size} байт")
                
                if not dry_run:
                    # Удаляем файл
                    if file_path.exists():
                        file_path.unlink()
                        freed_space += file_size
                    
                    # Удаляем запись из БД
                    with db_manager.get_session() as session:
                        session.delete(session.merge(image))
                        session.commit()
                
                removed_count += 1
        
        if dry_run:
            self.logger.info(f"\n🔍 РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА")
            self.logger.info(f"📊 Будет удалено: {removed_count} дубликатов")
            self.logger.info(f"💾 Будет освобождено: {freed_space / 1024:.1f} KB")
            self.logger.info(f"▶️  Для реального удаления запустите с параметром --execute")
        else:
            self.logger.info(f"\n✅ УДАЛЕНИЕ ЗАВЕРШЕНО")
            self.logger.info(f"🗑️  Удалено дубликатов: {removed_count}")
            self.logger.info(f"💾 Освобождено места: {freed_space / 1024:.1f} KB")
    
    def remove_missing_files(self, missing_files: list, dry_run: bool = True):
        """Удаляет записи о несуществующих файлах"""
        if not missing_files:
            return
            
        self.logger.info(f"\n🔍 Найдено {len(missing_files)} записей с отсутствующими файлами:")
        
        for image in missing_files:
            self.logger.info(f"  🗑️  {image.image_filename} (ID: {image.id}) - файл не найден")
            
            if not dry_run:
                with db_manager.get_session() as session:
                    session.delete(session.merge(image))
                    session.commit()
        
        if not dry_run:
            self.logger.info(f"✅ Удалено {len(missing_files)} записей с отсутствующими файлами")


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Удаление дубликатов изображений")
    parser.add_argument("--execute", action="store_true", 
                       help="Выполнить реальное удаление (по умолчанию только предварительный просмотр)")
    parser.add_argument("--remove-missing", action="store_true",
                       help="Также удалить записи с отсутствующими файлами")
    
    args = parser.parse_args()
    
    remover = ImageDuplicateRemover()
    
    # Находим дубликаты
    duplicates, missing_files = remover.find_duplicate_images()
    
    if not duplicates and not missing_files:
        logger.info("✅ Дубликаты не найдены!")
        return
    
    # Удаляем дубликаты
    if duplicates:
        remover.remove_duplicates(duplicates, dry_run=not args.execute)
    
    # Удаляем записи с отсутствующими файлами
    if missing_files and args.remove_missing:
        remover.remove_missing_files(missing_files, dry_run=not args.execute)
    
    if not args.execute:
        logger.info(f"\n💡 Для выполнения реального удаления запустите:")
        logger.info(f"   python cleanup_duplicate_images.py --execute")
        if missing_files:
            logger.info(f"   python cleanup_duplicate_images.py --execute --remove-missing")


if __name__ == "__main__":
    main()


