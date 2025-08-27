#!/usr/bin/env python3
"""
Исправленный анализатор зарплат с правильной интерпретацией процентов
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_corrected_salaries():
    """Анализирует зарплаты с правильной интерпретацией данных"""
    
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Исправленный анализ файла: {file_path}")
    
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        print(f"✅ Файл загружен: {df.shape[0]} строк, {df.shape[1]} столбцов")
        
        # Анализируем данные Артема Василевского
        print("\n" + "="*60)
        print("АНАЛИЗ ДАННЫХ АРТЕМА ВАСИЛЕВСКОГО")
        print("="*60)
        
        # Ищем строки с данными Артема
        artem_data = df[df.astype(str).apply(lambda x: x.str.contains('Артем|Василевский', case=False, na=False)).any(axis=1)]
        
        if not artem_data.empty:
            print(f"✅ Найдено {len(artem_data)} записей для Артема Василевского")
            
            for idx, row in artem_data.iterrows():
                name = row.get('Unnamed: 6', '')
                if 'Артем' in str(name):
                    print(f"\n📋 Запись #{idx} - АРТЕМ ВАСИЛЕВСКИЙ:")
                    
                    # Извлекаем ключевые данные
                    position = row.get('Unnamed: 5', 'Руководитель отдела по работе с Китаем')
                    base_salary = row.get('Unnamed: 7', 0)
                    date_column = row.get(datetime(2019, 8, 23, 0, 0), 0)  # Столбец с датой может содержать проценты
                    additional = row.get('Unnamed: 10', 0)
                    ss_amount = row.get('СС', 0)
                    final_amount = row.get('Unnamed: 22', 0)
                    
                    print(f"   👤 Имя: {name}")
                    print(f"   💼 Должность: {position}")
                    print(f"   💰 Базовая зарплата: {base_salary:,.2f} руб.")
                    print(f"   📅 Значение в столбце даты: {date_column}")
                    print(f"   ➕ Дополнительные выплаты (Unnamed: 10): {additional:,.2f} руб.")
                    print(f"   📊 СС: {ss_amount:,.2f} руб.")
                    print(f"   🎯 Итоговая сумма: {final_amount:,.2f} руб.")
                    
                    # Интерпретируем данные
                    if isinstance(date_column, (int, float)) and date_column > 0:
                        # Если в столбце даты число, это может быть процент
                        percentage = date_column
                        additional_by_percentage = base_salary * (percentage / 100)
                        print(f"   📊 Процент из столбца даты: {percentage}%")
                        print(f"   💰 Доплата по проценту: {additional_by_percentage:,.2f} руб.")
                        
                        # Общая месячная зарплата
                        total_monthly = base_salary + additional_by_percentage + additional
                        total_annual = total_monthly * 12
                        
                        print(f"\n   📈 РАСЧЕТЫ:")
                        print(f"      💵 Базовая зарплата: {base_salary:,.2f} руб.")
                        print(f"      📊 Доплата по проценту: {additional_by_percentage:,.2f} руб.")
                        print(f"      ➕ Дополнительные выплаты: {additional:,.2f} руб.")
                        print(f"      💰 Общая месячная зарплата: {total_monthly:,.2f} руб.")
                        print(f"      🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {total_annual:,.2f} руб.")
                    else:
                        # Если нет процента в столбце даты, используем только дополнительные выплаты
                        total_monthly = base_salary + additional
                        total_annual = total_monthly * 12
                        
                        print(f"\n   📈 РАСЧЕТЫ:")
                        print(f"      💵 Базовая зарплата: {base_salary:,.2f} руб.")
                        print(f"      ➕ Дополнительные выплаты: {additional:,.2f} руб.")
                        print(f"      💰 Общая месячная зарплата: {total_monthly:,.2f} руб.")
                        print(f"      🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {total_annual:,.2f} руб.")
        
        # Поиск данных Евгения Косицина
        print("\n" + "="*60)
        print("АНАЛИЗ ДАННЫХ ЕВГЕНИЯ КОСИЦИНА")
        print("="*60)
        
        # Ищем строки с данными Евгения
        eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косицин|Косицын', case=False, na=False)).any(axis=1)]
        
        if not eugene_data.empty:
            print(f"✅ Найдено {len(eugene_data)} записей для Евгения Косицина")
            
            for idx, row in eugene_data.iterrows():
                name = row.get('Unnamed: 6', '')
                if 'Евгений' in str(name) or 'Косиц' in str(name):
                    print(f"\n📋 Запись #{idx} - ЕВГЕНИЙ КОСИЦИН:")
                    
                    # Извлекаем ключевые данные
                    position = row.get('Unnamed: 5', 'Руководитель отдела по работе с Китаем')
                    base_salary = row.get('Unnamed: 7', 0)
                    date_column = row.get(datetime(2019, 8, 23, 0, 0), 0)
                    additional = row.get('Unnamed: 10', 0)
                    ss_amount = row.get('СС', 0)
                    final_amount = row.get('Unnamed: 22', 0)
                    
                    print(f"   👤 Имя: {name}")
                    print(f"   💼 Должность: {position}")
                    print(f"   💰 Базовая зарплата: {base_salary:,.2f} руб.")
                    print(f"   📅 Значение в столбце даты: {date_column}")
                    print(f"   ➕ Дополнительные выплаты (Unnamed: 10): {additional:,.2f} руб.")
                    print(f"   📊 СС: {ss_amount:,.2f} руб.")
                    print(f"   🎯 Итоговая сумма: {final_amount:,.2f} руб.")
                    
                    # Интерпретируем данные
                    if isinstance(date_column, (int, float)) and date_column > 0:
                        # Если в столбце даты число, это может быть процент
                        percentage = date_column
                        additional_by_percentage = base_salary * (percentage / 100)
                        print(f"   📊 Процент из столбца даты: {percentage}%")
                        print(f"   💰 Доплата по проценту: {additional_by_percentage:,.2f} руб.")
                        
                        # Общая месячная зарплата
                        total_monthly = base_salary + additional_by_percentage + additional
                        total_annual = total_monthly * 12
                        
                        print(f"\n   📈 РАСЧЕТЫ:")
                        print(f"      💵 Базовая зарплата: {base_salary:,.2f} руб.")
                        print(f"      📊 Доплата по проценту: {additional_by_percentage:,.2f} руб.")
                        print(f"      ➕ Дополнительные выплаты: {additional:,.2f} руб.")
                        print(f"      💰 Общая месячная зарплата: {total_monthly:,.2f} руб.")
                        print(f"      🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {total_annual:,.2f} руб.")
                    else:
                        # Если нет процента в столбце даты, используем только дополнительные выплаты
                        total_monthly = base_salary + additional
                        total_annual = total_monthly * 12
                        
                        print(f"\n   📈 РАСЧЕТЫ:")
                        print(f"      💵 Базовая зарплата: {base_salary:,.2f} руб.")
                        print(f"      ➕ Дополнительные выплаты: {additional:,.2f} руб.")
                        print(f"      💰 Общая месячная зарплата: {total_monthly:,.2f} руб.")
                        print(f"      🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {total_annual:,.2f} руб.")
        
        # Сохраняем исправленный отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"corrected_salary_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ИСПРАВЛЕННЫЙ ОТЧЕТ ПО АНАЛИЗУ ЗАРПЛАТ\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n")
            f.write("Примечание: Проценты могут находиться в столбце с датой 2019-08-23\n\n")
            
            f.write("СТРУКТУРА ДАННЫХ:\n")
            f.write("-" * 30 + "\n")
            for i, col in enumerate(df.columns):
                f.write(f"{i+1}. {col} (тип: {df[col].dtype})\n")
        
        print(f"\n📄 Исправленный отчет сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск исправленного анализатора зарплат")
    print("=" * 60)
    analyze_corrected_salaries()
    print("\n✅ Исправленный анализ завершен!")
