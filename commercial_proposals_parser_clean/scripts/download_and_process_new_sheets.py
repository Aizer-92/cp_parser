#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания и обработки 10 новых таблиц из списка
"""

import os
import sys
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import ProjectMetadata, SheetMetadata
from scripts.complete_parsing_pipeline import CompleteParsing

def get_next_urls_to_process(limit=10):
    """Получает следующие URL для обработки"""
    session = DatabaseManager.get_session()
    
    try:
        # Получаем проекты, которые еще не обработаны
        unprocessed_projects = session.query(ProjectMetadata).filter(
            ProjectMetadata.processing_status == 'pending',
            ProjectMetadata.google_sheets_url.isnot(None)
        ).limit(limit).all()
        
        return unprocessed_projects
        
    finally:
        session.close()

def process_next_sheets(count=10):
    """Обрабатывает следующие таблицы из списка"""
    print(f"🚀 ОБРАБОТКА {count} НОВЫХ ТАБЛИЦ")
    print("=" * 50)
    
    # Получаем проекты для обработки
    projects_to_process = get_next_urls_to_process(count)
    
    if not projects_to_process:
        print("✅ Все проекты уже обработаны!")
        return
    
    print(f"📋 Найдено проектов для обработки: {len(projects_to_process)}")
    
    # Создаем парсер
    parser = CompleteParsing()
    
    success_count = 0
    error_count = 0
    
    for i, project in enumerate(projects_to_process, 1):
        print(f"\n📊 Проект {i}/{len(projects_to_process)}")
        print(f"   📄 {project.project_title[:60]}...")
        print(f"   👤 Контрагент: {project.counterparty or 'Не указан'}")
        print(f"   🌍 Регион: {project.region or 'Не указан'}")
        
        try:
            # Отмечаем как обрабатываемый
            project.processing_status = 'processing'
            parser.session.commit()
            
            # Обрабатываем таблицу
            success = parser.process_single_sheet(project.google_sheets_url)
            
            if success:
                # Отмечаем как завершенный
                project.processing_status = 'completed'
                project.parsed_at = datetime.utcnow()
                
                # Связываем с созданной SheetMetadata
                latest_sheet = parser.session.query(SheetMetadata).filter(
                    SheetMetadata.sheet_url == project.google_sheets_url
                ).first()
                
                if latest_sheet:
                    project.sheet_metadata_id = latest_sheet.id
                
                success_count += 1
                print(f"   ✅ Успешно обработан")
            else:
                # Отмечаем как ошибку
                project.processing_status = 'error'
                error_count += 1
                print(f"   ❌ Ошибка обработки")
            
            parser.session.commit()
            
        except Exception as e:
            print(f"   ❌ Критическая ошибка: {e}")
            project.processing_status = 'error'
            parser.session.rollback()
            parser.session.commit()
            error_count += 1
        
        # Пауза между обработкой
        if i < len(projects_to_process):
            print("   ⏳ Пауза 3 секунды...")
            import time
            time.sleep(3)
    
    print(f"\n🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
    print(f"   ✅ Успешно: {success_count}")
    print(f"   ❌ Ошибки: {error_count}")
    print(f"   📊 Всего: {len(projects_to_process)}")
    
    # Показываем общую статистику
    session = DatabaseManager.get_session()
    try:
        total_projects = session.query(ProjectMetadata).count()
        completed_projects = session.query(ProjectMetadata).filter(
            ProjectMetadata.processing_status == 'completed'
        ).count()
        pending_projects = session.query(ProjectMetadata).filter(
            ProjectMetadata.processing_status == 'pending'
        ).count()
        error_projects = session.query(ProjectMetadata).filter(
            ProjectMetadata.processing_status == 'error'
        ).count()
        
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА ПРОЕКТОВ:")
        print(f"   📊 Всего: {total_projects}")
        print(f"   ✅ Обработано: {completed_projects}")
        print(f"   ⏳ Ожидает: {pending_projects}")
        print(f"   ❌ Ошибки: {error_projects}")
        
        # Статистика по товарам и изображениям
        from database.models_v4 import Product, ProductImage
        total_products = session.query(Product).count()
        total_images = session.query(ProductImage).count()
        
        print(f"\n📦 ОБЩАЯ СТАТИСТИКА ДАННЫХ:")
        print(f"   📦 Всего товаров: {total_products}")
        print(f"   🖼️ Всего изображений: {total_images}")
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        process_next_sheets(count)
    except KeyboardInterrupt:
        print("\n⚠️ Обработка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
