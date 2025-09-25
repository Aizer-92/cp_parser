#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализатор финансовых данных 2024-2025
Анализирует счета, создает прогнозы и выявляет проблемных клиентов
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Настройка для корректного отображения русского текста
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class FinancialAnalyzer:
    def __init__(self):
        self.data_2024 = None
        self.data_2025 = None
        self.merged_data = None
        self.analysis_results = {}
        
    def load_excel_file(self, file_path, year):
        """Загружает данные из Excel файла"""
        try:
            # Пытаемся прочитать все листы
            excel_file = pd.ExcelFile(file_path)
            print(f"Найдены листы в файле {file_path}: {excel_file.sheet_names}")
            
            # Читаем лист с нужным годом
            if str(year) in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=str(year))
                print(f"Загружено {len(df)} строк данных для {year} года")
            else:
                # Если лист с годом не найден, читаем первый лист
                df = pd.read_excel(file_path, sheet_name=0)
                print(f"Загружено {len(df)} строк данных для {year} года (первый лист)")
            
            print(f"Колонки: {list(df.columns)}")
            print(f"Первые 5 строк:")
            print(df.head())
            
            return df
            
        except Exception as e:
            print(f"Ошибка при загрузке файла {file_path}: {e}")
            return None
    
    def analyze_data_structure(self, df, year):
        """Анализирует структуру данных"""
        print(f"\n=== Анализ структуры данных {year} года ===")
        print(f"Размер данных: {df.shape}")
        print(f"Типы данных:")
        print(df.dtypes)
        print(f"\nОписательная статистика:")
        print(df.describe())
        print(f"\nПропущенные значения:")
        print(df.isnull().sum())
        
        return {
            'shape': df.shape,
            'dtypes': df.dtypes,
            'missing_values': df.isnull().sum().to_dict(),
            'columns': list(df.columns)
        }
    
    def identify_financial_columns(self, df):
        """Идентифицирует колонки с финансовыми данными"""
        financial_keywords = [
            'сумма', 'amount', 'цена', 'price', 'стоимость', 'cost',
            'оплата', 'payment', 'доход', 'revenue', 'прибыль', 'profit',
            'клиент', 'client', 'заказ', 'order', 'счет', 'invoice',
            'дата', 'date', 'месяц', 'month', 'год', 'year'
        ]
        
        financial_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in financial_keywords):
                financial_cols.append(col)
        
        print(f"Выявленные финансовые колонки: {financial_cols}")
        return financial_cols
    
    def analyze_client_performance(self, df, year):
        """Анализирует производительность клиентов"""
        print(f"\n=== Анализ клиентов {year} года ===")
        
        # Ищем колонку с клиентами
        client_cols = [col for col in df.columns if any(keyword in str(col).lower() 
                      for keyword in ['клиент', 'client', 'заказчик', 'покупатель', 'контрагент'])]
        
        if not client_cols:
            print("Колонка с клиентами не найдена")
            return None
        
        client_col = client_cols[0]
        print(f"Используем колонку клиентов: {client_col}")
        
        # Ищем колонку с суммами
        amount_cols = [col for col in df.columns if any(keyword in str(col).lower() 
                       for keyword in ['сумма', 'amount', 'цена', 'стоимость'])]
        
        if not amount_cols:
            print("Колонка с суммами не найдена")
            return None
        
        amount_col = amount_cols[0]
        print(f"Используем колонку сумм: {amount_col}")
        
        # Очищаем данные - убираем строки с пустыми суммами
        df_clean = df.dropna(subset=[amount_col])
        
        # Преобразуем суммы в числовой формат
        df_clean[amount_col] = pd.to_numeric(df_clean[amount_col], errors='coerce')
        df_clean = df_clean.dropna(subset=[amount_col])
        
        # Анализ по клиентам
        client_analysis = df_clean.groupby(client_col)[amount_col].agg([
            'count', 'sum', 'mean', 'std'
        ]).round(2)
        
        client_analysis.columns = ['Количество_заказов', 'Общая_сумма', 'Средний_чек', 'Стандартное_отклонение']
        client_analysis = client_analysis.sort_values('Общая_сумма', ascending=False)
        
        print(f"\nТоп-10 клиентов по общей сумме:")
        print(client_analysis.head(10))
        
        return client_analysis
    
    def create_forecast(self, data_2024, data_2025):
        """Создает прогноз на 2025 год"""
        print(f"\n=== Создание прогноза ===")
        
        # Здесь будет логика прогнозирования
        # Пока что базовая реализация
        
        forecast = {
            'method': 'Простой анализ трендов',
            'recommendations': []
        }
        
        return forecast
    
    def identify_problem_clients(self, client_analysis_2024, client_analysis_2025):
        """Выявляет проблемных клиентов"""
        print(f"\n=== Выявление проблемных клиентов ===")
        
        problem_clients = []
        
        if client_analysis_2024 is not None and client_analysis_2025 is not None:
            # Сравниваем клиентов между годами
            common_clients = set(client_analysis_2024.index) & set(client_analysis_2025.index)
            
            for client in common_clients:
                if client in client_analysis_2024.index and client in client_analysis_2025.index:
                    revenue_2024 = client_analysis_2024.loc[client, 'Общая_сумма']
                    revenue_2025 = client_analysis_2025.loc[client, 'Общая_сумма']
                    
                    if revenue_2024 > 0:
                        change_percent = ((revenue_2025 - revenue_2024) / revenue_2024) * 100
                        
                        if change_percent < -20:  # Снижение более чем на 20%
                            problem_clients.append({
                                'client': client,
                                'revenue_2024': revenue_2024,
                                'revenue_2025': revenue_2025,
                                'change_percent': change_percent,
                                'status': 'Критическое снижение'
                            })
                        elif change_percent < -10:  # Снижение на 10-20%
                            problem_clients.append({
                                'client': client,
                                'revenue_2024': revenue_2024,
                                'revenue_2025': revenue_2025,
                                'change_percent': change_percent,
                                'status': 'Снижение'
                            })
        
        return problem_clients
    
    def generate_detailed_report(self, client_analysis_2024, client_analysis_2025, problem_clients, forecast):
        """Генерирует детальный отчет"""
        report = f"""
# ФИНАНСОВЫЙ АНАЛИЗ 2024-2025

## Обзор
- Анализ проведен: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Данные 2024: {'Загружены' if self.data_2024 is not None else 'Не загружены'}
- Данные 2025: {'Загружены' if self.data_2025 is not None else 'Не загружены'}

## Анализ клиентов 2024 года
"""
        
        if client_analysis_2024 is not None:
            report += f"""
### Топ-10 клиентов 2024 года:
{client_analysis_2024.head(10).to_string()}

### Общая статистика 2024:
- Всего клиентов: {len(client_analysis_2024)}
- Общая сумма: {client_analysis_2024['Общая_сумма'].sum():,.2f}
- Средний чек: {client_analysis_2024['Средний_чек'].mean():,.2f}
"""
        else:
            report += "\nДанные за 2024 год не загружены\n"
        
        report += "\n## Анализ клиентов 2025 года\n"
        
        if client_analysis_2025 is not None:
            report += f"""
### Топ-10 клиентов 2025 года:
{client_analysis_2025.head(10).to_string()}

### Общая статистика 2025:
- Всего клиентов: {len(client_analysis_2025)}
- Общая сумма: {client_analysis_2025['Общая_сумма'].sum():,.2f}
- Средний чек: {client_analysis_2025['Средний_чек'].mean():,.2f}
"""
        else:
            report += "\nДанные за 2025 год не загружены\n"
        
        if problem_clients:
            report += "\n## 🚨 ПРОБЛЕМНЫЕ КЛИЕНТЫ (требуют внимания)\n"
            for client in problem_clients:
                report += f"""
### {client['client']}
- Статус: {client['status']}
- Доход 2024: {client['revenue_2024']:,.2f}
- Доход 2025: {client['revenue_2025']:,.2f}
- Изменение: {client['change_percent']:.1f}%
"""
        else:
            report += "\n## ✅ Проблемных клиентов не выявлено\n"
        
        report += f"""
## Рекомендации
1. Проанализируйте выявленных проблемных клиентов
2. Сосредоточьтесь на клиентах с наибольшим снижением доходов
3. Разработайте стратегию удержания ключевых клиентов
4. Создайте план работы с новыми клиентами

## Следующие шаги
- Детальный анализ по месяцам
- Сезонные тренды
- Прогноз на оставшуюся часть 2025 года
- Анализ эффективности менеджеров
"""
        return report

