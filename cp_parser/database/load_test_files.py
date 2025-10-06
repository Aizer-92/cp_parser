#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт загрузки тестовых Excel файлов в таблицу PROJECTS
Создает записи с table_id и путями к файлам
"""

import sys
import os
from pathlib import Path
import logging

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.manager import db_manager, project_service

def generate_table_id(filename: str) -> str:
    """Генерация table_id из имени файла"""
    # Убираем расширение и заменяем спецсимволы на подчеркивания
    table_id = filename.replace('.xlsx', '').replace('.csv', '')
    # Заменяем проблемные символы
    table_id = table_id.replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')
    # Ограничиваем длину
    if len(table_id) > 50:
        table_id = table_id[:50]
    return table_id

def extract_project_name(filename: str) -> str:
    """Извлечение названия проекта из имени файла"""
    # Убираем расширение
    name = filename.replace('.xlsx', '').replace('.csv', '')
    
    # Для файлов типа google_sheet_20250923_Просчет-ОАЭ_Client__Description
    if 'Просчет-' in name:
        parts = name.split('_')
        # Ищем части после даты
        for i, part in enumerate(parts):
            if 'Просчет-' in part:
                project_parts = parts[i:]
                return '_'.join(project_parts).replace('_', ' ')
    
    # Для обычных файлов
    if name.startswith('google_sheet_'):
        # Убираем префикс google_sheet_ и дату
        parts = name.split('_')
        if len(parts) > 2:
            # Убираем google_sheet и дату
            return '_'.join(parts[2:]).replace('_', ' ')
    
    return name.replace('_', ' ')

def load_test_files_to_database():
    """Загрузка всех тестовых файлов в базу данных"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Путь к тестовым файлам
    test_data_dir = project_root / "test_data"
    
    if not test_data_dir.exists():
        logger.error(f"❌ Папка с тестовыми данными не найдена: {test_data_dir}")
        return False
    
    # Поиск всех Excel файлов
    excel_files = list(test_data_dir.glob("*.xlsx"))
    logger.info(f"📁 Найдено {len(excel_files)} Excel файлов")
    
    if not excel_files:
        logger.warning("⚠️ Excel файлы не найдены!")
        return False
    
    # Проверка подключения к БД
    if not db_manager.health_check():
        logger.error("❌ Не удается подключиться к базе данных")
        return False
    
    successful_imports = 0
    failed_imports = 0
    
    logger.info("🚀 Начинаю загрузку файлов в базу данных...")
    
    for file_path in excel_files:
        try:
            # Генерируем данные для записи
            table_id = generate_table_id(file_path.name)
            project_name = extract_project_name(file_path.name)
            file_size_mb = round(file_path.stat().st_size / (1024*1024), 2)
            
            # Создаем запись в базе
            project = project_service.create_project(
                table_id=table_id,
                project_name=project_name,
                file_name=file_path.name,
                file_path=str(file_path),
                file_size_mb=file_size_mb,
                parsing_status='pending'
            )
            
            logger.info(f"✅ {file_path.name} → ID: {project.id}, table_id: {table_id}")
            successful_imports += 1
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {file_path.name}: {e}")
            failed_imports += 1
    
    # Итоговая статистика
    logger.info("\n" + "="*60)
    logger.info("📊 ИТОГИ ЗАГРУЗКИ")
    logger.info("="*60)
    logger.info(f"✅ Успешно загружено: {successful_imports} файлов")
    logger.info(f"❌ Ошибок: {failed_imports} файлов")
    logger.info(f"📁 Всего файлов: {len(excel_files)}")
    
    if successful_imports > 0:
        logger.info("\n🎯 Файлы готовы к парсингу!")
        show_sample_records()
    
    return successful_imports > 0

def show_sample_records():
    """Показать несколько примеров загруженных записей"""
    from database.models import Project
    
    with db_manager.get_session() as session:
        projects = session.query(Project).limit(5).all()
        
        print("\n📋 ПРИМЕРЫ ЗАГРУЖЕННЫХ ЗАПИСЕЙ:")
        print("-" * 100)
        print(f"{'ID':<4} {'table_id':<25} {'Название проекта':<40} {'Размер':<8}")
        print("-" * 100)
        
        for project in projects:
            name_short = project.project_name[:37] + "..." if len(project.project_name) > 40 else project.project_name
            print(f"{project.id:<4} {project.table_id:<25} {name_short:<40} {project.file_size_mb:<8}")

def clear_projects_table():
    """Очистка таблицы проектов (для отладки)"""
    from database.models import Project
    
    response = input("⚠️ ВНИМАНИЕ! Это удалит все записи из таблицы PROJECTS. Продолжить? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Операция отменена")
        return False
    
    with db_manager.get_session() as session:
        deleted_count = session.query(Project).delete()
        session.commit()
        print(f"🗑️ Удалено {deleted_count} записей из таблицы PROJECTS")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Загрузка тестовых файлов в БД')
    parser.add_argument('--clear', action='store_true', help='Очистить таблицу проектов')
    parser.add_argument('--show', action='store_true', help='Показать загруженные записи')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_projects_table()
    elif args.show:
        show_sample_records()
    else:
        load_test_files_to_database()



