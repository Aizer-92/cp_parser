#!/usr/bin/env python3
"""
Анализатор зарплат из сводных листов Excel файла
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_summary_sheets():
    """Анализирует зарплаты из сводных листов"""
    
    file_path = "Табл выплаты 2025 (1).xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return
    
    print(f"📊 Анализ сводных листов файла: {file_path}")
    
    try:
        # Читаем все листы Excel файла
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"✅ Найдено листов: {len(sheet_names)}")
        print(f"📋 Названия листов: {sheet_names}")
        
        # Ищем сводные листы
        summary_sheets = [sheet for sheet in sheet_names if 'сводная' in sheet.lower() or 'сводная по зп' in sheet.lower()]
        print(f"\n📊 Найденные сводные листы: {summary_sheets}")
        
        # Анализируем каждый сводный лист
        for sheet_name in summary_sheets:
            print(f"\n🔍 Анализируем сводный лист: {sheet_name}")
            
            try:
                # Читаем лист
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                print(f"   📊 Размер данных: {df.shape[0]} строк, {df.shape[1]} столбцов")
                print(f"   📋 Столбцы: {list(df.columns)}")
                
                # Ищем данные Артема Василевского
                artem_data = df[df.astype(str).apply(lambda x: x.str.contains('Артем', case=False, na=False)).any(axis=1)]
                
                if not artem_data.empty:
                    print(f"   ✅ Найдено {len(artem_data)} записей для Артема")
                    
                    for idx, row in artem_data.iterrows():
                        print(f"      📋 Запись #{idx}:")
                        
                        # Показываем все данные строки
                        for col, value in row.items():
                            if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                                print(f"         {col}: {value}")
                        
                        # Извлекаем месячные данные
                        monthly_data = {}
                        total = 0
                        
                        for col in df.columns:
                            if col not in ['Unnamed: 0', 'Всего'] and pd.notna(row.get(col, 0)):
                                try:
                                    value = float(row.get(col, 0))
                                    if value > 0:
                                        monthly_data[col] = value
                                        total += value
                                except:
                                    pass
                        
                        if monthly_data:
                            print(f"         📅 Месячные данные: {monthly_data}")
                            print(f"         💰 Общий доход: {total:,.2f} руб.")
                            
                            # Расчет среднегодовых показателей
                            months_count = len(monthly_data)
                            if months_count > 0:
                                avg_monthly = total / months_count
                                annual_estimate = avg_monthly * 12
                                print(f"         📊 Среднемесячно: {avg_monthly:,.2f} руб.")
                                print(f"         🎯 СРЕДНЕГОДОВАЯ ОЦЕНКА: {annual_estimate:,.2f} руб.")
                
                # Ищем данные Евгения Косицина
                eugene_data = df[df.astype(str).apply(lambda x: x.str.contains('Евгений|Косиц', case=False, na=False)).any(axis=1)]
                
                if not eugene_data.empty:
                    print(f"   ✅ Найдено {len(eugene_data)} записей для Евгения")
                    
                    for idx, row in eugene_data.iterrows():
                        print(f"      📋 Запись #{idx}:")
                        
                        # Показываем все данные строки
                        for col, value in row.items():
                            if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                                print(f"         {col}: {value}")
                        
                        # Извлекаем месячные данные
                        monthly_data = {}
                        total = 0
                        
                        for col in df.columns:
                            if col not in ['Unnamed: 0', 'Всего'] and pd.notna(row.get(col, 0)):
                                try:
                                    value = float(row.get(col, 0))
                                    if value > 0:
                                        monthly_data[col] = value
                                        total += value
                                except:
                                    pass
                        
                        if monthly_data:
                            print(f"         📅 Месячные данные: {monthly_data}")
                            print(f"         💰 Общий доход: {total:,.2f} руб.")
                            
                            # Расчет среднегодовых показателей
                            months_count = len(monthly_data)
                            if months_count > 0:
                                avg_monthly = total / months_count
                                annual_estimate = avg_monthly * 12
                                print(f"         📊 Среднемесячно: {avg_monthly:,.2f} руб.")
                                print(f"         🎯 СРЕДНЕГОДОВАЯ ОЦЕНКА: {annual_estimate:,.2f} руб.")
                
            except Exception as e:
                print(f"   ❌ Ошибка при чтении листа {sheet_name}: {e}")
        
        # Создаем итоговый анализ на основе найденных данных
        print("\n" + "="*80)
        print("ИТОГОВЫЙ АНАЛИЗ НА ОСНОВЕ СВОДНЫХ ДАННЫХ")
        print("="*80)
        
        # Данные из "Сводная по зп" листа
        print("\n📊 Данные из листа 'Сводная по зп':")
        
        try:
            df_summary = pd.read_excel(file_path, sheet_name='Сводная по зп')
            
            # Артем
            artem_row = df_summary[df_summary['Unnamed: 0'] == 'Артем']
            if not artem_row.empty:
                artem_total = artem_row['Всего'].iloc[0]
                print(f"   👤 Артем Василевский: {artem_total:,.2f} руб. (общий доход)")
                
                # Месячные данные Артема
                artem_monthly = {}
                for col in df_summary.columns:
                    if col not in ['Unnamed: 0', 'Всего'] and pd.notna(artem_row[col].iloc[0]):
                        try:
                            value = float(artem_row[col].iloc[0])
                            if value > 0:
                                artem_monthly[col] = value
                        except:
                            pass
                
                if artem_monthly:
                    months_count = len(artem_monthly)
                    avg_monthly_artem = artem_total / months_count
                    annual_artem = avg_monthly_artem * 12
                    print(f"      📅 Месяцы с данными: {list(artem_monthly.keys())}")
                    print(f"      📊 Среднемесячно: {avg_monthly_artem:,.2f} руб.")
                    print(f"      🎯 СРЕДНЕГОДОВАЯ ОЦЕНКА: {annual_artem:,.2f} руб.")
            
            # Евгений
            eugene_row = df_summary[df_summary['Unnamed: 0'] == 'Евгений Косицын']
            if not eugene_row.empty:
                eugene_total = eugene_row['Всего'].iloc[0]
                print(f"   👤 Евгений Косицин: {eugene_total:,.2f} руб. (общий доход)")
                
                # Месячные данные Евгения
                eugene_monthly = {}
                for col in df_summary.columns:
                    if col not in ['Unnamed: 0', 'Всего'] and pd.notna(eugene_row[col].iloc[0]):
                        try:
                            value = float(eugene_row[col].iloc[0])
                            if value > 0:
                                eugene_monthly[col] = value
                        except:
                            pass
                
                if eugene_monthly:
                    months_count = len(eugene_monthly)
                    avg_monthly_eugene = eugene_total / months_count
                    annual_eugene = avg_monthly_eugene * 12
                    print(f"      📅 Месяцы с данными: {list(eugene_monthly.keys())}")
                    print(f"      📊 Среднемесячно: {avg_monthly_eugene:,.2f} руб.")
                    print(f"      🎯 СРЕДНЕГОДОВАЯ ОЦЕНКА: {annual_eugene:,.2f} руб.")
                
                # Сравнительный анализ
                if not artem_row.empty and not eugene_row.empty:
                    print(f"\n📈 СРАВНИТЕЛЬНЫЙ АНАЛИЗ:")
                    print(f"   💰 Разница в общем доходе: {artem_total - eugene_total:,.2f} руб.")
                    print(f"   📊 Артем получает на {((artem_total / eugene_total - 1) * 100):.1f}% больше")
                    
                    if 'avg_monthly_artem' in locals() and 'avg_monthly_eugene' in locals():
                        print(f"   📅 Разница в среднемесячном доходе: {avg_monthly_artem - avg_monthly_eugene:,.2f} руб.")
                        print(f"   🎯 Разница в среднегодовых оценках: {annual_artem - annual_eugene:,.2f} руб.")
        
        except Exception as e:
            print(f"   ❌ Ошибка при анализе сводного листа: {e}")
        
        # Сохраняем отчет
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"summary_sheet_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("АНАЛИЗ СВОДНЫХ ЛИСТОВ EXCEL ФАЙЛА\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Файл: {file_path}\n")
            f.write(f"Сводные листы: {summary_sheets}\n\n")
            
            # Сохраняем данные из сводного листа
            try:
                df_summary = pd.read_excel(file_path, sheet_name='Сводная по зп')
                f.write("ДАННЫЕ ИЗ ЛИСТА 'СВОДНАЯ ПО ЗП':\n")
                f.write("-" * 40 + "\n")
                f.write(df_summary.to_string())
            except:
                f.write("Не удалось прочитать сводный лист\n")
        
        print(f"\n📄 Отчет сохранен в файл: {output_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск анализатора сводных листов")
    print("=" * 60)
    analyze_summary_sheets()
    print("\n✅ Анализ сводных листов завершен!")
