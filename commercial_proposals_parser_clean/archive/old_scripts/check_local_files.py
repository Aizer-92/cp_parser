#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки всех локальных Excel файлов и их полной обработки
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, ProductImage

def check_local_files():
    """Проверяет все локальные Excel файлы и их обработку"""
    print("📁 ПРОВЕРКА ЛОКАЛЬНЫХ EXCEL ФАЙЛОВ")
    print("=" * 50)
    
    # Получаем путь к папке с файлами
    base_dir = Path(__file__).parent.parent
    excel_dir = base_dir / "storage" / "excel_files"
    
    if not excel_dir.exists():
        print(f"❌ Папка {excel_dir} не найдена!")
        return
    
    # Получаем все Excel файлы
    excel_files = list(excel_dir.glob("*.xlsx"))
    print(f"📊 Найдено Excel файлов: {len(excel_files)}")
    
    session = DatabaseManager.get_session()
    
    try:
        processed_files = []
        unprocessed_files = []
        
        for excel_file in excel_files:
            print(f"\n🔍 Проверяем: {excel_file.name}")
            
            # Ищем соответствующую запись в SheetMetadata
            relative_path = str(excel_file.relative_to(base_dir))
            sheet = session.query(SheetMetadata).filter(
                SheetMetadata.local_file_path.like(f"%{excel_file.name}%")
            ).first()
            
            if sheet:
                # Проверяем наличие товаров и изображений
                products_count = session.query(Product).filter(Product.sheet_id == sheet.id).count()
                images_count = session.query(ProductImage).filter(ProductImage.sheet_id == sheet.id).count()
                
                if products_count > 0:
                    print(f"   ✅ Обработан: {products_count} товаров, {images_count} изображений")
                    processed_files.append({
                        'file': excel_file.name,
                        'sheet_id': sheet.id,
                        'products': products_count,
                        'images': images_count
                    })
                else:
                    print(f"   ⚠️ Записан в БД, но нет товаров")
                    unprocessed_files.append({
                        'file': excel_file.name,
                        'sheet_id': sheet.id,
                        'reason': 'Нет товаров'
                    })
            else:
                print(f"   ❌ Не найден в SheetMetadata")
                unprocessed_files.append({
                    'file': excel_file.name,
                    'sheet_id': None,
                    'reason': 'Не найден в БД'
                })
        
        print(f"\n📈 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   ✅ Обработано файлов: {len(processed_files)}")
        print(f"   ❌ Не обработано файлов: {len(unprocessed_files)}")
        
        if unprocessed_files:
            print(f"\n🔧 ФАЙЛЫ, ТРЕБУЮЩИЕ ОБРАБОТКИ:")
            for file_info in unprocessed_files:
                print(f"   📄 {file_info['file']} - {file_info['reason']}")
        
        # Подробная статистика по обработанным файлам
        if processed_files:
            print(f"\n📊 ДЕТАЛЬНАЯ СТАТИСТИКА ОБРАБОТАННЫХ ФАЙЛОВ:")
            total_products = sum(f['products'] for f in processed_files)
            total_images = sum(f['images'] for f in processed_files)
            print(f"   📦 Всего товаров: {total_products}")
            print(f"   🖼️ Всего изображений: {total_images}")
            
            # Топ-5 файлов по количеству товаров
            top_files = sorted(processed_files, key=lambda x: x['products'], reverse=True)[:5]
            print(f"\n🏆 ТОП-5 файлов по товарам:")
            for i, file_info in enumerate(top_files, 1):
                print(f"   {i}. {file_info['file']}: {file_info['products']} товаров, {file_info['images']} изображений")
        
        return unprocessed_files
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []
    finally:
        session.close()

def process_unprocessed_files(unprocessed_files):
    """Обрабатывает необработанные файлы"""
    if not unprocessed_files:
        print("✅ Все файлы уже обработаны!")
        return
    
    print(f"\n🔧 ОБРАБОТКА НЕОБРАБОТАННЫХ ФАЙЛОВ")
    print("=" * 40)
    
    from scripts.complete_parsing_pipeline import CompleteParsing
    
    base_dir = Path(__file__).parent.parent
    excel_dir = base_dir / "storage" / "excel_files"
    
    for file_info in unprocessed_files:
        if file_info['reason'] == 'Не найден в БД':
            print(f"\n📊 Обрабатываем файл: {file_info['file']}")
            
            excel_path = excel_dir / file_info['file']
            if excel_path.exists():
                try:
                    # Создаем парсер
                    parser = CompleteParsing()
                    
                    # Создаем запись в SheetMetadata
                    session = parser.session
                    from database.models_v4 import SheetMetadata
                    
                    sheet_metadata = SheetMetadata(
                        sheet_title=file_info['file'].replace('.xlsx', ''),
                        sheet_url='',  # Локальный файл
                        local_file_path=str(excel_path.relative_to(base_dir)),
                        total_products=0,
                        total_images=0
                    )
                    
                    session.add(sheet_metadata)
                    session.commit()
                    
                    sheet_id = sheet_metadata.id
                    print(f"   📋 Создана запись SheetMetadata с ID: {sheet_id}")
                    
                    # Запускаем обработку
                    images_count = parser.extract_images_from_excel(excel_path, sheet_id)
                    products_count = parser.parse_products_from_excel(excel_path, sheet_id)
                    assigned_count = parser.assign_images_to_products(sheet_id)
                    
                    # Обновляем статистику
                    sheet_metadata.total_images = images_count
                    sheet_metadata.total_products = products_count
                    session.commit()
                    
                    print(f"   ✅ Обработано: {products_count} товаров, {images_count} изображений, {assigned_count} привязано")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка обработки: {e}")
            else:
                print(f"   ❌ Файл не найден: {excel_path}")

if __name__ == "__main__":
    unprocessed = check_local_files()
    
    if unprocessed:
        response = input(f"\n❓ Обработать {len(unprocessed)} необработанных файлов? (y/n): ")
        if response.lower() in ['y', 'yes', 'да']:
            process_unprocessed_files(unprocessed)
