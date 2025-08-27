#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный анализ таблицы выплат 2025 - поиск данных по Флориде во всех листах
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
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']

class FloridaAnalyzerEnhanced:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.all_data = {}
        self.florida_data = None
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_all_sheets(self):
        """Загрузка данных из всех листов Excel файла"""
        print("📊 Загружаю данные из всех листов Excel файла...")
        
        try:
            # Загружаем все листы
            excel_file = pd.ExcelFile(self.excel_file_path)
            print(f"📋 Найдены листы: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                try:
                    data = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
                    self.all_data[sheet_name] = data
                    print(f"✅ Лист '{sheet_name}': {data.shape[0]} строк, {data.shape[1]} колонок")
                    
                    # Показываем первые строки для понимания структуры
                    if data.shape[0] > 0:
                        print(f"   Первые колонки: {list(data.columns[:5])}")
                        
                except Exception as e:
                    print(f"❌ Ошибка при загрузке листа '{sheet_name}': {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке данных: {e}")
            return False
    
    def search_florida_all_sheets(self):
        """Поиск данных по Флориде во всех листах"""
        print("\n🔍 Ищу данные по Флориде во всех листах...")
        
        if not self.all_data:
            print("❌ Данные не загружены")
            return False
        
        # Ищем Флориду в разных вариантах написания
        florida_patterns = ['флорида', 'florida', 'Флорида', 'Florida', 'ФЛОРИДА', 'флорид', 'Флорид']
        
        florida_found = []
        
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
                                
                                # Показываем найденные строки
                                for idx, row in found_rows.iterrows():
                                    print(f"    Строка {idx}: {row.to_dict()}")
                                
                                florida_found.append({
                                    'sheet': sheet_name,
                                    'column': col,
                                    'rows': found_rows,
                                    'pattern': pattern
                                })
                        except Exception as e:
                            continue
        
        if florida_found:
            print(f"\n✅ Найдено {len(florida_found)} совпадений с Флоридой")
            
            # Объединяем все найденные данные
            all_florida_rows = []
            for found in florida_found:
                all_florida_rows.append(found['rows'])
            
            if all_florida_rows:
                self.florida_data = pd.concat(all_florida_rows, ignore_index=True)
                print(f"📋 Объединенные данные Флориды: {len(self.florida_data)} строк")
                print(self.florida_data)
            
            return True
        else:
            print("❌ Данные по Флориде не найдены ни в одном листе")
            return False
    
    def analyze_percentages(self):
        """Анализ процентных данных"""
        if self.florida_data is None or len(self.florida_data) == 0:
            print("❌ Нет данных Флориды для анализа")
            return
        
        print("\n📊 Анализирую процентные данные...")
        
        # Ищем колонки с процентами
        percentage_columns = []
        for col in self.florida_data.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['процент', 'percent', '%', 'ставка', 'rate', 'комиссия', 'commission']):
                percentage_columns.append(col)
        
        print(f"📈 Найдены колонки с процентами: {percentage_columns}")
        
        if not percentage_columns:
            # Если не найдены специальные колонки, ищем числовые
            numeric_columns = self.florida_data.select_dtypes(include=[np.number]).columns.tolist()
            print(f"📊 Числовые колонки: {numeric_columns}")
            percentage_columns = numeric_columns
        
        results = {}
        
        for col in percentage_columns:
            try:
                # Преобразуем в числовой формат
                values = pd.to_numeric(self.florida_data[col], errors='coerce')
                values = values.dropna()
                
                if len(values) > 0:
                    stats = {
                        'среднее': values.mean(),
                        'медиана': values.median(),
                        'мин': values.min(),
                        'макс': values.max(),
                        'стандартное_отклонение': values.std(),
                        'количество_значений': len(values)
                    }
                    results[col] = stats
                    
                    print(f"\n📊 Статистика по колонке '{col}':")
                    for stat, value in stats.items():
                        print(f"  {stat}: {value:.2f}")
                    
            except Exception as e:
                print(f"❌ Ошибка при анализе колонки '{col}': {e}")
        
        return results
    
    def create_visualizations(self, stats_results):
        """Создание визуализаций"""
        if not stats_results:
            return
        
        print("\n📈 Создаю визуализации...")
        
        # График средних значений
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Анализ данных Флориды', fontsize=16, fontweight='bold')
        
        # График 1: Средние значения
        if stats_results:
            cols = list(stats_results.keys())
            means = [stats_results[col]['среднее'] for col in cols]
            
            axes[0, 0].bar(range(len(cols)), means, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('Средние значения по колонкам')
            axes[0, 0].set_xticks(range(len(cols)))
            axes[0, 0].set_xticklabels(cols, rotation=45, ha='right')
            axes[0, 0].set_ylabel('Значение')
            
            # Добавляем значения на столбцы
            for i, v in enumerate(means):
                axes[0, 0].text(i, v + max(means)*0.01, f'{v:.2f}', 
                               ha='center', va='bottom', fontweight='bold')
        
        # График 2: Распределение значений (если есть данные)
        if self.florida_data is not None and len(self.florida_data) > 0:
            numeric_cols = self.florida_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                values = pd.to_numeric(self.florida_data[col], errors='coerce').dropna()
                if len(values) > 0:
                    axes[0, 1].hist(values, bins=min(10, len(values)), color='lightgreen', alpha=0.7)
                    axes[0, 1].set_title(f'Распределение значений: {col}')
                    axes[0, 1].set_xlabel('Значение')
                    axes[0, 1].set_ylabel('Частота')
        
        # График 3: Сравнение мин/макс
        if stats_results:
            cols = list(stats_results.keys())
            mins = [stats_results[col]['мин'] for col in cols]
            maxs = [stats_results[col]['макс'] for col in cols]
            
            x = np.arange(len(cols))
            width = 0.35
            
            axes[1, 0].bar(x - width/2, mins, width, label='Минимум', color='lightcoral', alpha=0.7)
            axes[1, 0].bar(x + width/2, maxs, width, label='Максимум', color='lightblue', alpha=0.7)
            axes[1, 0].set_title('Минимальные и максимальные значения')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(cols, rotation=45, ha='right')
            axes[1, 0].legend()
        
        # График 4: Количество значений
        if stats_results:
            cols = list(stats_results.keys())
            counts = [stats_results[col]['количество_значений'] for col in cols]
            
            axes[1, 1].pie(counts, labels=cols, autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title('Распределение количества значений')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'florida_analysis_enhanced.png', dpi=300, bbox_inches='tight')
        print(f"✅ График сохранен: {self.output_dir / 'florida_analysis_enhanced.png'}")
        plt.show()
    
    def save_results(self, stats_results):
        """Сохранение результатов анализа"""
        print("\n💾 Сохраняю результаты...")
        
        # Сохраняем данные Флориды
        if self.florida_data is not None:
            florida_file = self.output_dir / 'florida_data_enhanced.xlsx'
            self.florida_data.to_excel(florida_file, index=False)
            print(f"✅ Данные Флориды сохранены: {florida_file}")
        
        # Сохраняем статистику
        if stats_results:
            stats_df = pd.DataFrame(stats_results).T
            stats_file = self.output_dir / 'florida_statistics_enhanced.xlsx'
            stats_df.to_excel(stats_file)
            print(f"✅ Статистика сохранена: {stats_file}")
            
            # Создаем текстовый отчет
            report_file = self.output_dir / 'florida_analysis_report_enhanced.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("АНАЛИЗ ДАННЫХ ФЛОРИДЫ (УЛУЧШЕННАЯ ВЕРСИЯ)\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Дата анализа: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Файл источника: {self.excel_file_path}\n")
                f.write(f"Количество строк с данными Флориды: {len(self.florida_data) if self.florida_data is not None else 0}\n\n")
                
                f.write("СТАТИСТИКА ПО КОЛОНКАМ:\n")
                f.write("-" * 30 + "\n")
                
                for col, stats in stats_results.items():
                    f.write(f"\nКолонка: {col}\n")
                    for stat, value in stats.items():
                        f.write(f"  {stat}: {value:.2f}\n")
                
                if stats_results:
                    f.write(f"\n\nСредний процент по всем колонкам: {np.mean([stats['среднее'] for stats in stats_results.values()]):.2f}%\n")
            
            print(f"✅ Отчет сохранен: {report_file}")
    
    def run_analysis(self):
        """Запуск полного анализа"""
        print("🚀 Запускаю улучшенный анализ данных Флориды...")
        print("=" * 70)
        
        # Загружаем данные из всех листов
        if not self.load_all_sheets():
            return
        
        # Ищем Флориду во всех листах
        if not self.search_florida_all_sheets():
            print("❌ Анализ завершен - данные Флориды не найдены")
            return
        
        # Анализируем проценты
        stats_results = self.analyze_percentages()
        
        # Создаем визуализации
        self.create_visualizations(stats_results)
        
        # Сохраняем результаты
        self.save_results(stats_results)
        
        print("\n✅ Анализ завершен!")
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
    analyzer = FloridaAnalyzerEnhanced(excel_file)
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
