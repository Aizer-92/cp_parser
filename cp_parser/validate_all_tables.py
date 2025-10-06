#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Валидация структуры всех таблиц в production_data
Проверяет какие файлы пройдут строгую валидацию парсера
"""

import sys
import os
from pathlib import Path
import time
from collections import defaultdict

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.structure_parser import CommercialProposalParser
from openpyxl import load_workbook

def validate_single_file(parser, file_path):
    """Валидирует один Excel файл"""
    try:
        # Загружаем workbook
        wb = load_workbook(file_path, data_only=True)
        
        # Находим подходящий лист
        sheet_name = parser.find_matching_sheet(wb)
        if not sheet_name:
            return {
                'valid': False,
                'rating': 0,
                'errors': ['Не найден подходящий лист (Просчет, Calculation)'],
                'sheet_name': None
            }
        
        ws = wb[sheet_name]
        
        # Проверяем структуру таблицы
        structure_result = parser.validate_table_structure(ws, sheet_name)
        
        # Определяем валидность по минимальному рейтингу
        min_rating = 62.5  # Минимальный рейтинг для считания файла валидным
        is_valid = structure_result['confidence_score'] >= min_rating
        
        return {
            'valid': is_valid,
            'rating': structure_result['confidence_score'],
            'errors': structure_result.get('validation_errors', []),
            'sheet_name': sheet_name
        }
        
    except Exception as e:
        return {
            'valid': False,
            'rating': 0,
            'errors': [f'Ошибка обработки файла: {str(e)}'],
            'sheet_name': None
        }

def validate_all_production_files():
    """Валидирует все файлы в production_data"""
    
    print("🔍 ВАЛИДАЦИЯ СТРУКТУРЫ ВСЕХ ТАБЛИЦ")
    print("=" * 60)
    
    production_dir = Path("production_data")
    if not production_dir.exists():
        print("❌ Папка production_data не найдена!")
        return
    
    # Получаем все xlsx файлы
    xlsx_files = list(production_dir.glob("*.xlsx"))
    total_files = len(xlsx_files)
    
    if total_files == 0:
        print("❌ Не найдено Excel файлов в production_data/")
        return
    
    print(f"📊 Найдено файлов для проверки: {total_files}")
    print("-" * 60)
    
    # Инициализируем парсер
    parser = CommercialProposalParser()
    
    # Статистика
    stats = {
        'total': total_files,
        'valid': 0,
        'invalid': 0,
        'errors': 0,
        'valid_files': [],
        'invalid_files': [],
        'error_files': [],
        'rating_distribution': defaultdict(int)
    }
    
    start_time = time.time()
    
    for i, file_path in enumerate(xlsx_files, 1):
        try:
            print(f"{i:3d}/{total_files}: {file_path.name[:50]}")
            
            # Валидируем структуру файла
            result = validate_single_file(parser, str(file_path))
            
            if result['valid']:
                stats['valid'] += 1
                stats['valid_files'].append({
                    'name': file_path.name,
                    'rating': result.get('rating', 0),
                    'sheet': result.get('sheet_name', 'N/A')
                })
                print(f"      ✅ ВАЛИДНА - рейтинг: {result.get('rating', 0):.1f}%")
            else:
                stats['invalid'] += 1
                stats['invalid_files'].append({
                    'name': file_path.name,
                    'rating': result.get('rating', 0),
                    'errors': result.get('errors', [])
                })
                errors = result.get('errors', [])
                main_error = errors[0] if errors else 'неизвестная ошибка'
                print(f"      ❌ НЕ ВАЛИДНА - {main_error}")
            
            # Статистика по рейтингам
            rating = result.get('rating', 0)
            rating_range = int(rating // 10) * 10
            stats['rating_distribution'][rating_range] += 1
            
        except Exception as e:
            stats['errors'] += 1
            stats['error_files'].append({
                'name': file_path.name,
                'error': str(e)
            })
            print(f"      💥 ОШИБКА: {str(e)[:50]}")
        
        # Прогресс каждые 20 файлов
        if i % 20 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (total_files - i) * avg_time
            valid_percent = (stats['valid'] / i) * 100
            print(f"\n⏱️  Прогресс: {i}/{total_files} ({i/total_files*100:.1f}%)")
            print(f"   Валидных: {stats['valid']}/{i} ({valid_percent:.1f}%)")
            print(f"   Время: {elapsed:.1f}с, осталось: ~{remaining:.1f}с\n")
    
    # Финальная статистика
    elapsed_total = time.time() - start_time
    valid_percent = (stats['valid'] / stats['total']) * 100
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА ВАЛИДАЦИИ:")
    print("=" * 60)
    print(f"⏱️  Время выполнения: {elapsed_total:.1f} секунд")
    print(f"📁 Всего файлов: {stats['total']}")
    print(f"✅ Валидных файлов: {stats['valid']} ({valid_percent:.1f}%)")
    print(f"❌ Невалидных файлов: {stats['invalid']}")
    print(f"💥 Ошибок обработки: {stats['errors']}")
    
    # Распределение по рейтингам
    print(f"\n📈 РАСПРЕДЕЛЕНИЕ ПО РЕЙТИНГАМ СООТВЕТСТВИЯ:")
    for rating_range in sorted(stats['rating_distribution'].keys()):
        count = stats['rating_distribution'][rating_range]
        percent = (count / stats['total']) * 100
        print(f"  {rating_range:2d}-{rating_range+9:2d}%: {count:3d} файлов ({percent:.1f}%)")
    
    # ТОП валидных файлов
    if stats['valid_files']:
        print(f"\n🏆 ТОП-10 ВАЛИДНЫХ ФАЙЛОВ:")
        top_valid = sorted(stats['valid_files'], key=lambda x: x['rating'], reverse=True)[:10]
        for i, file_info in enumerate(top_valid, 1):
            print(f"  {i:2d}. {file_info['rating']:5.1f}% - {file_info['name'][:50]}")
    
    # Основные причины невалидности
    if stats['invalid_files']:
        print(f"\n❌ ОСНОВНЫЕ ПРИЧИНЫ НЕВАЛИДНОСТИ:")
        error_counts = defaultdict(int)
        for file_info in stats['invalid_files']:
            errors = file_info.get('errors', [])
            if errors:
                error_counts[errors[0]] += 1
        
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            percent = (count / stats['invalid']) * 100
            print(f"  • {error}: {count} файлов ({percent:.1f}%)")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    if valid_percent >= 70:
        print(f"  🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! {valid_percent:.1f}% файлов готовы к парсингу")
    elif valid_percent >= 50:
        print(f"  ✅ ХОРОШИЙ РЕЗУЛЬТАТ! {valid_percent:.1f}% файлов готовы к парсингу")
    elif valid_percent >= 30:
        print(f"  ⚠️  СРЕДНИЙ РЕЗУЛЬТАТ! {valid_percent:.1f}% файлов требуют улучшения парсера")
    else:
        print(f"  ❌ НИЗКИЙ РЕЗУЛЬТАТ! Только {valid_percent:.1f}% файлов готовы к парсингу")
    
    print(f"\n🚀 Готово! Валидные файлы можно парсить командой:")
    print(f"   python3 production_parser.py")

if __name__ == "__main__":
    validate_all_production_files()
