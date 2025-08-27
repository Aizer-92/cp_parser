#!/usr/bin/env python3
"""
Анализатор зарплат за 2025 год
"""

import pandas as pd
from datetime import datetime
import os

def analyze_2025():
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
        
        # Ищем листы за 2025 год
        sheets_2025 = [sheet for sheet in sheet_names if '2025' in sheet and not 'архив' in sheet.lower()]
        print(f"\n📅 Найденные листы за 2025 год: {sheets_2025}")
        
        # Словарь для хранения данных
        employees_2025 = {
            'Артем Василевский': {},
            'Евгений Косицин': {}
        }
        
        # Анализируем каждый лист за 2025 год
        for sheet_name in sheets_2025:
            print(f"\n🔍 Анализируем лист: {sheet_name}")
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Ищем данные Артема
                artem_data = df[df.astype(str).apply(lambda x: x.str.contains('Артем|Василевский', case=False, na=False)).any(axis=1)]
                
                if not artem_data.empty:
                    for idx, row in artem_data.iterrows():
                        name = row.get('Unnamed: 6', '')
                        if 'Артем' in str(name):
                            salary = row.get('Unnamed: 7', 0)
                            additional = row.get('Unnamed: 10', 0)
                            
                            if salary and salary > 0:
                                if sheet_name not in employees_2025['Артем Василевский']:
                                    employees_2025['Артем Василевский'][sheet_name] = {'salary': 0, 'additional': 0}
                                employees_2025['Артем Василевский'][sheet_name]['salary'] += salary
                            
                            if additional and additional > 0:
                                if sheet_name not in employees_2025['Артем Василевский']:
                                    employees_2025['Артем Василевский'][sheet_name] = {'salary': 0, 'additional': 0}
                                employees_2025['Артем Василевский'][sheet_name]['additional'] += additional
                
                # Ищем данные Евгения
                eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косицин|Косицын', case=False, na=False)).any(axis=1)]
                
                if not eugene_data.empty:
                    for idx, row in eugene_data.iterrows():
                        name = row.get('Unnamed: 6', '')
                        if 'Евгений' in str(name) or 'Косиц' in str(name):
                            salary = row.get('Unnamed: 7', 0)
                            additional = row.get('Unnamed: 10', 0)
                            
                            if salary and salary > 0:
                                if sheet_name not in employees_2025['Евгений Косицин']:
                                    employees_2025['Евгений Косицин'][sheet_name] = {'salary': 0, 'additional': 0}
                                employees_2025['Евгений Косицин'][sheet_name]['salary'] += salary
                            
                            if additional and additional > 0:
                                if sheet_name not in employees_2025['Евгений Косицин']:
                                    employees_2025['Евгений Косицин'][sheet_name] = {'salary': 0, 'additional': 0}
                                employees_2025['Евгений Косицин'][sheet_name]['additional'] += additional
                
            except Exception as e:
                print(f"   ❌ Ошибка при чтении листа {sheet_name}: {e}")
        
        # Анализируем собранные данные
        print("\n" + "="*80)
        print("ИТОГОВЫЙ АНАЛИЗ ЗАРПЛАТ ЗА 2025 ГОД")
        print("="*80)
        
        for employee, data in employees_2025.items():
            print(f"\n👤 {employee.upper()}")
            print("-" * 50)
            
            if data:
                total_salary = 0
                total_additional = 0
                
                for month, amounts in data.items():
                    salary = amounts.get('salary', 0)
                    additional = amounts.get('additional', 0)
                    total = salary + additional
                    
                    total_salary += salary
                    total_additional += additional
                    
                    print(f"   📅 {month}: {total:,.2f} руб. (зарплата: {salary:,.2f}, доп.: {additional:,.2f})")
                
                total_2025 = total_salary + total_additional
                months_count = len(data)
                
                print(f"\n   📊 ИТОГО ЗА 2025 ГОД:")
                print(f"      💰 Основные зарплаты: {total_salary:,.2f} руб.")
                print(f"      ➕ Дополнительные выплаты: {total_additional:,.2f} руб.")
                print(f"      🎯 ОБЩИЙ ДОХОД: {total_2025:,.2f} руб.")
                
                if months_count > 0:
                    avg_monthly = total_2025 / months_count
                    print(f"      📅 Среднемесячно: {avg_monthly:,.2f} руб.")
                    print(f"      🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {total_2025:,.2f} руб.")
            else:
                print("❌ Данные за 2025 год не найдены")
        
        # Сравнительный анализ
        print("\n" + "="*80)
        print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ ЗА 2025 ГОД")
        print("="*80)
        
        artem_total = sum([sum(amounts.values()) for amounts in employees_2025['Артем Василевский'].values()])
        eugene_total = sum([sum(amounts.values()) for amounts in employees_2025['Евгений Косицин'].values()])
        
        if artem_total > 0 and eugene_total > 0:
            print(f"\n📊 СРАВНЕНИЕ ДОХОДОВ ЗА 2025 ГОД:")
            print(f"   👤 Артем Василевский: {artem_total:,.2f} руб.")
            print(f"   👤 Евгений Косицин:   {eugene_total:,.2f} руб.")
            print(f"   📈 Разница: {artem_total - eugene_total:,.2f} руб.")
            print(f"   📊 Артем получает на {((artem_total / eugene_total - 1) * 100):.1f}% больше")
        
        # Сохраняем отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"salary_2025_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("АНАЛИЗ ЗАРПЛАТ ЗА 2025 ГОД\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Листы за 2025 год: {sheets_2025}\n\n")
            
            for employee, data in employees_2025.items():
                f.write(f"{employee.upper()}\n")
                f.write("-" * 40 + "\n")
                
                if data:
                    total_salary = 0
                    total_additional = 0
                    
                    for month, amounts in data.items():
                        salary = amounts.get('salary', 0)
                        additional = amounts.get('additional', 0)
                        total = salary + additional
                        
                        total_salary += salary
                        total_additional += additional
                        
                        f.write(f"{month}: {total:,.2f} руб. (зарплата: {salary:,.2f}, доп.: {additional:,.2f})\n")
                    
                    total_2025 = total_salary + total_additional
                    f.write(f"\nИТОГО ЗА 2025 ГОД: {total_2025:,.2f} руб.\n")
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
    analyze_2025()
    print("\n✅ Анализ зарплат за 2025 год завершен!")
