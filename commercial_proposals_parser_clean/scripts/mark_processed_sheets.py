#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для отметки уже спарсенных таблиц как обработанных
"""

import os
import sys
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, ProjectMetadata, Product, ProductImage

def mark_processed_sheets():
    """Отмечает уже спарсенные таблицы как обработанные в ProjectMetadata"""
    print("🔍 ПОИСК УЖЕ ОБРАБОТАННЫХ ТАБЛИЦ")
    print("=" * 50)
    
    session = DatabaseManager.get_session()
    
    try:
        # Получаем все таблицы с товарами (значит они спарсены)
        processed_sheets = session.query(SheetMetadata).join(Product).distinct().all()
        
        print(f"📊 Найдено обработанных таблиц: {len(processed_sheets)}")
        
        marked_count = 0
        
        for sheet in processed_sheets:
            print(f"\n🔍 Обрабатываем: {sheet.sheet_title}")
            
            # Получаем статистику
            products_count = session.query(Product).filter(Product.sheet_id == sheet.id).count()
            images_count = session.query(ProductImage).filter(ProductImage.sheet_id == sheet.id).count()
            
            print(f"   📦 Товаров: {products_count}")
            print(f"   🖼️ Изображений: {images_count}")
            
            # Ищем соответствующий проект в ProjectMetadata по URL
            if sheet.sheet_url:
                # Пытаемся найти проект по URL
                project = session.query(ProjectMetadata).filter(
                    ProjectMetadata.google_sheets_url == sheet.sheet_url
                ).first()
                
                if project:
                    if project.processing_status != 'completed':
                        project.processing_status = 'completed'
                        project.parsed_at = datetime.utcnow()
                        
                        # Связываем с SheetMetadata
                        if not project.sheet_metadata_id:
                            project.sheet_metadata_id = sheet.id
                        
                        marked_count += 1
                        print(f"   ✅ Проект отмечен как обработанный: {project.project_title[:50]}...")
                    else:
                        print(f"   ℹ️ Проект уже отмечен как обработанный")
                else:
                    print(f"   ⚠️ Проект не найден в ProjectMetadata по URL")
            else:
                print(f"   ⚠️ У таблицы нет URL для поиска проекта")
        
        session.commit()
        
        print(f"\n✅ ЗАВЕРШЕНО: отмечено {marked_count} проектов как обработанных")
        
        # Показываем статистику
        total_projects = session.query(ProjectMetadata).count()
        completed_projects = session.query(ProjectMetadata).filter(
            ProjectMetadata.processing_status == 'completed'
        ).count()
        pending_projects = session.query(ProjectMetadata).filter(
            ProjectMetadata.processing_status == 'pending'
        ).count()
        
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   📊 Всего проектов: {total_projects}")
        print(f"   ✅ Обработано: {completed_projects}")
        print(f"   ⏳ Ожидает обработки: {pending_projects}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    mark_processed_sheets()
