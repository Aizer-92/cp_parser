#!/usr/bin/env python3
"""
Анализатор зарплат с учетом всех листов Excel файла
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_multi_sheet_salaries():
    """Анализирует зарплаты со всех листов Excel файла"""
    
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Анализ всех листов файла: {file_path}")
    
    try:
        # Читаем все листы Excel файла
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"✅ Найдено листов: {len(sheet_names)}")
        print(f"📋 Названия листов: {sheet_names}")
        
        # Словарь для хранения данных по сотрудникам
        employees_data = {
            'Артем Василевский': [],
            'Евгений Косицин': []
        }
        
        # Анализируем каждый лист
        for sheet_name in sheet_names:
            print(f"\n🔍 Анализируем лист: {sheet_name}")
            
            try:
                # Читаем лист
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                print(f"   📊 Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов")
                print(f"   📋 Столбцы: {list(df.columns)}")
                
                # Ищем столбцы "ст" и "проценты"
                st_columns = []
                percentage_columns = []
                
                for col in df.columns:
                    col_str = str(col).lower()
                    if 'ст' in col_str and len(col_str) <= 3:  # Ищем именно "ст"
                        st_columns.append(col)
                    if 'процент' in col_str or 'проц' in col_str:
                        percentage_columns.append(col)
                
                print(f"   💰 Найденные столбцы 'ст': {st_columns}")
                print(f"   📊 Найденные столбцы 'проценты': {percentage_columns}")
                
                # Ищем данные Артема Василевского
                artem_data = df[df.astype(str).apply(lambda x: x.str.contains('Артем|Василевский', case=False, na=False)).any(axis=1)]
                
                if not artem_data.empty:
                    print(f"   ✅ Найдено {len(artem_data)} записей для Артема Василевского")
                    
                    for idx, row in artem_data.iterrows():
                        print(f"      📋 Запись #{idx}:")
                        
                        # Извлекаем данные из столбцов "ст" и "проценты"
                        st_values = []
                        percentage_values = []
                        
                        for col in st_columns:
                            value = row.get(col, 0)
                            if pd.notna(value) and value != 0:
                                st_values.append((col, value))
                        
                        for col in percentage_columns:
                            value = row.get(col, 0)
                            if pd.notna(value) and value != 0:
                                percentage_values.append((col, value))
                        
                        if st_values:
                            print(f"         💰 Значения в столбцах 'ст': {st_values}")
                        if percentage_values:
                            print(f"         📊 Значения в столбцах 'проценты': {percentage_values}")
                        
                        # Показываем все данные строки
                        for col, value in row.items():
                            if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                                print(f"         {col}: {value}")
                        
                        # Сохраняем данные для анализа
                        employees_data['Артем Василевский'].append({
                            'sheet': sheet_name,
                            'row': idx,
                            'st_values': st_values,
                            'percentage_values': percentage_values,
                            'all_data': dict(row)
                        })
                
                # Ищем данные Евгения Косицина
                eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косицин|Косицын', case=False, na=False)).any(axis=1)]
                
                if not eugene_data.empty:
                    print(f"   ✅ Найдено {len(eugene_data)} записей для Евгения Косицина")
                    
                    for idx, row in eugene_data.iterrows():
                        print(f"      📋 Запись #{idx}:")
                        
                        # Извлекаем данные из столбцов "ст" и "проценты"
                        st_values = []
                        percentage_values = []
                        
                        for col in st_columns:
                            value = row.get(col, 0)
                            if pd.notna(value) and value != 0:
                                st_values.append((col, value))
                        
                        for col in percentage_columns:
                            value = row.get(col, 0)
                            if pd.notna(value) and value != 0:
                                percentage_values.append((col, value))
                        
                        if st_values:
                            print(f"         💰 Значения в столбцах 'ст': {st_values}")
                        if percentage_values:
                            print(f"         📊 Значения в столбцах 'проценты': {percentage_values}")
                        
                        # Показываем все данные строки
                        for col, value in row.items():
                            if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                                print(f"         {col}: {value}")
                        
                        # Сохраняем данные для анализа
                        employees_data['Евгений Косицин'].append({
                            'sheet': sheet_name,
                            'row': idx,
                            'st_values': st_values,
                            'percentage_values': percentage_values,
                            'all_data': dict(row)
                        })
                
            except Exception as e:
                print(f"   ❌ Ошибка при чтении листа {sheet_name}: {e}")
        
        # Анализируем собранные данные
        print("\n" + "="*80)
        print("ИТОГОВЫЙ АНАЛИЗ СОБРАННЫХ ДАННЫХ")
        print("="*80)
        
        for employee, data_list in employees_data.items():
            print(f"\n👤 {employee.upper()}")
            print("-" * 50)
            
            if data_list:
                print(f"✅ Найдено {len(data_list)} записей в {len(set([d['sheet'] for d in data_list]))} листах")
                
                total_st = 0
                total_percentage = 0
                monthly_data = {}
                
                for data in data_list:
                    sheet = data['sheet']
                    st_sum = sum([val for _, val in data['st_values']])
                    percentage_sum = sum([val for _, val in data['percentage_values']])
                    
                    total_st += st_sum
                    total_percentage += percentage_sum
                    
                    if sheet not in monthly_data:
                        monthly_data[sheet] = {'st': 0, 'percentage': 0}
                    
                    monthly_data[sheet]['st'] += st_sum
                    monthly_data[sheet]['percentage'] += percentage_sum
                    
                    print(f"   📅 {sheet}: ст={st_sum:,.2f}, проценты={percentage_sum:,.2f}")
                
                print(f"\n   📊 ИТОГО:")
                print(f"      💰 Общая сумма 'ст': {total_st:,.2f}")
                print(f"      📊 Общая сумма 'проценты': {total_percentage:,.2f}")
                
                # Расчет среднегодовых показателей
                months_count = len(monthly_data)
                if months_count > 0:
                    avg_monthly_st = total_st / months_count
                    avg_monthly_percentage = total_percentage / months_count
                    annual_st = avg_monthly_st * 12
                    annual_percentage = avg_monthly_percentage * 12
                    
                    print(f"      📅 Среднемесячные показатели:")
                    print(f"         💰 'ст': {avg_monthly_st:,.2f} руб.")
                    print(f"         📊 'проценты': {avg_monthly_percentage:,.2f} руб.")
                    print(f"      🎯 СРЕДНЕГОДОВЫЕ ПОКАЗАТЕЛИ:")
                    print(f"         💰 'ст': {annual_st:,.2f} руб.")
                    print(f"         📊 'проценты': {annual_percentage:,.2f} руб.")
            else:
                print("❌ Данные не найдены")
        
        # Сохраняем отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"multi_sheet_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("АНАЛИЗ ВСЕХ ЛИСТОВ EXCEL ФАЙЛА\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n")
            f.write(f"Количество листов: {len(sheet_names)}\n")
            f.write(f"Листы: {sheet_names}\n\n")
            
            for employee, data_list in employees_data.items():
                f.write(f"{employee.upper()}\n")
                f.write("-" * 40 + "\n")
                
                if data_list:
                    total_st = sum([sum([val for _, val in d['st_values']]) for d in data_list])
                    total_percentage = sum([sum([val for _, val in d['percentage_values']]) for d in data_list])
                    months_count = len(set([d['sheet'] for d in data_list]))
                    
                    f.write(f"Найдено записей: {len(data_list)}\n")
                    f.write(f"Количество месяцев: {months_count}\n")
                    f.write(f"Общая сумма 'ст': {total_st:,.2f}\n")
                    f.write(f"Общая сумма 'проценты': {total_percentage:,.2f}\n")
                    
                    if months_count > 0:
                        avg_monthly_st = total_st / months_count
                        avg_monthly_percentage = total_percentage / months_count
                        annual_st = avg_monthly_st * 12
                        annual_percentage = avg_monthly_percentage * 12
                        
                        f.write(f"Среднемесячно 'ст': {avg_monthly_st:,.2f}\n")
                        f.write(f"Среднемесячно 'проценты': {avg_monthly_percentage:,.2f}\n")
                        f.write(f"Среднегодово 'ст': {annual_st:,.2f}\n")
                        f.write(f"Среднегодово 'проценты': {annual_percentage:,.2f}\n")
                else:
                    f.write("Данные не найдены\n")
                
                f.write("\n")
        
        print(f"\n📄 Отчет сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск анализатора всех листов Excel")
    print("=" * 60)
    analyze_multi_sheet_salaries()
    print("\n✅ Анализ всех листов завершен!")
