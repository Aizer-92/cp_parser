#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СОЗДАНИЕ EXCEL ОТЧЕТА С ГАУССОВСКИМИ ДИАПАЗОНАМИ ПО КАТЕГОРИЯМ
"""

import pandas as pd
import numpy as np
from pathlib import Path
from business_final_analyzer import BusinessFinalAnalyzer

def format_gaussian_range(ranges, field, format_type='currency'):
    """Форматирование гауссовского диапазона"""
    if field not in ranges:
        return 'Недостаточно данных'
    
    r = ranges[field]
    
    if format_type == 'currency_rub':
        return f"{r['lower_70']:.0f} - {r['upper_70']:.0f} ₽"
    elif format_type == 'currency_cny':
        return f"{r['lower_70']:.1f} - {r['upper_70']:.1f} ¥"
    elif format_type == 'currency_usd':
        return f"${r['lower_70']:.1f} - ${r['upper_70']:.1f}"
    elif format_type == 'number':
        return f"{r['lower_70']:.0f} - {r['upper_70']:.0f}"
    elif format_type == 'density':
        return f"{r['lower_70']:.1f} - {r['upper_70']:.1f}"
    else:
        return f"{r['lower_70']:.1f} - {r['upper_70']:.1f}"

def create_business_excel_report():
    """Создание Excel отчета для бизнеса"""
    
    print("🎯 СОЗДАНИЕ БИЗНЕС-EXCEL С РЕАЛЬНЫМИ 70% ДИАПАЗОНАМИ")
    print("=" * 60)
    
    # Запуск анализа
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    analyzer = BusinessFinalAnalyzer(db_path)
    
    try:
        stats, coverage, excluded_count, total_products = analyzer.run_business_analysis()
        
        # Подготовка данных для Excel
        categories_data = []
        gaussian_details = []
        
        for stat in stats:
            type_label = "Основная" if stat['тип'] == 'main' else "Подкатегория"
            category_display = stat['категория'] if stat['тип'] == 'main' else f"└─ {stat['категория']}"
            
            # Основная таблица категорий
            categories_data.append({
                'Тип': type_label,
                'Категория': category_display,
                'Родитель': stat['родитель'] if stat['тип'] == 'sub' else '',
                'Товаров': stat['товары'],
                'Медиана цены (₽)': f"{stat['медиана_цены_rub']:.0f}" if stat['медиана_цены_rub'] else 'н/д',
                'Медиана цены (¥)': f"{stat['медиана_цены_cny']:.1f}" if stat['медиана_цены_cny'] else 'н/д',
                'Средний тираж': f"{stat['средний_тираж']:.0f}" if stat['средний_тираж'] else 'н/д',
                'Плотность (кг/м³)': f"{stat['медиана_плотности']:.1f}" if stat['медиана_плотности'] else 'н/д',
                'Транспорт ($/кг)': f"${stat['медиана_транспорта_usd']:.1f}" if stat['медиана_транспорта_usd'] else 'н/д',
                
                # Реальные 70% диапазоны товаров
                'Диапазон цен (₽)': format_gaussian_range(stat['gaussian_ranges'], 'price_rub', 'currency_rub'),
                'Диапазон цен (¥)': format_gaussian_range(stat['gaussian_ranges'], 'price_cny', 'currency_cny'),
                'Диапазон тиражей': format_gaussian_range(stat['gaussian_ranges'], 'avg_requested_tirage', 'number'),
                'Диапазон плотности': format_gaussian_range(stat['gaussian_ranges'], 'cargo_density', 'density'),
                'Диапазон транспорта': format_gaussian_range(stat['gaussian_ranges'], 'transport_tariff', 'currency_usd'),
            })
            
            # Детальные гауссовские диапазоны
            if stat['gaussian_ranges']:
                for field, ranges in stat['gaussian_ranges'].items():
                    gaussian_details.append({
                        'Категория': stat['категория'],
                        'Тип категории': type_label,
                        'Метрика': ranges['label'],
                        'Количество данных': ranges['count'],
                        'Среднее': f"{ranges['mean']:.2f}",
                        'Ст. отклонение': f"{ranges['std']:.2f}",
                        'Медиана': f"{ranges['median']:.2f}",
                        'Минимум': f"{ranges['min']:.2f}",
                        'Максимум': f"{ranges['max']:.2f}",
                        '70% диапазон (от)': f"{ranges['lower_70']:.2f}",
                        '70% диапазон (до)': f"{ranges['upper_70']:.2f}",
                        'Диапазон': f"{ranges['lower_70']:.1f} - {ranges['upper_70']:.1f}"
                    })
        
        # Создание DataFrame
        df_categories = pd.DataFrame(categories_data)
        df_gaussian = pd.DataFrame(gaussian_details)
        
        # Топ категории
        main_categories = [stat for stat in stats if stat['тип'] == 'main']
        top_categories = sorted(main_categories, key=lambda x: x['товары'], reverse=True)[:20]
        
        top_data = []
        for i, stat in enumerate(top_categories, 1):
            top_data.append({
                'Место': i,
                'Категория': stat['категория'],
                'Товаров': stat['товары'],
                '% от БД': f"{(stat['товары'] / (total_products - excluded_count) * 100):.1f}%",
                'Цена (₽)': f"{stat['медиана_цены_rub']:.0f}" if stat['медиана_цены_rub'] else 'н/д',
                'Тираж': f"{stat['средний_тираж']:.0f}" if stat['средний_тираж'] else 'н/д',
                'Гауссовский диапазон цен (₽)': format_gaussian_range(stat['gaussian_ranges'], 'price_rub', 'currency_rub'),
                'Гауссовский диапазон тиражей': format_gaussian_range(stat['gaussian_ranges'], 'avg_requested_tirage', 'number'),
            })
        
        df_top = pd.DataFrame(top_data)
        
        # Статистика
        total_main_categories = len([s for s in stats if s['тип'] == 'main'])
        total_subcategories = len([s for s in stats if s['тип'] == 'sub'])
        
        summary_data = [
            ['БИЗНЕС-АНАЛИЗ ТОВАРНЫХ КАТЕГОРИЙ', '', ''],
            ['Дата анализа', '23 сентября 2025', ''],
            ['', '', ''],
            ['ПОКРЫТИЕ ТОВАРОВ', '', ''],
            ['Всего товаров в БД', f'{total_products:,}', '100%'],
            ['Исключено служебных', f'{excluded_count:,}', 'образцы, лого'],
            ['Проанализировано', f'{total_products - excluded_count:,}', 'основная база'],
            ['Категоризировано', f'{sum(s["товары"] for s in stats):,}', f'{coverage:.1f}%'],
            ['', '', ''],
            ['СТРУКТУРА КАТЕГОРИЙ', '', ''],
            ['Основных категорий', f'{total_main_categories}', 'главные группы'],
            ['Подкатегорий', f'{total_subcategories}', 'детализация ≥20 товаров'],
            ['Всего категорий', f'{total_main_categories + total_subcategories}', 'полная структура'],
            ['', '', ''],
            ['РЕАЛЬНЫЕ 70% ДИАПАЗОНЫ', '', ''],
            ['Принцип расчета', '70% товаров', '15-85 процентили'],
            ['Охват категорий', f'{len([s for s in stats if s["gaussian_ranges"]])}', 'с достаточными данными'],
            ['Применение', 'Прогнозирование', 'планирование закупок'],
            ['', '', ''],
            ['ТОП-3 КАТЕГОРИИ', '', ''],
            ['№1 по объему', top_data[0]['Категория'] if top_data else 'н/д', f"{top_data[0]['Товаров']} товаров" if top_data else ''],
            ['№2 по объему', top_data[1]['Категория'] if len(top_data) > 1 else 'н/д', f"{top_data[1]['Товаров']} товаров" if len(top_data) > 1 else ''],
            ['№3 по объему', top_data[2]['Категория'] if len(top_data) > 2 else 'н/д', f"{top_data[2]['Товаров']} товаров" if len(top_data) > 2 else ''],
        ]
        
        df_summary = pd.DataFrame(summary_data, columns=['Показатель', 'Значение', 'Примечание'])
        
        # Сохранение в Excel
        output_file = Path(__file__).parent / 'BUSINESS_ANALYSIS_WITH_GAUSSIAN.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Лист 1: Все категории с гауссовскими диапазонами
            df_categories.to_excel(writer, sheet_name='Категории с диапазонами', index=False)
            
            # Лист 2: Топ-20 категорий
            df_top.to_excel(writer, sheet_name='ТОП-20 категорий', index=False)
            
            # Лист 3: Детальные гауссовские диапазоны
            df_gaussian.to_excel(writer, sheet_name='Детальные диапазоны', index=False)
            
            # Лист 4: Сводка
            df_summary.to_excel(writer, sheet_name='Сводка анализа', index=False)
        
        print(f"✅ Бизнес-Excel создан: {output_file}")
        print(f"📊 Листы:")
        print(f"  1. 'Категории с диапазонами' - {len(df_categories)} категорий")
        print(f"  2. 'ТОП-20 категорий' - лидеры с диапазонами")
        print(f"  3. 'Детальные диапазоны' - {len(df_gaussian)} гауссовских распределений")
        print(f"  4. 'Сводка анализа' - общие показатели")
        print(f"")
        print(f"🎯 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:")
        print(f"  • Реальные 70% товаров для каждой категории отдельно")
        print(f"  • 15-85 процентили для точного планирования")
        print(f"  • Иерархическая структура категорий")
        print(f"  • Медианы для устойчивости к выбросам")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analyzer.conn.close()

if __name__ == "__main__":
    create_business_excel_report()
