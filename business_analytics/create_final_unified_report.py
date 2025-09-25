#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СОЗДАНИЕ ФИНАЛЬНОГО ОБЪЕДИНЕННОГО ОТЧЕТА
Объединение всех данных после умного поиска
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_final_unified_report():
    """Создание финального объединенного отчета"""
    
    print("🎯 СОЗДАНИЕ ФИНАЛЬНОГО ОБЪЕДИНЕННОГО ОТЧЕТА")
    print("=" * 60)
    
    # 1. Читаем исходную расширенную таблицу
    df_original = pd.read_excel('ENHANCED_CATEGORIES_RANGES.xlsx', sheet_name='Расширенные_диапазоны')
    print(f"📊 Исходная таблица: {len(df_original)} категорий, {df_original['Товаров'].sum():,} товаров")
    
    # Рассчитываем полноту данных для исходной таблицы
    df_original['Есть_диапазоны_БД'] = (
        df_original['Цена_руб_мин'].notna() | 
        df_original['Тираж_мин'].notna() | 
        df_original['Плотность_мин'].notna()
    )
    
    df_original['Есть_данные_CSV'] = df_original['Популярная_категория'].notna()
    
    df_original['Есть_ставки_транспорт'] = (
        df_original['Ставка_жд_базовая'].notna() | 
        df_original['Ставка_авиа_базовая'].notna()
    )
    
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
    
    df_original['Полнота_данных'] = df_original.apply(get_completeness_category, axis=1)
    
    # 2. Читаем дополненные категории из CSV
    df_enhanced_csv = pd.read_excel('ENHANCED_CSV_CATEGORIES.xlsx', sheet_name='Дополненные_категории')
    print(f"📊 Дополненные CSV: {len(df_enhanced_csv)} категорий, {df_enhanced_csv['Товаров'].sum():,} товаров")
    
    # 3. Объединяем данные
    # Удаляем из исходной таблицы категории, которые были дополнены
    enhanced_categories = set(df_enhanced_csv['Категория'].values)
    df_original_filtered = df_original[~df_original['Категория'].isin(enhanced_categories)].copy()
    
    print(f"📊 После исключения дублей: {len(df_original_filtered)} исходных категорий")
    
    # Объединяем
    df_unified = pd.concat([df_original_filtered, df_enhanced_csv], ignore_index=True)
    print(f"✅ Объединенная таблица: {len(df_unified)} категорий, {df_unified['Товаров'].sum():,} товаров")
    
    # 4. Пересчитываем индикаторы полноты данных
    df_unified['Есть_диапазоны_БД'] = (
        df_unified['Цена_руб_мин'].notna() | 
        df_unified['Тираж_мин'].notna() | 
        df_unified['Плотность_мин'].notna()
    )
    
    df_unified['Есть_данные_CSV'] = df_unified['Популярная_категория'].notna()
    
    df_unified['Есть_ставки_транспорт'] = (
        df_unified['Ставка_жд_базовая'].notna() | 
        df_unified['Ставка_авиа_базовая'].notna()
    )
    
    df_unified['Есть_материалы'] = df_unified['Материал_рекомендуемый'].notna()
    df_unified['Есть_сертификаты'] = df_unified['Сертификаты_требуемые'].notna()
    
    # Обновляем категории полноты
    
    df_unified['Полнота_данных'] = df_unified.apply(get_completeness_category, axis=1)
    
    # Подсчитываем количество диапазонов
    df_unified['Количество_диапазонов'] = (
        df_unified['Цена_руб_мин'].notna().astype(int) +
        df_unified['Цена_юань_мин'].notna().astype(int) +
        df_unified['Тираж_мин'].notna().astype(int) +
        df_unified['Плотность_мин'].notna().astype(int) +
        df_unified['Транспорт_мин'].notna().astype(int)
    )
    
    # 5. Создаем итоговые сводки
    
    # Статистика полноты
    completeness_stats = df_unified.groupby('Полнота_данных').agg({
        'Категория': 'count',
        'Товаров': ['sum', 'mean']
    }).round(1)
    completeness_stats.columns = ['Количество_категорий', 'Всего_товаров', 'Средне_товаров']
    completeness_stats = completeness_stats.reset_index()
    
    # Сортируем по полноте данных
    completeness_order = {
        "🟢 ПОЛНЫЕ ДАННЫЕ": 1,
        "🟡 БД + CSV (нет ставок)": 2, 
        "🔵 ТОЛЬКО БД": 3,
        "🟠 ТОЛЬКО CSV": 4,
        "🔴 МИНИМАЛЬНЫЕ ДАННЫЕ": 5
    }
    
    df_unified['sort_order'] = df_unified['Полнота_данных'].map(completeness_order)
    df_unified = df_unified.sort_values(['sort_order', 'Товаров'], ascending=[True, False])
    df_unified = df_unified.drop('sort_order', axis=1)
    
    # 6. Сводка основных колонок
    summary_columns = [
        'Тип', 'Категория', 'Родитель', 'Товаров', 'Полнота_данных',
        'Популярная_категория', 'Материал_рекомендуемый', 
        'Количество_диапазонов', 'Есть_диапазоны_БД', 'Есть_данные_CSV',
        'Есть_ставки_транспорт', 'Есть_материалы', 'Есть_сертификаты',
        'Медиана_цены_руб', 'Медиана_плотности', 'Медиана_тиража',
        'Ставка_жд_базовая', 'Ставка_авиа_базовая', 'Сертификаты_требуемые'
    ]
    
    df_summary = df_unified[summary_columns].copy()
    
    # Анализ изменений
    comparison_stats = pd.DataFrame([{
        'Категория': 'ДО объединения',
        'Всего_категорий': len(df_original),
        'Всего_товаров': df_original['Товаров'].sum(),
        'Полных_данных': len(df_original[df_original['Полнота_данных'] == "🟢 ПОЛНЫЕ ДАННЫЕ"]),
        'БД_плюс_CSV': len(df_original[df_original['Полнота_данных'] == "🟡 БД + CSV (нет ставок)"]),
        'Только_БД': len(df_original[df_original['Полнота_данных'] == "🔵 ТОЛЬКО БД"]),
        'Только_CSV': len(df_original[df_original['Полнота_данных'] == "🟠 ТОЛЬКО CSV"])
    }, {
        'Категория': 'ПОСЛЕ объединения',
        'Всего_категорий': len(df_unified),
        'Всего_товаров': df_unified['Товаров'].sum(),
        'Полных_данных': len(df_unified[df_unified['Полнота_данных'] == "🟢 ПОЛНЫЕ ДАННЫЕ"]),
        'БД_плюс_CSV': len(df_unified[df_unified['Полнота_данных'] == "🟡 БД + CSV (нет ставок)"]),
        'Только_БД': len(df_unified[df_unified['Полнота_данных'] == "🔵 ТОЛЬКО БД"]),
        'Только_CSV': len(df_unified[df_unified['Полнота_данных'] == "🟠 ТОЛЬКО CSV"])
    }])
    
    # Рассчитываем изменения (только числовые колонки)
    numeric_cols = ['Всего_категорий', 'Всего_товаров', 'Полных_данных', 'БД_плюс_CSV', 'Только_БД', 'Только_CSV']
    changes = {}
    changes['Категория'] = 'ИЗМЕНЕНИЯ (+/-)'
    
    for col in numeric_cols:
        changes[col] = comparison_stats.loc[1, col] - comparison_stats.loc[0, col]
    
    comparison_stats.loc[2] = pd.Series(changes)
    
    # 7. Сохраняем результат
    output_file = Path(__file__).parent / "FINAL_UNIFIED_ANALYSIS.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. Основная сводка
        df_summary.to_excel(writer, sheet_name='📊_Итоговая_сводка', index=False)
        
        # 2. Статистика полноты (обновленная)
        completeness_stats.to_excel(writer, sheet_name='📈_Новая_статистика', index=False)
        
        # 3. Сравнение до/после
        comparison_stats.to_excel(writer, sheet_name='🔄_Сравнение_изменений', index=False)
        
        # 4. Полные данные (обновленные)
        full_data = df_unified[df_unified['Полнота_данных'] == "🟢 ПОЛНЫЕ ДАННЫЕ"]
        if len(full_data) > 0:
            full_data.to_excel(writer, sheet_name='🟢_Полные_данные_ИТОГ', index=False)
        
        # 5. БД + CSV без ставок
        partial_data = df_unified[df_unified['Полнота_данных'] == "🟡 БД + CSV (нет ставок)"]
        if len(partial_data) > 0:
            partial_data.to_excel(writer, sheet_name='🟡_БД_плюс_CSV_ИТОГ', index=False)
        
        # 6. Только БД (уменьшилось)
        db_only = df_unified[df_unified['Полнота_данных'] == "🔵 ТОЛЬКО БД"]
        if len(db_only) > 0:
            db_only.to_excel(writer, sheet_name='🔵_Только_БД_ИТОГ', index=False)
        
        # 7. Только CSV (должно стать меньше)
        csv_only = df_unified[df_unified['Полнота_данных'] == "🟠 ТОЛЬКО CSV"]
        if len(csv_only) > 0:
            csv_only.to_excel(writer, sheet_name='🟠_Только_CSV_ИТОГ', index=False)
        
        # 8. ТОП категории по количеству товаров
        top_categories = df_unified.nlargest(50, 'Товаров')[summary_columns]
        top_categories.to_excel(writer, sheet_name='🏆_ТОП_50_категорий', index=False)
        
        # 9. Полная таблица с диапазонами
        df_unified.to_excel(writer, sheet_name='📋_Полная_итоговая', index=False)
    
    print(f"✅ Финальный отчет создан: {output_file}")
    print()
    print("📊 ИТОГОВАЯ СТАТИСТИКА ПОЛНОТЫ:")
    for _, row in completeness_stats.iterrows():
        print(f"  {row['Полнота_данных']}: {row['Количество_категорий']} категорий, {row['Всего_товаров']:,.0f} товаров")
    
    print()
    print("🔄 ИЗМЕНЕНИЯ ПОСЛЕ УМНОГО ПОИСКА:")
    for col in ['Всего_категорий', 'Всего_товаров', 'Полных_данных', 'БД_плюс_CSV', 'Только_CSV']:
        change = comparison_stats.loc[2, col]
        if col == 'Всего_товаров':
            print(f"  {col}: {change:+,}")
        else:
            print(f"  {col}: {change:+}")
    
    # Создаем CSV версии ключевых листов
    df_summary.to_csv('FINAL_UNIFIED_SUMMARY.csv', index=False, encoding='utf-8')
    completeness_stats.to_csv('FINAL_COMPLETENESS_STATS.csv', index=False, encoding='utf-8')
    comparison_stats.to_csv('BEFORE_AFTER_COMPARISON.csv', index=False, encoding='utf-8')
    
    print()
    print("📄 CSV ФАЙЛЫ:")
    print("  • FINAL_UNIFIED_SUMMARY.csv - итоговая сводка")
    print("  • FINAL_COMPLETENESS_STATS.csv - финальная статистика")
    print("  • BEFORE_AFTER_COMPARISON.csv - сравнение до/после")
    
    return df_unified

if __name__ == "__main__":
    create_final_unified_report()
