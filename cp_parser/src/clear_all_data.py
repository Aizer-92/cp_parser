#!/usr/bin/env python3
"""
Скрипт для полной очистки всех спарсенных данных.
Удаляет товары, ценовые предложения, изображения и файлы изображений.
Оставляет только проекты (метаданные файлов).
"""

import os
import shutil
from pathlib import Path
import sys

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from database import db_manager
from sqlalchemy import text
from loguru import logger

def clear_all_data():
    """Полная очистка всех спарсенных данных"""
    
    logger.info("🧹 Начинаю полную очистку данных...")
    
    # 1. Удаляем все данные из БД
    with db_manager.get_session() as session:
        # Удаляем изображения
        images_deleted = session.execute(text("DELETE FROM product_images")).rowcount
        session.commit()
        logger.info(f"🗑️  Удалено записей изображений: {images_deleted}")
        
        # Удаляем ценовые предложения
        offers_deleted = session.execute(text("DELETE FROM price_offers")).rowcount
        session.commit()
        logger.info(f"🗑️  Удалено ценовых предложений: {offers_deleted}")
        
        # Удаляем товары
        products_deleted = session.execute(text("DELETE FROM products")).rowcount
        session.commit()
        logger.info(f"🗑️  Удалено товаров: {products_deleted}")
        
        # Проверяем количество проектов (должны остаться)
        projects_count = session.execute(text("SELECT COUNT(*) FROM projects")).scalar()
        logger.info(f"📁 Проектов осталось: {projects_count}")
    
    # 2. Удаляем все файлы изображений
    images_dir = Path(__file__).parent.parent / "storage" / "images"
    if images_dir.exists():
        files_before = len(list(images_dir.glob("*.png")))
        
        # Удаляем все PNG файлы
        for image_file in images_dir.glob("*.png"):
            image_file.unlink()
        
        files_after = len(list(images_dir.glob("*.png")))
        logger.info(f"🗑️  Удалено файлов изображений: {files_before - files_after}")
    else:
        logger.warning("📁 Папка изображений не найдена")
    
    # 3. Сбрасываем счетчики автоинкремента (если таблица существует)
    with db_manager.get_session() as session:
        try:
            session.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name IN ('products', 'price_offers', 'product_images')"))
            session.commit()
            logger.info("🔄 Сброшены счетчики автоинкремента")
        except Exception as e:
            logger.info("🔄 Счетчики автоинкремента будут сброшены при создании новых записей")
    
    logger.info("✅ Полная очистка завершена! База готова к парсингу с нуля.")
    
    # 4. Показываем финальную статистику
    with db_manager.get_session() as session:
        stats = {
            'projects': session.execute(text("SELECT COUNT(*) FROM projects")).scalar(),
            'products': session.execute(text("SELECT COUNT(*) FROM products")).scalar(),
            'price_offers': session.execute(text("SELECT COUNT(*) FROM price_offers")).scalar(),
            'product_images': session.execute(text("SELECT COUNT(*) FROM product_images")).scalar()
        }
    
    logger.info("📊 Финальная статистика:")
    for table, count in stats.items():
        logger.info(f"  • {table}: {count}")

if __name__ == "__main__":
    clear_all_data()
