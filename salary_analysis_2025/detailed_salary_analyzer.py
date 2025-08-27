#!/usr/bin/env python3
"""
Детальный анализатор зарплат для расчета среднегодовых показателей
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_detailed_salaries():
    """Детальный анализ зарплат с расчетом среднегодовых показателей"""
    
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Детальный анализ файла: {file_path}")
    
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
                print(f"\n📋 Запись #{idx}:")
                
                # Извлекаем ключевые данные
                name = row.get('Unnamed: 6', 'Артем')
                position = row.get('Unnamed: 5', 'Руководитель отдела по работе с Китаем')
                base_salary = row.get('Unnamed: 7', 0)
                ss_amount = row.get('СС', 0)
                additional = row.get('Unnamed: 10', 0)
                total_ss = row.get('Unnamed: 13', 0)
                final_amount = row.get('Unnamed: 22', 0)
                
                print(f"   👤 Имя: {name}")
                print(f"   💼 Должность: {position}")
                print(f"   💰 Базовая зарплата: {base_salary:,.2f} руб.")
                print(f"   📊 СС: {ss_amount:,.2f} руб.")
                print(f"   ➕ Дополнительно: {additional:,.2f} руб.")
                print(f"   📈 Общая СС: {total_ss:,.2f} руб.")
                print(f"   🎯 Итоговая сумма: {final_amount:,.2f} руб.")
                
                # Расчеты
                if base_salary and base_salary > 0:
                    monthly_salary = base_salary
                    annual_salary = monthly_salary * 12
                    
                    print(f"\n   📊 РАСЧЕТЫ:")
                    print(f"      💵 Месячная зарплата: {monthly_salary:,.2f} руб.")
                    print(f"      📅 Годовая зарплата: {annual_salary:,.2f} руб.")
                    
                    # Если есть дополнительные выплаты
                    if additional and additional > 0:
                        total_monthly = monthly_salary + additional
                        total_annual = total_monthly * 12
                        print(f"      💰 Месячная с доплатами: {total_monthly:,.2f} руб.")
                        print(f"      📅 Годовая с доплатами: {total_annual:,.2f} руб.")
        
        # Поиск данных Евгения Косицина
        print("\n" + "="*60)
        print("ПОИСК ДАННЫХ ЕВГЕНИЯ КОСИЦИНА")
        print("="*60)
        
        # Ищем строки с данными Евгения
        eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косицин|Косицын', case=False, na=False)).any(axis=1)]
        
        if not eugene_data.empty:
            print(f"✅ Найдено {len(eugene_data)} записей для Евгения Косицина")
            
            for idx, row in eugene_data.iterrows():
                print(f"\n📋 Запись #{idx}:")
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        print(f"   {col}: {value}")
        else:
            print("❌ Данные для Евгения Косицина не найдены")
            
            # Попробуем найти похожие имена
            print("\n🔍 Поиск похожих имен...")
            all_text = df.astype(str).values.flatten()
            
            for text in all_text:
                if 'евг' in text.lower() or 'косиц' in text.lower():
                    print(f"   Возможное совпадение: {text}")
        
        # Анализ всех сотрудников
        print("\n" + "="*60)
        print("АНАЛИЗ ВСЕХ СОТРУДНИКОВ")
        print("="*60)
        
        # Ищем строки с зарплатами (столбец Unnamed: 7)
        salary_data = df[df['Unnamed: 7'].notna() & (df['Unnamed: 7'] > 0)]
        
        if not salary_data.empty:
            print(f"✅ Найдено {len(salary_data)} записей с зарплатами")
            
            for idx, row in salary_data.iterrows():
                name = row.get('Unnamed: 6', 'Неизвестно')
                position = row.get('Unnamed: 5', 'Не указано')
                salary = row.get('Unnamed: 7', 0)
                
                if name and name != 'nan':
                    print(f"\n👤 {name}")
                    print(f"   💼 {position}")
                    print(f"   💰 Зарплата: {salary:,.2f} руб.")
                    print(f"   📅 Годовая: {salary * 12:,.2f} руб.")
        
        # Сохраняем детальный отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"detailed_salary_report_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ДЕТАЛЬНЫЙ ОТЧЕТ ПО АНАЛИЗУ ЗАРПЛАТ\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n\n")
            
            # Данные Артема
            f.write("ДАННЫЕ АРТЕМА ВАСИЛЕВСКОГО:\n")
            f.write("-" * 40 + "\n")
            if not artem_data.empty:
                for idx, row in artem_data.iterrows():
                    f.write(f"Запись #{idx}:\n")
                    f.write(f"  Имя: {row.get('Unnamed: 6', 'Артем')}\n")
                    f.write(f"  Должность: {row.get('Unnamed: 5', 'Руководитель отдела по работе с Китаем')}\n")
                    f.write(f"  Базовая зарплата: {row.get('Unnamed: 7', 0):,.2f} руб.\n")
                    f.write(f"  СС: {row.get('СС', 0):,.2f} руб.\n")
                    f.write(f"  Дополнительно: {row.get('Unnamed: 10', 0):,.2f} руб.\n")
                    f.write(f"  Общая СС: {row.get('Unnamed: 13', 0):,.2f} руб.\n")
                    f.write(f"  Итоговая сумма: {row.get('Unnamed: 22', 0):,.2f} руб.\n")
                    
                    base_salary = row.get('Unnamed: 7', 0)
                    if base_salary > 0:
                        f.write(f"  Годовая зарплата: {base_salary * 12:,.2f} руб.\n")
            else:
                f.write("Данные не найдены\n")
            
            f.write("\nДАННЫЕ ЕВГЕНИЯ КОСИЦИНА:\n")
            f.write("-" * 40 + "\n")
            if not eugene_data.empty:
                for idx, row in eugene_data.iterrows():
                    f.write(f"Запись #{idx}:\n")
                    for col, value in row.items():
                        if pd.notna(value) and str(value).strip():
                            f.write(f"  {col}: {value}\n")
            else:
                f.write("Данные не найдены\n")
        
        print(f"\n📄 Детальный отчет сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск детального анализатора зарплат")
    print("=" * 60)
    analyze_detailed_salaries()
    print("\n✅ Детальный анализ завершен!")
