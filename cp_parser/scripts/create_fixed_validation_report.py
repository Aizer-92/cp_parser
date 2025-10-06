#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ИСПРАВЛЕННЫЙ скрипт для создания полного отчета по валидации всех таблиц
Корректно сохраняет рейтинги и детальную информацию о столбцах
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

def create_fixed_validation_report():
    print('🔍 СОЗДАНИЕ ИСПРАВЛЕННОГО ОТЧЕТА ПО ВАЛИДАЦИИ ВСЕХ ТАБЛИЦ')
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
            'analysis_version': '2.0_fixed',
            'description': 'Исправленная версия с корректным сохранением рейтингов и детальной информацией о столбцах'
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
                'missing_data': ['Весь файл отсутствует'],
                'columns_analysis': {
                    'main_columns': {'found': [], 'missing': ['A', 'B', 'C', 'D', 'E']},
                    'price_columns': {'found': [], 'missing': ['F', 'G', 'H', 'I', 'J', 'K', 'L', 'N']},
                    'routes': {'found': [], 'missing': ['F', 'I', 'L']}
                }
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
                        'missing_data': ['Лист с названием Просчет или Calculation'],
                        'columns_analysis': {
                            'main_columns': {'found': [], 'missing': ['A', 'B', 'C', 'D', 'E']},
                            'price_columns': {'found': [], 'missing': ['F', 'G', 'H', 'I', 'J', 'K', 'L', 'N']},
                            'routes': {'found': [], 'missing': ['F', 'I', 'L']}
                        }
                    }
                    validation_results['summary']['failed'].append(project.id)
                else:
                    ws = wb[sheet_name]
                    result = parser.validate_table_structure(ws, sheet_name)
                    
                    # ИСПРАВЛЕНИЕ: Берем правильный рейтинг из результата
                    rating = result.get('confidence_score', result.get('rating', 0))
                    
                    # Анализируем отсутствующие данные
                    missing_data = []
                    errors = result.get('validation_errors', result.get('errors', []))
                    
                    # Детальный анализ столбцов
                    matched_main = result.get('matched_main_columns', {})
                    matched_price = result.get('matched_price_columns', {})
                    matched_routes = result.get('matched_routes', {})
                    complete_routes = result.get('complete_routes', [])
                    
                    # Анализ основных столбцов
                    main_found = []
                    main_missing = []
                    for col, info in matched_main.items():
                        if info.get('matched', False):
                            main_found.append(f"{col}: {info.get('actual', '')}")
                        else:
                            main_missing.append(f"{col}: ожидалось {info.get('expected', [])}")
                            missing_data.append(f'Основной столбец {col}: {info.get("expected", "неизвестно")}')
                    
                    # Анализ ценовых столбцов  
                    price_found = []
                    price_missing = []
                    for col, info in matched_price.items():
                        if info.get('matched', False):
                            price_found.append(f"{col}: {info.get('actual', '')}")
                        else:
                            price_missing.append(f"{col}: ожидалось {info.get('expected', [])}")
                            missing_data.append(f'Ценовой столбец {col}: {info.get("expected", "неизвестно")}')
                    
                    # Анализ маршрутов
                    routes_found = []
                    routes_missing = []
                    for col, info in matched_routes.items():
                        if info.get('matched', False):
                            routes_found.append(f"{col}: {info.get('actual', '')}")
                        else:
                            routes_missing.append(f"{col}: ожидалось {info.get('expected', [])}")
                    
                    # Проверяем полные маршруты
                    if not complete_routes:
                        missing_data.append('Полные маршруты (тип + тираж + цена + сроки)')
                    
                    project_result['validation'] = {
                        'rating': rating,
                        'status': 'analyzed',
                        'errors': errors,
                        'missing_data': missing_data,
                        'sheet_name': sheet_name,
                        'complete_routes': complete_routes,
                        'columns_analysis': {
                            'main_columns': {
                                'found': main_found,
                                'missing': main_missing,
                                'total_expected': len(matched_main),
                                'total_found': len(main_found)
                            },
                            'price_columns': {
                                'found': price_found,
                                'missing': price_missing,
                                'total_expected': len(matched_price),
                                'total_found': len(price_found)
                            },
                            'routes': {
                                'found': routes_found,
                                'missing': routes_missing,
                                'complete_routes': complete_routes,
                                'total_complete': len(complete_routes)
                            }
                        },
                        'raw_validation_result': result  # Сохраняем полный результат для отладки
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
                    'missing_data': ['Невозможно проанализировать из-за ошибки'],
                    'columns_analysis': {
                        'main_columns': {'found': [], 'missing': ['Ошибка анализа']},
                        'price_columns': {'found': [], 'missing': ['Ошибка анализа']},
                        'routes': {'found': [], 'missing': ['Ошибка анализа']}
                    }
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
    results_file = f'fixed_validation_results_{timestamp}.json'

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print('🎉 ИСПРАВЛЕННЫЙ АНАЛИЗ ЗАВЕРШЕН!')
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
    
    if validation_results['summary']['acceptable']:
        print()
        print('📊 ПРИМЕРЫ ПРИЕМЛЕМЫХ ФАЙЛОВ (60-74%):')
        for project_id in validation_results['summary']['acceptable'][:10]:  # Первые 10
            project_data = next(p for p in validation_results['projects'] if p['id'] == project_id)
            rating = project_data['validation']['rating']
            print(f'   ID {project_id}: {rating:.1f}% - {project_data["name"][:40]}...')

    session.close()
    return results_file

if __name__ == '__main__':
    create_fixed_validation_report()

