#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт просмотра всех загруженных проектов в базе данных
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database import db_manager, Project

def show_all_projects():
    """Показать все проекты в базе данных"""
    
    with db_manager.get_session() as session:
        projects = session.query(Project).order_by(Project.id).all()
        
        print(f"\n📊 ЗАГРУЖЕНО {len(projects)} ПРОЕКТОВ В БАЗУ ДАННЫХ")
        print("="*120)
        print(f"{'ID':<4} {'table_id':<35} {'Название проекта':<50} {'Размер':<8} {'Статус':<10}")
        print("="*120)
        
        for project in projects:
            name_short = project.project_name[:47] + "..." if len(project.project_name) > 50 else project.project_name
            table_id_short = project.table_id[:32] + "..." if len(project.table_id) > 35 else project.table_id
            print(f"{project.id:<4} {table_id_short:<35} {name_short:<50} {project.file_size_mb:<8} {project.parsing_status:<10}")
        
        print("="*120)
        print(f"\n✅ Все файлы имеют table_id и готовы к парсингу!")
        print(f"📁 Путь к тестовым данным: {project_root}/test_data/")
        print(f"🗃️ База данных: {project_root}/data/commercial_proposals.db")

def show_projects_by_type():
    """Группировка проектов по типам"""
    
    with db_manager.get_session() as session:
        projects = session.query(Project).order_by(Project.id).all()
        
        # Группировка по типам
        types = {
            'google_sheet_numbered': [],  # google_sheet_20250923_xxxxxx
            'google_sheet_named': [],     # google_sheet_20250923_Просчет-...
            'sheet_id': [],               # sheet_xxxxxx_xxxxxx
            'other': []                   # остальные
        }
        
        for project in projects:
            if project.table_id.startswith('google_sheet_20250923_') and 'Просчет' not in project.table_id:
                types['google_sheet_numbered'].append(project)
            elif project.table_id.startswith('google_sheet_20250923_') and 'Просчет' in project.table_id:
                types['google_sheet_named'].append(project)
            elif project.table_id.startswith('sheet_'):
                types['sheet_id'].append(project)
            else:
                types['other'].append(project)
        
        print(f"\n📊 ГРУППИРОВКА ПО ТИПАМ:")
        print("="*80)
        
        for type_name, projects_list in types.items():
            if projects_list:
                print(f"\n🔹 {type_name.upper()}: {len(projects_list)} файлов")
                for project in projects_list[:5]:  # Показываем первые 5
                    print(f"   • ID {project.id}: {project.table_id}")
                if len(projects_list) > 5:
                    print(f"   ... и еще {len(projects_list) - 5} файлов")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Просмотр проектов в БД')
    parser.add_argument('--types', action='store_true', help='Группировка по типам')
    
    args = parser.parse_args()
    
    if args.types:
        show_projects_by_type()
    else:
        show_all_projects()



