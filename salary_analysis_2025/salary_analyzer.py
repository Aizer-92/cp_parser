#!/usr/bin/env python3
"""
Анализатор зарплат для Артема Василевского и Евгения Косицина
Анализирует данные из таблицы выплат 2025 года
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_salaries():
    """Анализирует зарплаты указанных сотрудников"""
    
    # Путь к файлу
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Анализирую файл: {file_path}")
    
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        print(f"✅ Файл успешно загружен")
        print(f"📋 Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов")
        print(f"📋 Столбцы: {list(df.columns)}")
        
        # Показываем первые несколько строк для понимания структуры
        print("\n🔍 Первые 5 строк данных:")
        print(df.head())
        
        # Ищем столбцы с именами сотрудников (безопасно обрабатываем разные типы данных)
        name_columns = []
        for col in df.columns:
            col_str = str(col).lower()
            if 'имя' in col_str or 'name' in col_str or 'сотрудник' in col_str:
                name_columns.append(col)
        
        print(f"\n👥 Найденные столбцы с именами: {name_columns}")
        
        # Ищем столбцы с зарплатами
        salary_columns = []
        for col in df.columns:
            col_str = str(col).lower()
            if 'зарплат' in col_str or 'salary' in col_str or 'выплат' in col_str or 'сумма' in col_str:
                salary_columns.append(col)
        
        print(f"💰 Найденные столбцы с зарплатами: {salary_columns}")
        
        # Ищем данные по конкретным сотрудникам
        target_names = ['Артем Василевский', 'Евгений Косицин', 'Василевский', 'Косицин']
        
        results = {}
        
        for name in target_names:
            print(f"\n🔍 Ищем данные для: {name}")
            
            # Ищем в разных столбцах
            for col in df.columns:
                if df[col].dtype == 'object':  # Текстовые столбцы
                    matches = df[df[col].astype(str).str.contains(name, case=False, na=False)]
                    if not matches.empty:
                        print(f"   ✅ Найдено в столбце '{col}': {len(matches)} записей")
                        
                        # Показываем найденные записи
                        print(f"   📋 Найденные записи:")
                        for idx, row in matches.iterrows():
                            print(f"      Строка {idx}: {dict(row)}")
        
        # Альтернативный подход - поиск по всем данным
        print(f"\n🔍 Поиск по всем данным...")
        
        # Преобразуем все данные в строки для поиска
        df_str = df.astype(str)
        
        for name in target_names:
            print(f"\n🔍 Поиск '{name}' во всех данных:")
            
            # Ищем строки, содержащие имя
            mask = df_str.apply(lambda x: x.str.contains(name, case=False, na=False)).any(axis=1)
            matching_rows = df[mask]
            
            if not matching_rows.empty:
                print(f"   ✅ Найдено {len(matching_rows)} строк с '{name}':")
                for idx, row in matching_rows.iterrows():
                    print(f"      Строка {idx}:")
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            print(f"         {col}: {value}")
            else:
                print(f"   ❌ Данные для '{name}' не найдены")
        
        # Показываем все уникальные значения в первом столбце (часто там имена)
        print(f"\n🔍 Анализ первого столбца (Unnamed: 0):")
        unique_values = df['Unnamed: 0'].dropna().unique()
        print(f"   Уникальные значения: {list(unique_values)}")
        
        # Показываем все уникальные значения во втором столбце
        print(f"\n🔍 Анализ второго столбца (Unnamed: 1):")
        unique_values_2 = df['Unnamed: 1'].dropna().unique()
        print(f"   Уникальные значения: {list(unique_values_2)}")
        
        # Сохраняем результаты анализа
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"salary_analysis_report_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ ПО АНАЛИЗУ ЗАРПЛАТ\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n")
            f.write(f"Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов\n\n")
            
            f.write("СТРУКТУРА ДАННЫХ:\n")
            f.write("-" * 30 + "\n")
            for i, col in enumerate(df.columns):
                f.write(f"{i+1}. {col} (тип: {df[col].dtype})\n")
            
            f.write(f"\nПЕРВЫЕ 10 СТРОК ДАННЫХ:\n")
            f.write("-" * 30 + "\n")
            f.write(df.head(10).to_string())
            
            f.write(f"\n\nУНИКАЛЬНЫЕ ЗНАЧЕНИЯ В ПЕРВОМ СТОЛБЦЕ:\n")
            f.write("-" * 30 + "\n")
            for val in unique_values:
                f.write(f"- {val}\n")
            
            f.write(f"\nУНИКАЛЬНЫЕ ЗНАЧЕНИЯ ВО ВТОРОМ СТОЛБЦЕ:\n")
            f.write("-" * 30 + "\n")
            for val in unique_values_2:
                f.write(f"- {val}\n")
        
        print(f"\n📄 Отчет сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе файла: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск анализатора зарплат")
    print("=" * 50)
    analyze_salaries()
    print("\n✅ Анализ завершен!")
