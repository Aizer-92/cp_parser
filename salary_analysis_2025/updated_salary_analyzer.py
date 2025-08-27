#!/usr/bin/env python3
"""
Обновленный анализатор зарплат с учетом столбца "проценты"
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_updated_salaries():
    """Анализирует зарплаты с учетом столбца 'проценты'"""
    
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Обновленный анализ файла: {file_path}")
    
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        print(f"✅ Файл загружен: {df.shape[0]} строк, {df.shape[1]} столбцов")
        print(f"📋 Столбцы: {list(df.columns)}")
        
        # Ищем столбец "проценты"
        percentage_columns = []
        for col in df.columns:
            col_str = str(col).lower()
            if 'процент' in col_str or 'проц' in col_str:
                percentage_columns.append(col)
        
        print(f"\n🔍 Найденные столбцы с процентами: {percentage_columns}")
        
        # Показываем первые несколько строк для понимания структуры
        print("\n🔍 Первые 10 строк данных:")
        print(df.head(10))
        
        # Анализируем данные Артема Василевского
        print("\n" + "="*60)
        print("АНАЛИЗ ДАННЫХ АРТЕМА ВАСИЛЕВСКОГО")
        print("="*60)
        
        # Ищем строки с данными Артема
        artem_data = df[df.astype(str).apply(lambda x: x.str.contains('Артем|Василевский', case=False, na=False)).any(axis=1)]
        
        if not artem_data.empty:
            print(f"✅ Найдено {len(artem_data)} записей для Артема Василевского")
            
            for idx, row in artem_data.iterrows():
                print(f"\n📋 Запись #{idx}:")
                
                # Извлекаем все данные
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                        print(f"   {col}: {value}")
                
                # Ищем базовую зарплату (столбец Unnamed: 7)
                base_salary = row.get('Unnamed: 7', 0)
                if base_salary and base_salary > 0:
                    print(f"\n   💰 Базовая зарплата: {base_salary:,.2f} руб.")
                    
                    # Ищем проценты в разных столбцах
                    percentages_found = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if 'процент' in col_str or 'проц' in col_str:
                            percent_value = row.get(col, 0)
                            if pd.notna(percent_value) and percent_value != 0:
                                percentages_found.append((col, percent_value))
                    
                    if percentages_found:
                        print(f"   📊 Найденные проценты:")
                        for col, value in percentages_found:
                            print(f"      {col}: {value}")
                        
                        # Расчет дополнительных выплат
                        total_percentage = sum([val for _, val in percentages_found if isinstance(val, (int, float))])
                        additional_payment = base_salary * (total_percentage / 100) if total_percentage > 0 else 0
                        
                        print(f"   ➕ Общий процент: {total_percentage}%")
                        print(f"   💰 Дополнительная выплата: {additional_payment:,.2f} руб.")
                        print(f"   🎯 Общая месячная зарплата: {base_salary + additional_payment:,.2f} руб.")
                        print(f"   📅 Годовая зарплата: {(base_salary + additional_payment) * 12:,.2f} руб.")
        
        # Поиск данных Евгения Косицина
        print("\n" + "="*60)
        print("АНАЛИЗ ДАННЫХ ЕВГЕНИЯ КОСИЦИНА")
        print("="*60)
        
        # Ищем строки с данными Евгения
        eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косицин|Косицын', case=False, na=False)).any(axis=1)]
        
        if not eugene_data.empty:
            print(f"✅ Найдено {len(eugene_data)} записей для Евгения Косицина")
            
            for idx, row in eugene_data.iterrows():
                print(f"\n📋 Запись #{idx}:")
                
                # Извлекаем все данные
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                        print(f"   {col}: {value}")
                
                # Ищем базовую зарплату
                base_salary = row.get('Unnamed: 7', 0)
                if base_salary and base_salary > 0:
                    print(f"\n   💰 Базовая зарплата: {base_salary:,.2f} руб.")
                    
                    # Ищем проценты
                    percentages_found = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if 'процент' in col_str or 'проц' in col_str:
                            percent_value = row.get(col, 0)
                            if pd.notna(percent_value) and percent_value != 0:
                                percentages_found.append((col, percent_value))
                    
                    if percentages_found:
                        print(f"   📊 Найденные проценты:")
                        for col, value in percentages_found:
                            print(f"      {col}: {value}")
                        
                        # Расчет дополнительных выплат
                        total_percentage = sum([val for _, val in percentages_found if isinstance(val, (int, float))])
                        additional_payment = base_salary * (total_percentage / 100) if total_percentage > 0 else 0
                        
                        print(f"   ➕ Общий процент: {total_percentage}%")
                        print(f"   💰 Дополнительная выплата: {additional_payment:,.2f} руб.")
                        print(f"   🎯 Общая месячная зарплата: {base_salary + additional_payment:,.2f} руб.")
                        print(f"   📅 Годовая зарплата: {(base_salary + additional_payment) * 12:,.2f} руб.")
        
        # Сохраняем обновленный отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"updated_salary_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ОБНОВЛЕННЫЙ ОТЧЕТ ПО АНАЛИЗУ ЗАРПЛАТ\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n")
            f.write(f"Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов\n\n")
            
            f.write("СТРУКТУРА ДАННЫХ:\n")
            f.write("-" * 30 + "\n")
            for i, col in enumerate(df.columns):
                f.write(f"{i+1}. {col} (тип: {df[col].dtype})\n")
            
            f.write(f"\nСТОЛБЦЫ С ПРОЦЕНТАМИ:\n")
            f.write("-" * 30 + "\n")
            for col in percentage_columns:
                f.write(f"- {col}\n")
            
            f.write(f"\nПЕРВЫЕ 10 СТРОК ДАННЫХ:\n")
            f.write("-" * 30 + "\n")
            f.write(df.head(10).to_string())
        
        print(f"\n📄 Обновленный отчет сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск обновленного анализатора зарплат")
    print("=" * 60)
    analyze_updated_salaries()
    print("\n✅ Обновленный анализ завершен!")
