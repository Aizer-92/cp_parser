#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Массовая нормализация всех Excel таблиц с использованием AdvancedNormalizer
"""

import os
import sys
import logging
from pathlib import Path
import time

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_normalizer import AdvancedNormalizer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_all_excel_files():
    """Находит все Excel файлы в storage/excel_files"""
    
    excel_dir = Path("storage/excel_files")
    if not excel_dir.exists():
        logger.error("Папка storage/excel_files не найдена!")
        return []
    
    # Ищем все xlsx файлы (исключая уже нормализованные)
    excel_files = []
    for file_path in excel_dir.glob("*.xlsx"):
        if "_normalized" not in file_path.name:
            excel_files.append(file_path)
    
    logger.info(f"Найдено Excel файлов: {len(excel_files)}")
    return excel_files

def mass_normalize_all_tables():
    """Выполняет массовую нормализацию всех таблиц"""
    
    print("🔧 МАССОВАЯ НОРМАЛИЗАЦИЯ ВСЕХ ТАБЛИЦ")
    print("=" * 80)
    
    # Находим все Excel файлы
    excel_files = find_all_excel_files()
    
    if not excel_files:
        print("❌ Не найдено Excel файлов для нормализации")
        return
    
    print(f"📊 К обработке: {len(excel_files)} файлов")
    
    # Инициализируем нормализатор
    normalizer = AdvancedNormalizer()
    
    # Счетчики
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    # Обрабатываем каждый файл
    for i, file_path in enumerate(excel_files, 1):
        
        print(f"\n📋 [{i}/{len(excel_files)}] Обрабатываем: {file_path.name}")
        
        try:
            # Нормализуем таблицу
            normalized_path = normalizer.normalize_table(str(file_path))
            
            if normalized_path:
                success_count += 1
                print(f"✅ Успешно: {Path(normalized_path).name}")
            else:
                error_count += 1
                print(f"❌ Ошибка нормализации: {file_path.name}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Ошибка обработки {file_path.name}: {e}")
            print(f"❌ Исключение: {e}")
        
        # Прогресс
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(excel_files) - i) * avg_time
            print(f"⏱️ Прогресс: {i}/{len(excel_files)} | Осталось: ~{remaining/60:.1f} мин")
    
    # Итоговая статистика
    elapsed_total = time.time() - start_time
    
    print("\n🎯 ИТОГИ МАССОВОЙ НОРМАЛИЗАЦИИ:")
    print("=" * 80)
    print(f"✅ Успешно обработано: {success_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"⏱️ Общее время: {elapsed_total/60:.1f} мин")
    print(f"📊 Средняя скорость: {elapsed_total/len(excel_files):.1f} сек/файл")
    
    if success_count > 0:
        print(f"\n🗂️ Нормализованные файлы сохранены в storage/excel_files/")
        print(f"📋 Метаданные в формате *_metadata.json")
        print(f"🔄 Готово к перепарсингу в БД!")

def check_normalized_files():
    """Проверяет количество нормализованных файлов"""
    
    excel_dir = Path("storage/excel_files")
    
    # Оригинальные файлы
    original_files = list(excel_dir.glob("*.xlsx"))
    original_count = len([f for f in original_files if "_normalized" not in f.name])
    
    # Нормализованные файлы
    normalized_files = list(excel_dir.glob("*_normalized.xlsx"))
    normalized_count = len(normalized_files)
    
    # Файлы метаданных
    metadata_files = list(excel_dir.glob("*_metadata.json"))
    metadata_count = len(metadata_files)
    
    print(f"\n📊 СТАТИСТИКА ФАЙЛОВ:")
    print("-" * 40)
    print(f"📁 Оригинальных файлов: {original_count}")
    print(f"🔧 Нормализованных файлов: {normalized_count}")
    print(f"📋 Файлов метаданных: {metadata_count}")
    
    if normalized_count == original_count:
        print("✅ Все файлы успешно нормализованы!")
    else:
        print(f"⚠️ Не хватает {original_count - normalized_count} нормализованных файлов")
    
    if metadata_count == normalized_count:
        print("✅ Все метаданные созданы!")
    else:
        print(f"⚠️ Не хватает {normalized_count - metadata_count} файлов метаданных")

if __name__ == "__main__":
    
    # Сначала проверяем текущее состояние
    check_normalized_files()
    
    # Запрашиваем подтверждение
    print("\n" + "=" * 80)
    response = input("🚀 Начать массовую нормализацию? (y/N): ")
    
    if response.lower() in ['y', 'yes', 'да']:
        mass_normalize_all_tables()
        
        # Финальная проверка
        check_normalized_files()
    else:
        print("❌ Отменено пользователем")