def main():
    print("=== ФИНАНСОВЫЙ АНАЛИЗАТОР 2024-2025 ===")
    
    analyzer = FinancialAnalyzer()
    
    # Загружаем данные из одного файла с разными листами
    file_path = "/Users/bakirovresad/Downloads/Reshad 1/Отчет счета май-сентябрь 2025 (1).xlsx"
    
    # Загружаем данные 2024 года
    analyzer.data_2024 = analyzer.load_excel_file(file_path, 2024)
    
    # Загружаем данные 2025 года
    analyzer.data_2025 = analyzer.load_excel_file(file_path, 2025)
    
    client_analysis_2024 = None
    client_analysis_2025 = None
    
    if analyzer.data_2024 is not None:
        analyzer.analyze_data_structure(analyzer.data_2024, 2024)
        financial_cols_2024 = analyzer.identify_financial_columns(analyzer.data_2024)
        client_analysis_2024 = analyzer.analyze_client_performance(analyzer.data_2024, 2024)
    
    if analyzer.data_2025 is not None:
        analyzer.analyze_data_structure(analyzer.data_2025, 2025)
        financial_cols_2025 = analyzer.identify_financial_columns(analyzer.data_2025)
        client_analysis_2025 = analyzer.analyze_client_performance(analyzer.data_2025, 2025)
    
    # Выявляем проблемных клиентов
    problem_clients = analyzer.identify_problem_clients(client_analysis_2024, client_analysis_2025)
    
    # Создаем прогноз
    forecast = analyzer.create_forecast(analyzer.data_2024, analyzer.data_2025)
    
    # Генерируем отчет
    report = analyzer.generate_detailed_report(client_analysis_2024, client_analysis_2025, problem_clients, forecast)
    print(report)
    
    # Сохраняем отчет
    with open("/Users/bakirovresad/Downloads/Reshad 1/projects/financial_analysis_2024_2025/analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\nАнализ завершен! Отчет сохранен в analysis_report.md")

if __name__ == "__main__":
    main()
