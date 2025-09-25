#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СОЗДАНИЕ ПОНЯТНОГО ОТЧЕТА ПО ПОЛНОТЕ ДАННЫХ
Четкий анализ того, что есть и чего не хватает
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_comprehensive_analysis():
    """Создание подробного анализа полноты данных"""
    
    print("📊 СОЗДАНИЕ ПОНЯТНОГО ОТЧЕТА ПО ПОЛНОТЕ ДАННЫХ")
    print("=" * 60)
    
    # Читаем расширенную таблицу
    df = pd.read_excel('ENHANCED_CATEGORIES_RANGES.xlsx', sheet_name='Расширенные_диапазоны')
    
    # Создаем индикаторы полноты данных
    df_analysis = df.copy()
    
    # Индикаторы наличия данных
    df_analysis['Есть_диапазоны_БД'] = (
        df_analysis['Цена_руб_мин'].notna() | 
        df_analysis['Тираж_мин'].notna() | 
        df_analysis['Плотность_мин'].notna()
    )
    
    df_analysis['Есть_данные_CSV'] = df_analysis['Популярная_категория'].notna()
    
    df_analysis['Есть_ставки_транспорт'] = (
        df_analysis['Ставка_жд_базовая'].notna() | 
        df_analysis['Ставка_авиа_базовая'].notna()
    )
    
    df_analysis['Есть_материалы'] = df_analysis['Материал_рекомендуемый'].notna()
    df_analysis['Есть_сертификаты'] = df_analysis['Сертификаты_требуемые'].notna()
    
    # Создаем категории полноты
    def get_completeness_category(row):
        has_db = row['Есть_диапазоны_БД']
        has_csv = row['Есть_данные_CSV']
        has_rates = row['Есть_ставки_транспорт']
        
        if has_db and has_csv and has_rates:
            return "🟢 ПОЛНЫЕ ДАННЫЕ"
        elif has_db and has_csv:
            return "🟡 БД + CSV (нет ставок)"
        elif has_db and not has_csv:
            return "🔵 ТОЛЬКО БД"
        elif not has_db and has_csv:
            return "🟠 ТОЛЬКО CSV"
        else:
            return "🔴 МИНИМАЛЬНЫЕ ДАННЫЕ"
    
    df_analysis['Полнота_данных'] = df_analysis.apply(get_completeness_category, axis=1)
    
    # Подсчитываем количество метрик
    df_analysis['Количество_диапазонов'] = (
        df_analysis['Цена_руб_мин'].notna().astype(int) +
        df_analysis['Цена_юань_мин'].notna().astype(int) +
        df_analysis['Тираж_мин'].notna().astype(int) +
        df_analysis['Плотность_мин'].notna().astype(int) +
        df_analysis['Транспорт_мин'].notna().astype(int)
    )
    
    # Создаем сводную таблицу для каждой категории
    summary_columns = [
        'Тип', 'Категория', 'Родитель', 'Товаров', 'Полнота_данных',
        'Популярная_категория', 'Материал_рекомендуемый', 
        'Количество_диапазонов', 'Есть_диапазоны_БД', 'Есть_данные_CSV',
        'Есть_ставки_транспорт', 'Есть_материалы', 'Есть_сертификаты',
        'Медиана_цены_руб', 'Медиана_плотности', 'Медиана_тиража',
        'Ставка_жд_базовая', 'Ставка_авиа_базовая', 'Сертификаты_требуемые'
    ]
    
    df_summary = df_analysis[summary_columns].copy()
    
    # Сортируем по полноте данных и количеству товаров
    completeness_order = {
        "🟢 ПОЛНЫЕ ДАННЫЕ": 1,
        "🟡 БД + CSV (нет ставок)": 2, 
        "🔵 ТОЛЬКО БД": 3,
        "🟠 ТОЛЬКО CSV": 4,
        "🔴 МИНИМАЛЬНЫЕ ДАННЫЕ": 5
    }
    
    df_summary['sort_order'] = df_summary['Полнота_данных'].map(completeness_order)
    df_summary = df_summary.sort_values(['sort_order', 'Товаров'], ascending=[True, False])
    df_summary = df_summary.drop('sort_order', axis=1)
    
    # Создаем статистику по полноте
    completeness_stats = df_summary.groupby('Полнота_данных').agg({
        'Категория': 'count',
        'Товаров': ['sum', 'mean']
    }).round(1)
    
    completeness_stats.columns = ['Количество_категорий', 'Всего_товаров', 'Средне_товаров']
    completeness_stats = completeness_stats.reset_index()
    
    # Создаем детальный анализ недостающих данных
    missing_data = []
    
    for _, row in df_analysis.iterrows():
        missing = []
        
        if not row['Есть_диапазоны_БД']:
            missing.append("Диапазоны из БД")
        if not row['Есть_данные_CSV']:
            missing.append("Данные из CSV")
        if not row['Есть_ставки_транспорт']:
            missing.append("Транспортные ставки")
        if not row['Есть_материалы']:
            missing.append("Рекомендуемые материалы")
        if not row['Есть_сертификаты']:
            missing.append("Сертификаты")
            
        # Проверяем конкретные диапазоны
        if pd.isna(row['Цена_руб_мин']):
            missing.append("Диапазон цен в рублях")
        if pd.isna(row['Плотность_мин']):
            missing.append("Диапазон плотности")
        if pd.isna(row['Тираж_мин']):
            missing.append("Диапазон тиражей")
            
        missing_data.append({
            'Категория': row['Категория'],
            'Тип': row['Тип'],
            'Товаров': row['Товаров'],
            'Полнота_данных': row['Полнота_данных'],
            'Отсутствует': "; ".join(missing) if missing else "Все данные есть"
        })
    
    df_missing = pd.DataFrame(missing_data)
    df_missing = df_missing.sort_values('Товаров', ascending=False)
    
    # Создаем таблицу приоритетов для доработки
    priority_categories = df_analysis[
        (df_analysis['Товаров'] >= 20) & 
        (~df_analysis['Есть_данные_CSV'])
    ][['Тип', 'Категория', 'Товаров', 'Медиана_цены_руб', 'Медиана_плотности']].copy()
    
    priority_categories = priority_categories.sort_values('Товаров', ascending=False)
    priority_categories['Приоритет'] = range(1, len(priority_categories) + 1)
    
    # Сохраняем результат
    output_file = Path(__file__).parent / "COMPREHENSIVE_DATA_ANALYSIS.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. Основная сводка по полноте
        df_summary.to_excel(writer, sheet_name='📊_Сводка_по_полноте', index=False)
        
        # 2. Статистика полноты данных
        completeness_stats.to_excel(writer, sheet_name='📈_Статистика_полноты', index=False)
        
        # 3. Полные данные (самые ценные)
        full_data = df_summary[df_summary['Полнота_данных'] == "🟢 ПОЛНЫЕ ДАННЫЕ"]
        if len(full_data) > 0:
            full_data.to_excel(writer, sheet_name='🟢_Полные_данные', index=False)
        
        # 4. БД + CSV без ставок
        partial_data = df_summary[df_summary['Полнота_данных'] == "🟡 БД + CSV (нет ставок)"]
        if len(partial_data) > 0:
            partial_data.to_excel(writer, sheet_name='🟡_БД_плюс_CSV', index=False)
        
        # 5. Только БД (нужно дополнить)
        db_only = df_summary[df_summary['Полнота_данных'] == "🔵 ТОЛЬКО БД"]
        if len(db_only) > 0:
            db_only.to_excel(writer, sheet_name='🔵_Только_БД', index=False)
        
        # 6. Только CSV (нужно найти товары)
        csv_only = df_summary[df_summary['Полнота_данных'] == "🟠 ТОЛЬКО CSV"]
        if len(csv_only) > 0:
            csv_only.to_excel(writer, sheet_name='🟠_Только_CSV', index=False)
        
        # 7. Детальный анализ недостающих данных
        df_missing.to_excel(writer, sheet_name='🔍_Анализ_пропусков', index=False)
        
        # 8. Приоритетные категории для доработки
        priority_categories.to_excel(writer, sheet_name='⚡_Приоритеты_доработки', index=False)
        
        # 9. Исходная полная таблица (для справки)
        df_analysis.to_excel(writer, sheet_name='📋_Полная_таблица', index=False)
    
    # Выводим статистику
    print(f"✅ Понятный отчет создан: {output_file}")
    print(f"📊 Листы:")
    print(f"  1. '📊_Сводка_по_полноте' - {len(df_summary)} категорий с индикаторами полноты")
    print(f"  2. '📈_Статистика_полноты' - сводная статистика по типам данных")
    print(f"  3. '🟢_Полные_данные' - {len(full_data)} категорий с полными данными")
    print(f"  4. '🟡_БД_плюс_CSV' - {len(partial_data)} категорий без ставок")
    print(f"  5. '🔵_Только_БД' - {len(db_only)} категорий только из БД")
    print(f"  6. '🟠_Только_CSV' - {len(csv_only)} категорий только из CSV")
    print(f"  7. '🔍_Анализ_пропусков' - детальный анализ недостающих данных")
    print(f"  8. '⚡_Приоритеты_доработки' - {len(priority_categories)} приоритетных категорий")
    print(f"  9. '📋_Полная_таблица' - исходные данные со всеми индикаторами")
    
    print()
    print("🎯 КЛЮЧЕВЫЕ ИНДИКАТОРЫ:")
    print("  • Есть_диапазоны_БД - есть ли диапазоны из базы данных")
    print("  • Есть_данные_CSV - есть ли данные из популярного CSV")
    print("  • Есть_ставки_транспорт - есть ли транспортные ставки")
    print("  • Количество_диапазонов - сколько метрик имеют диапазоны")
    print("  • Полнота_данных - общая оценка полноты информации")
    
    print()
    print("📈 СТАТИСТИКА ПОЛНОТЫ:")
    for _, row in completeness_stats.iterrows():
        print(f"  {row['Полнота_данных']}: {row['Количество_категорий']} категорий, {row['Всего_товаров']:,.0f} товаров")
    
    return output_file

if __name__ == "__main__":
    create_comprehensive_analysis()
