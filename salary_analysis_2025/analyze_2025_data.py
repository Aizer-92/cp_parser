#!/usr/bin/env python3
"""
Анализатор зарплат за 2025 год
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_2025_salaries():
    """Анализирует зарплаты за 2025 год"""
    
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Анализ зарплат за 2025 год: {file_path}")
    
    try:
        # Читаем все листы Excel файла
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"✅ Найдено листов: {len(sheet_names)}")
        print(f"📋 Названия листов: {sheet_names}")
        
        # Ищем листы за 2025 год
        sheets_2025 = [sheet for sheet in sheet_names if '2025' in sheet and not 'архив' in sheet.lower()]
        print(f"\n📅 Найденные листы за 2025 год: {sheets_2025}")
        
        # Словарь для хранения данных по сотрудникам за 2025 год
        employees_2025 = {
            'Артем Василевский': {},
            'Евгений Косицин': {}
        }
        
        # Анализируем каждый лист за 2025 год
        for sheet_name in sheets_2025:
            print(f"\n🔍 Анализируем лист: {sheet_name}")
            
            try:
                # Читаем лист
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                print(f"   📊 Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов")
                
                # Ищем данные Артема Василевского
                artem_data = df[df.astype(str).apply(lambda x: x.str.contains('Артем|Василевский', case=False, na=False)).any(axis=1)]
                
                if not artem_data.empty:
                    print(f"   ✅ Найдено {len(artem_data)} записей для Артема")
                    
                    for idx, row in artem_data.iterrows():
                        name = row.get('Unnamed: 6', '')
                        if 'Артем' in str(name):
                            print(f"      📋 Запись #{idx} - АРТЕМ ВАСИЛЕВСКИЙ:")
                            
                            # Ищем зарплату в столбце Unnamed: 7
                            salary = row.get('Unnamed: 7', 0)
                            if salary and salary > 0:
                                print(f"         💰 Зарплата: {salary:,.2f} руб.")
                                
                                # Сохраняем данные
                                if sheet_name not in employees_2025['Артем Василевский']:
                                    employees_2025['Артем Василевский'][sheet_name] = []
                                employees_2025['Артем Василевский'][sheet_name].append(salary)
                            
                            # Ищем дополнительные выплаты в столбце Unnamed: 10
                            additional = row.get('Unnamed: 10', 0)
                            if additional and additional > 0:
                                print(f"         ➕ Дополнительно: {additional:,.2f} руб.")
                                
                                # Сохраняем дополнительные выплаты
                                if f"{sheet_name}_additional" not in employees_2025['Артем Василевский']:
                                    employees_2025['Артем Василевский'][f"{sheet_name}_additional"] = []
                                employees_2025['Артем Василевский'][f"{sheet_name}_additional"].append(additional)
                
                # Ищем данные Евгения Косицина
                eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косицин|Косицын', case=False, na=False)).any(axis=1)]
                
                if not eugene_data.empty:
                    print(f"   ✅ Найдено {len(eugene_data)} записей для Евгения")
                    
                    for idx, row in eugene_data.iterrows():
                        name = row.get('Unnamed: 6', '')
                        if 'Евгений' in str(name) or 'Косиц' in str(name):
                            print(f"      📋 Запись #{idx} - ЕВГЕНИЙ КОСИЦИН:")
                            
                            # Ищем зарплату в столбце Unnamed: 7
                            salary = row.get('Unnamed: 7', 0)
                            if salary and salary > 0:
                                print(f"         💰 Зарплата: {salary:,.2f} руб.")
                                
                                # Сохраняем данные
                                if sheet_name not in employees_2025['Евгений Косицин']:
                                    employees_2025['Евгений Косицин'][sheet_name] = []
                                employees_2025['Евгений Косицин'][sheet_name].append(salary)
                            
                            # Ищем дополнительные выплаты в столбце Unnamed: 10
                            additional = row.get('Unnamed: 10', 0)
                            if additional and additional > 0:
                                print(f"         ➕ Дополнительно: {additional:,.2f} руб.")
                                
                                # Сохраняем дополнительные выплаты
                                if f"{sheet_name}_additional" not in employees_2025['Евгений Косицин']:
                                    employees_2025['Евгений Косицин'][f"{sheet_name}_additional"] = []
                                employees_2025['Евгений Косицин'][f"{sheet_name}_additional"].append(additional)
                
            except Exception as e:
                print(f"   ❌ Ошибка при чтении листа {sheet_name}: {e}")
        
        # Анализируем собранные данные за 2025 год
        print("\n" + "="*80)
        print("ИТОГОВЫЙ АНАЛИЗ ЗАРПЛАТ ЗА 2025 ГОД")
        print("="*80)
        
        for employee, data in employees_2025.items():
            print(f"\n👤 {employee.upper()}")
            print("-" * 50)
            
            if data:
                total_salary_2025 = 0
                total_additional_2025 = 0
                monthly_data = {}
                
                for key, values in data.items():
                    if not key.endswith('_additional'):
                        # Основные зарплаты
                        month_total = sum(values)
                        total_salary_2025 += month_total
                        monthly_data[key] = month_total
                        print(f"   📅 {key}: {month_total:,.2f} руб.")
                    else:
                        # Дополнительные выплаты
                        month_additional = sum(values)
                        total_additional_2025 += month_additional
                        print(f"   ➕ {key.replace('_additional', '')} (доп.): {month_additional:,.2f} руб.")
                
                total_2025 = total_salary_2025 + total_additional_2025
                months_count = len([k for k in data.keys() if not k.endswith('_additional')])
                
                print(f"\n   📊 ИТОГО ЗА 2025 ГОД:")
                print(f"      💰 Основные зарплаты: {total_salary_2025:,.2f} руб.")
                print(f"      ➕ Дополнительные выплаты: {total_additional_2025:,.2f} руб.")
                print(f"      🎯 ОБЩИЙ ДОХОД: {total_2025:,.2f} руб.")
                
                if months_count > 0:
                    avg_monthly_2025 = total_2025 / months_count
                    print(f"      📅 Среднемесячно: {avg_monthly_2025:,.2f} руб.")
                    print(f"      🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {total_2025:,.2f} руб.")
            else:
                print("❌ Данные за 2025 год не найдены")
        
        # Сравнительный анализ за 2025 год
        print("\n" + "="*80)
        print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ ЗА 2025 ГОД")
        print("="*80)
        
        artem_total_2025 = 0
        eugene_total_2025 = 0
        
        if employees_2025['Артем Василевский']:
            for key, values in employees_2025['Артем Василевский'].items():
                if not key.endswith('_additional'):
                    artem_total_2025 += sum(values)
                else:
                    artem_total_2025 += sum(values)
        
        if employees_2025['Евгений Косицин']:
            for key, values in employees_2025['Евгений Косицин'].items():
                if not key.endswith('_additional'):
                    eugene_total_2025 += sum(values)
                else:
                    eugene_total_2025 += sum(values)
        
        if artem_total_2025 > 0 and eugene_total_2025 > 0:
            print(f"\n📊 СРАВНЕНИЕ ДОХОДОВ ЗА 2025 ГОД:")
            print(f"   👤 Артем Василевский: {artem_total_2025:,.2f} руб.")
            print(f"   👤 Евгений Косицин:   {eugene_total_2025:,.2f} руб.")
            print(f"   📈 Разница: {artem_total_2025 - eugene_total_2025:,.2f} руб.")
            print(f"   📊 Артем получает на {((artem_total_2025 / eugene_total_2025 - 1) * 100):.1f}% больше")
        
        # Сохраняем отчет за 2025 год
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"salary_analysis_2025_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("АНАЛИЗ ЗАРПЛАТ ЗА 2025 ГОД\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n")
            f.write(f"Листы за 2025 год: {sheets_2025}\n\n")
            
            for employee, data in employees_2025.items():
                f.write(f"{employee.upper()}\n")
                f.write("-" * 40 + "\n")
                
                if data:
                    total_salary = 0
                    total_additional = 0
                    
                    for key, values in data.items():
                        if not key.endswith('_additional'):
                            month_total = sum(values)
                            total_salary += month_total
                            f.write(f"{key}: {month_total:,.2f} руб.\n")
                        else:
                            month_additional = sum(values)
                            total_additional += month_additional
                            f.write(f"{key.replace('_additional', '')} (доп.): {month_additional:,.2f} руб.\n")
                    
                    total = total_salary + total_additional
                    months_count = len([k for k in data.keys() if not k.endswith('_additional')])
                    
                    f.write(f"\nИТОГО ЗА 2025 ГОД: {total:,.2f} руб.\n")
                    if months_count > 0:
                        avg_monthly = total / months_count
                        f.write(f"Среднемесячно: {avg_monthly:,.2f} руб.\n")
                else:
                    f.write("Данные не найдены\n")
                
                f.write("\n")
        
        print(f"\n📄 Отчет за 2025 год сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск анализатора зарплат за 2025 год")
    print("=" * 60)
    analyze_2025_salaries()
    print("\n✅ Анализ зарплат за 2025 год завершен!")
