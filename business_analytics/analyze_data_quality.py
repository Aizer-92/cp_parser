#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ качества данных - проверка нулевых и пустых значений
"""

import sqlite3
import pandas as pd
from pathlib import Path

def analyze_data_quality():
    """Анализ качества данных в БД"""
    
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    conn = sqlite3.connect(db_path)
    
    # Загружаем данные для категории "сумка"
    query = """
    SELECT 
        p.original_title,
        pv.cargo_density,
        pv.item_weight,
        pv.transport_tariff,
        pv.price_rub,
        pv.price_cny,
        pv.moq,
        pv.avg_requested_tirage
    FROM products p
    JOIN product_variants pv ON p.id = pv.product_id
    WHERE p.original_title LIKE '%сумка%' OR p.title LIKE '%сумка%'
    """
    
    df = pd.read_sql_query(query, conn)
    
    print("🔍 АНАЛИЗ КАЧЕСТВА ДАННЫХ ПО КАТЕГОРИИ 'СУМКА'")
    print("=" * 60)
    print(f"Всего записей: {len(df)}")
    print()
    
    # Анализ каждой метрики
    metrics = {
        'cargo_density': 'Плотность (кг/м³)',
        'item_weight': 'Вес товара (кг)',
        'transport_tariff': 'Транспорт ($/кг)',
        'price_rub': 'Цена (₽)',
        'price_cny': 'Цена (¥)',
        'moq': 'MOQ'
    }
    
    print("📊 КАЧЕСТВО ДАННЫХ ПО МЕТРИКАМ:")
    print("-" * 60)
    
    for col, label in metrics.items():
        print(f"{label}:")
        
        total = len(df)
        na_count = df[col].isna().sum()
        zero_count = (df[col] == 0).sum()
        valid_count = ((df[col] > 0) & df[col].notna()).sum()
        
        print(f"  📋 Всего: {total}")
        print(f"  ❓ Пустых (NaN): {na_count} ({na_count/total*100:.1f}%)")
        print(f"  🚫 Нулевых: {zero_count} ({zero_count/total*100:.1f}%)")
        print(f"  ✅ Валидных (>0): {valid_count} ({valid_count/total*100:.1f}%)")
        
        if valid_count > 0:
            valid_data = df[col][(df[col] > 0) & df[col].notna()]
            print(f"  📈 Статистика валидных:")
            print(f"     Мин: {valid_data.min():.3f}")
            print(f"     Макс: {valid_data.max():.3f}")
            print(f"     Медиана: {valid_data.median():.3f}")
            print(f"     15-й процентиль: {valid_data.quantile(0.15):.3f}")
            print(f"     85-й процентиль: {valid_data.quantile(0.85):.3f}")
        
        print()
    
    # Проверим конкретно проблемные записи с плотностью
    print("🚨 ПРОБЛЕМНЫЕ ЗАПИСИ С НИЗКОЙ ПЛОТНОСТЬЮ:")
    print("-" * 60)
    
    density_issues = df[(df['cargo_density'] > 0) & (df['cargo_density'] < 1)]
    if len(density_issues) > 0:
        print(f"Найдено {len(density_issues)} записей с плотностью < 1 кг/м³:")
        for idx, row in density_issues.head(5).iterrows():
            print(f"  • {row['original_title'][:50]}... плотность: {row['cargo_density']:.3f}")
    else:
        print("Проблемных записей не найдено")
    
    print()
    
    # Рекомендации
    print("💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
    print("-" * 60)
    print("1. Исключить из анализа записи с NaN значениями")
    print("2. Исключить из анализа записи с нулевыми значениями")
    print("3. Для плотности: исключить записи < 0.1 кг/м³ (нереальные)")
    print("4. Анализировать только валидные данные для каждой метрики отдельно")
    
    conn.close()
    
    return df

if __name__ == "__main__":
    analyze_data_quality()
