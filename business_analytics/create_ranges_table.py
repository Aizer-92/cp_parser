#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СОЗДАНИЕ ТАБЛИЦЫ ДИАПАЗОНОВ В ОТДЕЛЬНЫХ СТОЛБЦАХ
Удобный формат для дальнейшего использования
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from business_final_analyzer import BusinessFinalAnalyzer

def create_ranges_table():
    """Создание таблицы с диапазонами в отдельных столбцах"""
    
    print("🎯 СОЗДАНИЕ ТАБЛИЦЫ ДИАПАЗОНОВ В ОТДЕЛЬНЫХ СТОЛБЦАХ")
    print("=" * 60)
    
    # Загружаем данные
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    analyzer = BusinessFinalAnalyzer(db_path)
    
    # Запускаем анализ
    stats, coverage, excluded_count, total_products = analyzer.run_business_analysis()
    
    # Создаем таблицу с диапазонами
    ranges_data = []
    
    for stat in stats:
        if not stat.get('gaussian_ranges'):
            continue
            
        row = {
            'Тип': stat['тип'],
            'Категория': stat['категория'],
            'Родитель': stat['родитель'],
            'Товаров': stat['товары'],
            'Медиана_цены_руб': stat.get('медиана_цены_rub'),
            'Медиана_цены_юань': stat.get('медиана_цены_cny'),
            'Медиана_тиража': stat.get('средний_тираж'),
            'Медиана_плотности': stat.get('медиана_плотности'),
            'Медиана_транспорта': stat.get('медиана_транспорта_usd'),
        }
        
        # Добавляем диапазоны для каждой метрики
        for field, ranges in stat['gaussian_ranges'].items():
            if field == 'price_rub':
                row.update({
                    'Цена_руб_мин': ranges['lower_70'],
                    'Цена_руб_макс': ranges['upper_70'],
                    'Цена_руб_медиана': ranges['median'],
                    'Цена_руб_среднее': ranges['mean'],
                    'Цена_руб_стд': ranges['std'],
                    'Цена_руб_количество': ranges['count']
                })
            elif field == 'price_cny':
                row.update({
                    'Цена_юань_мин': ranges['lower_70'],
                    'Цена_юань_макс': ranges['upper_70'],
                    'Цена_юань_медиана': ranges['median'],
                    'Цена_юань_среднее': ranges['mean'],
                    'Цена_юань_стд': ranges['std'],
                    'Цена_юань_количество': ranges['count']
                })
            elif field == 'avg_requested_tirage':
                row.update({
                    'Тираж_мин': ranges['lower_70'],
                    'Тираж_макс': ranges['upper_70'],
                    'Тираж_медиана': ranges['median'],
                    'Тираж_среднее': ranges['mean'],
                    'Тираж_стд': ranges['std'],
                    'Тираж_количество': ranges['count']
                })
            elif field == 'cargo_density':
                row.update({
                    'Плотность_мин': ranges['lower_70'],
                    'Плотность_макс': ranges['upper_70'],
                    'Плотность_медиана': ranges['median'],
                    'Плотность_среднее': ranges['mean'],
                    'Плотность_стд': ranges['std'],
                    'Плотность_количество': ranges['count']
                })
            elif field == 'transport_tariff':
                row.update({
                    'Транспорт_мин': ranges['lower_70'],
                    'Транспорт_макс': ranges['upper_70'],
                    'Транспорт_медиана': ranges['median'],
                    'Транспорт_среднее': ranges['mean'],
                    'Транспорт_стд': ranges['std'],
                    'Транспорт_количество': ranges['count']
                })
        
        ranges_data.append(row)
    
    # Создаем DataFrame
    df_ranges = pd.DataFrame(ranges_data)
    
    # Сортируем по количеству товаров
    df_ranges = df_ranges.sort_values('Товаров', ascending=False)
    
    # Сохраняем в Excel
    output_file = Path(__file__).parent / "CATEGORIES_RANGES_TABLE.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Основная таблица с диапазонами
        df_ranges.to_excel(writer, sheet_name='Диапазоны_категорий', index=False)
        
        # ТОП-20 категорий
        df_top20 = df_ranges.head(20)
        df_top20.to_excel(writer, sheet_name='ТОП_20_категорий', index=False)
        
        # Только основные категории
        df_main = df_ranges[df_ranges['Тип'] == 'main']
        df_main.to_excel(writer, sheet_name='Основные_категории', index=False)
        
        # Сводка по метрикам
        summary_data = []
        for col in ['Цена_руб', 'Цена_юань', 'Тираж', 'Плотность', 'Транспорт']:
            min_col = f'{col}_мин'
            max_col = f'{col}_макс'
            median_col = f'{col}_медиана'
            count_col = f'{col}_количество'
            
            if min_col in df_ranges.columns:
                valid_data = df_ranges[df_ranges[count_col].notna()]
                if len(valid_data) > 0:
                    summary_data.append({
                        'Метрика': col,
                        'Категорий_с_данными': len(valid_data),
                        'Общий_мин': valid_data[min_col].min(),
                        'Общий_макс': valid_data[max_col].max(),
                        'Средняя_медиана': valid_data[median_col].mean(),
                        'Общее_количество_товаров': valid_data[count_col].sum()
                    })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Сводка_метрик', index=False)
    
    print(f"✅ Таблица диапазонов создана: {output_file}")
    print(f"📊 Листы:")
    print(f"  1. 'Диапазоны_категорий' - {len(df_ranges)} категорий с полными диапазонами")
    print(f"  2. 'ТОП_20_категорий' - лидеры по количеству товаров")
    print(f"  3. 'Основные_категории' - только основные категории")
    print(f"  4. 'Сводка_метрик' - общая статистика по всем метрикам")
    print()
    print(f"🎯 СТРУКТУРА ДИАПАЗОНОВ:")
    print(f"  • Каждая метрика имеет 6 столбцов: мин, макс, медиана, среднее, стд, количество")
    print(f"  • Готово для импорта в другие системы")
    print(f"  • Удобно для фильтрации и анализа")
    
    # Показываем пример структуры
    print(f"\n📋 ПРИМЕР СТРУКТУРЫ (первые 3 строки):")
    print("=" * 80)
    display_cols = ['Тип', 'Категория', 'Товаров', 'Цена_руб_мин', 'Цена_руб_макс', 
                   'Плотность_мин', 'Плотность_макс', 'Тираж_мин', 'Тираж_макс']
    available_cols = [col for col in display_cols if col in df_ranges.columns]
    print(df_ranges[available_cols].head(3).to_string(index=False))
    
    analyzer.conn.close()
    return output_file

if __name__ == "__main__":
    create_ranges_table()
