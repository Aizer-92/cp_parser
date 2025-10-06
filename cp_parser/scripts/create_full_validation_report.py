#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Создание полного отчета по валидации всех таблиц
Анализирует все проекты один раз и сохраняет результаты в JSON
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import time

sys.path.append('.')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Project
from src.structure_parser import CommercialProposalParser
from openpyxl import load_workbook

def create_full_validation_report():
    print('🔍 СОЗДАНИЕ ПОЛНОГО ОТЧЕТА ПО ВАЛИДАЦИИ ВСЕХ ТАБЛИЦ')
    print('=' * 70)

    db_path = Path('database/commercial_proposals.db')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    parser = CommercialProposalParser()

    # Получаем все проекты
    all_projects = session.query(Project).all()
    print(f'📋 Всего проектов для анализа: {len(all_projects)}')

    validation_results = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'total_projects': len(all_projects),
            'analysis_version': '1.0'
        },
        'projects': [],
        'summary': {
            'excellent': [],      # 90%+
            'good': [],          # 75-89%
            'acceptable': [],    # 60-74%
            'poor': [],          # 40-59%
            'failed': []         # <40%
        }
    }

    start_time = time.time()
    processed = 0

    for project in all_projects:
        processed += 1
        
        # Прогресс каждые 100 файлов
        if processed % 100 == 0 or processed == len(all_projects):
            elapsed = (time.time() - start_time) / 60
            remaining = ((elapsed / processed) * (len(all_projects) - processed)) if processed > 0 else 0
            print(f'\r🔄 Обработано: {processed}/{len(all_projects)} ({processed/len(all_projects)*100:.1f}%) | ⏱️ {elapsed:.1f}мин | Осталось: ~{remaining:.1f}мин', end='', flush=True)
        
        file_path = Path('production_data') / project.file_name
        
        project_result = {
            'id': project.id,
            'name': project.project_name,
            'client': project.client_name,
            'region': project.region,
            'file_name': project.file_name,
            'file_exists': file_path.exists(),
            'validation': None
        }
        
        if not file_path.exists():
            project_result['validation'] = {
                'rating': 0,
                'status': 'file_not_found',
                'errors': ['Файл не найден'],
                'missing_data': ['Весь файл отсутствует']
            }
            validation_results['summary']['failed'].append(project.id)
        else:
            try:
                wb = load_workbook(str(file_path), data_only=True)
                sheet_name = parser.find_matching_sheet(wb)
                
                if not sheet_name:
                    project_result['validation'] = {
                        'rating': 0,
                        'status': 'no_valid_sheet',
                        'errors': ['Не найден подходящий лист (Просчет, Calculation)'],
                        'missing_data': ['Лист с названием Просчет или Calculation']
                    }
                    validation_results['summary']['failed'].append(project.id)
                else:
                    ws = wb[sheet_name]
                    result = parser.validate_table_structure(ws, sheet_name)
                    rating = result.get('rating', 0)
                    
                    # Анализируем отсутствующие данные
                    missing_data = []
                    errors = result.get('errors', [])
                    
                    # Проверяем основные столбцы
                    matched_basic = result.get('matched_basic_columns', {})
                    for col, info in matched_basic.items():
                        if not info.get('matched', False):
                            missing_data.append(f'Столбец {col}: {info.get("expected", "неизвестно")}')
                    
                    # Проверяем ценовые столбцы  
                    matched_price = result.get('matched_price_columns', {})
                    for col, info in matched_price.items():
                        if not info.get('matched', False):
                            missing_data.append(f'Ценовой столбец {col}: {info.get("expected", "неизвестно")}')
                    
                    # Проверяем маршруты
                    complete_routes = result.get('complete_routes', [])
                    if not complete_routes:
                        missing_data.append('Полные маршруты (тип + тираж + цена + сроки)')
                    
                    project_result['validation'] = {
                        'rating': rating,
                        'status': 'analyzed',
                        'errors': errors,
                        'missing_data': missing_data,
                        'sheet_name': sheet_name,
                        'complete_routes': complete_routes,
                        'matched_basic_columns': matched_basic,
                        'matched_price_columns': matched_price
                    }
                    
                    # Категоризируем по рейтингу
                    if rating >= 90:
                        validation_results['summary']['excellent'].append(project.id)
                    elif rating >= 75:
                        validation_results['summary']['good'].append(project.id)
                    elif rating >= 60:
                        validation_results['summary']['acceptable'].append(project.id)
                    elif rating >= 40:
                        validation_results['summary']['poor'].append(project.id)
                    else:
                        validation_results['summary']['failed'].append(project.id)
                        
            except Exception as e:
                project_result['validation'] = {
                    'rating': 0,
                    'status': 'error',
                    'errors': [f'Критическая ошибка: {str(e)}'],
                    'missing_data': ['Невозможно проанализировать из-за ошибки']
                }
                validation_results['summary']['failed'].append(project.id)
        
        validation_results['projects'].append(project_result)

    print()  # Новая строка после прогресса
    end_time = time.time()
    duration = (end_time - start_time) / 60

    # Финальная статистика
    validation_results['metadata']['processing_time_minutes'] = duration
    validation_results['metadata']['summary_stats'] = {
        'excellent_90_plus': len(validation_results['summary']['excellent']),
        'good_75_89': len(validation_results['summary']['good']),
        'acceptable_60_74': len(validation_results['summary']['acceptable']),
        'poor_40_59': len(validation_results['summary']['poor']),
        'failed_under_40': len(validation_results['summary']['failed'])
    }

    # Сохраняем результат
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'complete_validation_results_{timestamp}.json'

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print('🎉 АНАЛИЗ ЗАВЕРШЕН!')
    print('=' * 50)
    print(f'⏱️ Время обработки: {duration:.1f} минут')
    print(f'📊 Обработано проектов: {processed}')
    print()
    print('📈 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:')
    print(f'🏆 Отличные (90%+):     {len(validation_results["summary"]["excellent"])}')
    print(f'✅ Хорошие (75-89%):    {len(validation_results["summary"]["good"])}')
    print(f'📊 Приемлемые (60-74%): {len(validation_results["summary"]["acceptable"])}')
    print(f'⚠️ Слабые (40-59%):     {len(validation_results["summary"]["poor"])}')
    print(f'❌ Неудачные (<40%):    {len(validation_results["summary"]["failed"])}')
    print()
    print(f'💾 Результаты сохранены: {results_file}')
    
    # Показываем примеры отличных файлов
    if validation_results['summary']['excellent']:
        print()
        print('🏆 ПРИМЕРЫ ОТЛИЧНЫХ ФАЙЛОВ (90%+):')
        for project_id in validation_results['summary']['excellent'][:10]:  # Первые 10
            project_data = next(p for p in validation_results['projects'] if p['id'] == project_id)
            rating = project_data['validation']['rating']
            print(f'   ID {project_id}: {rating:.1f}% - {project_data["name"][:40]}...')
    
    if validation_results['summary']['good']:
        print()
        print('✅ ПРИМЕРЫ ХОРОШИХ ФАЙЛОВ (75-89%):')
        for project_id in validation_results['summary']['good'][:10]:  # Первые 10
            project_data = next(p for p in validation_results['projects'] if p['id'] == project_id)
            rating = project_data['validation']['rating']
            print(f'   ID {project_id}: {rating:.1f}% - {project_data["name"][:40]}...')

    session.close()
    return results_file

if __name__ == '__main__':
    create_full_validation_report()

