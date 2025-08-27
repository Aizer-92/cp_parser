#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальный анализ таблицы выплат 2025 - поиск данных по Флориде с анализом ставок и процентов
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Настройка для корректного отображения русских символов
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS']

class FloridaFinalAnalyzer:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.all_data = {}
        self.florida_data = None
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_monthly_sheets(self):
        """Загрузка данных только из листов с названиями месяцев"""
        print("📊 Загружаю данные из листов с названиями месяцев...")
        
        try:
            # Загружаем все листы
            excel_file = pd.ExcelFile(self.excel_file_path)
            print(f"📋 Найдены листы: {excel_file.sheet_names}")
            
            # Фильтруем только листы с названиями месяцев
            month_keywords = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
            monthly_sheets = []
            
            for sheet_name in excel_file.sheet_names:
                sheet_lower = sheet_name.lower()
                if any(month in sheet_lower for month in month_keywords):
                    monthly_sheets.append(sheet_name)
            
            print(f"📅 Листы с месяцами: {monthly_sheets}")
            
            for sheet_name in monthly_sheets:
                try:
                    data = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
                    self.all_data[sheet_name] = data
                    print(f"✅ Лист '{sheet_name}': {data.shape[0]} строк, {data.shape[1]} колонок")
                    
                    # Показываем колонки для понимания структуры
                    if data.shape[0] > 0:
                        print(f"   Колонки: {list(data.columns)}")
                        
                except Exception as e:
                    print(f"❌ Ошибка при загрузке листа '{sheet_name}': {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке данных: {e}")
            return False
    
    def search_florida_and_analyze(self):
        """Поиск данных по Флориде и анализ ставок/процентов"""
        print("\n🔍 Ищу данные по Флориде в месячных листах...")
        
        if not self.all_data:
            print("❌ Данные не загружены")
            return False
        
        # Ищем Флориду в разных вариантах написания
        florida_patterns = ['флорида', 'florida', 'Флорида', 'Florida', 'ФЛОРИДА', 'флорид', 'Флорид']
        
        florida_results = []
        
        for sheet_name, data in self.all_data.items():
            print(f"\n🔍 Проверяю лист: {sheet_name}")
            
            # Поиск по всем колонкам
            for col in data.columns:
                if data[col].dtype == 'object':  # Только текстовые колонки
                    for pattern in florida_patterns:
                        try:
                            mask = data[col].astype(str).str.contains(pattern, case=False, na=False)
                            if mask.any():
                                found_rows = data[mask]
                                print(f"  ✅ Найдено в колонке '{col}': {len(found_rows)} строк")
                                
                                # Анализируем найденные строки
                                for idx, row in found_rows.iterrows():
                                    result = {
                                        'sheet': sheet_name,
                                        'row_index': idx,
                                        'data': row.to_dict()
                                    }
                                    florida_results.append(result)
                                    
                                    # Показываем ключевые данные
                                    print(f"    Строка {idx}:")
                                    for key, value in row.items():
                                        if pd.notna(value) and str(value).strip() != '':
                                            print(f"      {key}: {value}")
                                
                        except Exception as e:
                            continue
        
        if florida_results:
            print(f"\n✅ Найдено {len(florida_results)} записей с данными Флориды")
            
            # Создаем DataFrame с данными Флориды
            florida_data_list = []
            for result in florida_results:
                row_data = result['data'].copy()
                row_data['sheet_name'] = result['sheet']
                row_data['row_index'] = result['row_index']
                florida_data_list.append(row_data)
            
            self.florida_data = pd.DataFrame(florida_data_list)
            print(f"📋 Объединенные данные Флориды: {len(self.florida_data)} строк")
            
            return True
        else:
            print("❌ Данные по Флориде не найдены")
            return False
    
    def analyze_rates_and_percentages(self):
        """Анализ ставок (СС) и процентов"""
        if self.florida_data is None or len(self.florida_data) == 0:
            print("❌ Нет данных Флориды для анализа")
            return
        
        print("\n📊 Анализирую ставки и проценты...")
        
        # Ищем колонки со ставками (СС)
        rate_columns = []
        percentage_columns = []
        
        for col in self.florida_data.columns:
            col_str = str(col).lower()
            
            # Ищем ставки (СС)
            if 'сс' in col_str or 'ставка' in col_str or 'rate' in col_str:
                rate_columns.append(col)
            
            # Ищем проценты
            if 'процент' in col_str or 'percent' in col_str or '%' in col_str:
                percentage_columns.append(col)
        
        print(f"📈 Найдены колонки со ставками: {rate_columns}")
        print(f"📊 Найдены колонки с процентами: {percentage_columns}")
        
        # Если не найдены специальные колонки, ищем числовые
        if not rate_columns and not percentage_columns:
            numeric_columns = self.florida_data.select_dtypes(include=[np.number]).columns.tolist()
            print(f"📊 Числовые колонки: {numeric_columns}")
            
            # Пытаемся определить ставки и проценты по значениям
            for col in numeric_columns:
                values = pd.to_numeric(self.florida_data[col], errors='coerce').dropna()
                if len(values) > 0:
                    avg_value = values.mean()
                    if avg_value > 1000:  # Большие значения - вероятно ставки
                        rate_columns.append(col)
                    elif avg_value <= 100:  # Малые значения - вероятно проценты
                        percentage_columns.append(col)
        
        results = {}
        
        # Анализируем ставки
        for col in rate_columns:
            try:
                values = pd.to_numeric(self.florida_data[col], errors='coerce')
                values = values.dropna()
                
                if len(values) > 0:
                    stats = {
                        'тип': 'ставка',
                        'среднее': values.mean(),
                        'медиана': values.median(),
                        'мин': values.min(),
                        'макс': values.max(),
                        'стандартное_отклонение': values.std(),
                        'количество_значений': len(values)
                    }
                    results[col] = stats
                    
                    print(f"\n📊 Статистика по ставке '{col}':")
                    for stat, value in stats.items():
                        if stat != 'тип':
                            print(f"  {stat}: {value:.2f}")
                    
            except Exception as e:
                print(f"❌ Ошибка при анализе колонки '{col}': {e}")
        
        # Анализируем проценты
        for col in percentage_columns:
            try:
                values = pd.to_numeric(self.florida_data[col], errors='coerce')
                values = values.dropna()
                
                if len(values) > 0:
                    stats = {
                        'тип': 'процент',
                        'среднее': values.mean(),
                        'медиана': values.median(),
                        'мин': values.min(),
                        'макс': values.max(),
                        'стандартное_отклонение': values.std(),
                        'количество_значений': len(values)
                    }
                    results[col] = stats
                    
                    print(f"\n📊 Статистика по проценту '{col}':")
                    for stat, value in stats.items():
                        if stat != 'тип':
                            print(f"  {stat}: {value:.2f}")
                    
            except Exception as e:
                print(f"❌ Ошибка при анализе колонки '{col}': {e}")
        
        return results
    
    def create_comprehensive_visualizations(self, stats_results):
        """Создание комплексных визуализаций"""
        if not stats_results:
            return
        
        print("\n📈 Создаю комплексные визуализации...")
        
        # Создаем большой график с 4 подграфиками
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Комплексный анализ данных Флориды', fontsize=16, fontweight='bold')
        
        # Разделяем данные по типам
        rate_cols = [col for col, stats in stats_results.items() if stats.get('тип') == 'ставка']
        percentage_cols = [col for col, stats in stats_results.items() if stats.get('тип') == 'процент']
        
        # График 1: Средние ставки
        if rate_cols:
            means = [stats_results[col]['среднее'] for col in rate_cols]
            
            axes[0, 0].bar(range(len(rate_cols)), means, color='lightblue', alpha=0.7)
            axes[0, 0].set_title('Средние ставки (СС)')
            axes[0, 0].set_xticks(range(len(rate_cols)))
            axes[0, 0].set_xticklabels(rate_cols, rotation=45, ha='right')
            axes[0, 0].set_ylabel('Сумма (руб.)')
            
            # Добавляем значения на столбцы
            for i, v in enumerate(means):
                axes[0, 0].text(i, v + max(means)*0.01, f'{v:,.0f}', 
                               ha='center', va='bottom', fontweight='bold')
        else:
            axes[0, 0].text(0.5, 0.5, 'Нет данных о ставках', ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('Средние ставки (СС)')
        
        # График 2: Средние проценты
        if percentage_cols:
            means = [stats_results[col]['среднее'] for col in percentage_cols]
            
            axes[0, 1].bar(range(len(percentage_cols)), means, color='lightgreen', alpha=0.7)
            axes[0, 1].set_title('Средние проценты')
            axes[0, 1].set_xticks(range(len(percentage_cols)))
            axes[0, 1].set_xticklabels(percentage_cols, rotation=45, ha='right')
            axes[0, 1].set_ylabel('Процент (%)')
            
            # Добавляем значения на столбцы
            for i, v in enumerate(means):
                axes[0, 1].text(i, v + max(means)*0.01, f'{v:.1f}%', 
                               ha='center', va='bottom', fontweight='bold')
        else:
            axes[0, 1].text(0.5, 0.5, 'Нет данных о процентах', ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 1].set_title('Средние проценты')
        
        # График 3: Сравнение мин/макс для ставок
        if rate_cols:
            mins = [stats_results[col]['мин'] for col in rate_cols]
            maxs = [stats_results[col]['макс'] for col in rate_cols]
            
            x = np.arange(len(rate_cols))
            width = 0.35
            
            axes[1, 0].bar(x - width/2, mins, width, label='Минимум', color='lightcoral', alpha=0.7)
            axes[1, 0].bar(x + width/2, maxs, width, label='Максимум', color='lightblue', alpha=0.7)
            axes[1, 0].set_title('Минимальные и максимальные ставки')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(rate_cols, rotation=45, ha='right')
            axes[1, 0].legend()
            axes[1, 0].set_ylabel('Сумма (руб.)')
        else:
            axes[1, 0].text(0.5, 0.5, 'Нет данных о ставках', ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Минимальные и максимальные ставки')
        
        # График 4: Итоговая сводка
        all_cols = list(stats_results.keys())
        if all_cols:
            # Создаем сводную таблицу
            summary_data = []
            for col in all_cols:
                stats = stats_results[col]
                summary_data.append({
                    'Колонка': col,
                    'Тип': stats.get('тип', 'неизвестно'),
                    'Среднее': stats['среднее'],
                    'Количество': stats['количество_значений']
                })
            
            summary_df = pd.DataFrame(summary_data)
            
            # Создаем круговую диаграмму по типам
            type_counts = summary_df['Тип'].value_counts()
            axes[1, 1].pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title('Распределение по типам данных')
        else:
            axes[1, 1].text(0.5, 0.5, 'Нет данных для анализа', ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Распределение по типам данных')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'florida_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
        print(f"✅ Комплексный график сохранен: {self.output_dir / 'florida_comprehensive_analysis.png'}")
        plt.show()
    
    def create_summary_report(self, stats_results):
        """Создание итогового отчета"""
        print("\n📋 Создаю итоговый отчет...")
        
        # Сохраняем данные Флориды
        if self.florida_data is not None:
            florida_file = self.output_dir / 'florida_data_final.xlsx'
            self.florida_data.to_excel(florida_file, index=False)
            print(f"✅ Данные Флориды сохранены: {florida_file}")
        
        # Сохраняем статистику
        if stats_results:
            stats_df = pd.DataFrame(stats_results).T
            stats_file = self.output_dir / 'florida_statistics_final.xlsx'
            stats_df.to_excel(stats_file)
            print(f"✅ Статистика сохранена: {stats_file}")
            
            # Создаем текстовый отчет
            report_file = self.output_dir / 'florida_final_report.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("ИТОГОВЫЙ АНАЛИЗ ДАННЫХ ФЛОРИДЫ\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Дата анализа: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Файл источника: {self.excel_file_path}\n")
                f.write(f"Количество записей с данными Флориды: {len(self.florida_data) if self.florida_data is not None else 0}\n\n")
                
                # Сводка по типам данных
                rate_cols = [col for col, stats in stats_results.items() if stats.get('тип') == 'ставка']
                percentage_cols = [col for col, stats in stats_results.items() if stats.get('тип') == 'процент']
                
                f.write("СВОДКА ПО ТИПАМ ДАННЫХ:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Колонки со ставками (СС): {len(rate_cols)}\n")
                f.write(f"Колонки с процентами: {len(percentage_cols)}\n\n")
                
                f.write("ДЕТАЛЬНАЯ СТАТИСТИКА:\n")
                f.write("-" * 30 + "\n")
                
                for col, stats in stats_results.items():
                    f.write(f"\nКолонка: {col}\n")
                    f.write(f"Тип: {stats.get('тип', 'неизвестно')}\n")
                    for stat, value in stats.items():
                        if stat != 'тип':
                            f.write(f"  {stat}: {value:.2f}\n")
                
                # Итоговые расчеты
                if rate_cols:
                    avg_rate = np.mean([stats_results[col]['среднее'] for col in rate_cols])
                    f.write(f"\n\nИТОГОВЫЕ РАСЧЕТЫ:\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Средняя ставка по всем колонкам: {avg_rate:,.2f} руб.\n")
                
                if percentage_cols:
                    avg_percentage = np.mean([stats_results[col]['среднее'] for col in percentage_cols])
                    f.write(f"Средний процент по всем колонкам: {avg_percentage:.2f}%\n")
                
                # Анализ по месяцам
                if self.florida_data is not None and 'sheet_name' in self.florida_data.columns:
                    f.write(f"\nАНАЛИЗ ПО МЕСЯЦАМ:\n")
                    f.write("-" * 30 + "\n")
                    month_counts = self.florida_data['sheet_name'].value_counts()
                    for month, count in month_counts.items():
                        f.write(f"{month}: {count} записей\n")
            
            print(f"✅ Итоговый отчет сохранен: {report_file}")
    
    def run_analysis(self):
        """Запуск полного анализа"""
        print("🚀 Запускаю финальный анализ данных Флориды...")
        print("=" * 70)
        
        # Загружаем данные из месячных листов
        if not self.load_monthly_sheets():
            return
        
        # Ищем Флориду и анализируем
        if not self.search_florida_and_analyze():
            print("❌ Анализ завершен - данные Флориды не найдены")
            return
        
        # Анализируем ставки и проценты
        stats_results = self.analyze_rates_and_percentages()
        
        # Создаем визуализации
        self.create_comprehensive_visualizations(stats_results)
        
        # Создаем итоговый отчет
        self.create_summary_report(stats_results)
        
        print("\n✅ Финальный анализ завершен!")
        print(f"📁 Результаты сохранены в папке: {self.output_dir}")


def main():
    """Основная функция"""
    # Путь к файлу Excel
    excel_file = "../../Табл выплаты 2025 (1).xlsx"
    
    # Проверяем существование файла
    if not os.path.exists(excel_file):
        print(f"❌ Файл не найден: {excel_file}")
        print("Убедитесь, что файл находится в корневой папке проекта")
        return
    
    # Создаем анализатор и запускаем анализ
    analyzer = FloridaFinalAnalyzer(excel_file)
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
