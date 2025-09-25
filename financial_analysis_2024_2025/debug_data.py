#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка структуры данных
"""

import pandas as pd
import numpy as np

def debug_data():
    file_path = "/Users/bakirovresad/Downloads/Reshad 1/Отчет счета май-сентябрь 2025 (1).xlsx"
    
    # Загружаем данные 2024
    df_2024 = pd.read_excel(file_path, sheet_name='2024')
    print("=== ДАННЫЕ 2024 ===")
    print(f"Размер: {df_2024.shape}")
    print(f"Колонки: {list(df_2024.columns)}")
    print(f"Первые 10 строк:")
    print(df_2024.head(10))
    print(f"\nТипы данных:")
    print(df_2024.dtypes)
    print(f"\nПропущенные значения:")
    print(df_2024.isnull().sum())
    
    # Проверяем колонку Сумма
    print(f"\nУникальные значения в колонке 'Сумма' (первые 20):")
    print(df_2024['Сумма'].value_counts().head(20))
    
    # Проверяем колонку Дата и время
    print(f"\nУникальные значения в колонке 'Дата и время' (первые 20):")
    print(df_2024['Дата и время'].value_counts().head(20))
    
    print("\n" + "="*50)
    
    # Загружаем данные 2025
    df_2025 = pd.read_excel(file_path, sheet_name='2025')
    print("=== ДАННЫЕ 2025 ===")
    print(f"Размер: {df_2025.shape}")
    print(f"Колонки: {list(df_2025.columns)}")
    print(f"Первые 10 строк:")
    print(df_2025.head(10))
    print(f"\nТипы данных:")
    print(df_2025.dtypes)
    print(f"\nПропущенные значения:")
    print(df_2025.isnull().sum())
    
    # Проверяем колонку Сумма
    print(f"\nУникальные значения в колонке 'Сумма' (первые 20):")
    print(df_2025['Сумма'].value_counts().head(20))
    
    # Проверяем колонку Дата и время
    print(f"\nУникальные значения в колонке 'Дата и время' (первые 20):")
    print(df_2025['Дата и время'].value_counts().head(20))

if __name__ == "__main__":
    debug_data()
