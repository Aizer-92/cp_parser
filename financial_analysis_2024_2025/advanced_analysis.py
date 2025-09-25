#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный анализ финансовых данных 2024-2025
Создает визуализации и детальные прогнозы
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

class AdvancedFinancialAnalyzer:
    def __init__(self):
        self.data_2024 = None
        self.data_2025 = None
        self.analysis_results = {}
        
    def load_data(self, file_path):
        """Загружает данные из Excel файла"""
        try:
            # Загружаем данные 2024 года
            self.data_2024 = pd.read_excel(file_path, sheet_name='2024')
            print(f"Загружено {len(self.data_2024)} строк данных за 2024 год")
            
            # Загружаем данные 2025 года
            self.data_2025 = pd.read_excel(file_path, sheet_name='2025')
            print(f"Загружено {len(self.data_2025)} строк данных за 2025 год")
            
            return True
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return False
    
    def clean_data(self, df, year):
        """Очищает и подготавливает данные"""
        # Убираем строки с пустыми суммами
        df_clean = df.dropna(subset=['Сумма'])
        
        # Преобразуем суммы в числовой формат
        df_clean['Сумма'] = pd.to_numeric(df_clean['Сумма'], errors='coerce')
        df_clean = df_clean.dropna(subset=['Сумма'])
        
        # Преобразуем даты
        df_clean['Дата'] = pd.to_datetime(df_clean['Дата и время'], errors='coerce')
        df_clean = df_clean.dropna(subset=['Дата'])
        
        # Добавляем месяц и год
        df_clean['Месяц'] = df_clean['Дата'].dt.month
        df_clean['Год'] = df_clean['Дата'].dt.year
        
        print(f"Очищено данных за {year} год: {len(df_clean)} строк")
        return df_clean
    
    def analyze_growth(self):
        """Анализирует рост бизнеса"""
        print("\n=== АНАЛИЗ РОСТА БИЗНЕСА ===")
        
        # Очищаем данные
        data_2024_clean = self.clean_data(self.data_2024, 2024)
        data_2025_clean = self.clean_data(self.data_2025, 2025)
        
        # Общие показатели
        total_2024 = data_2024_clean['Сумма'].sum()
        total_2025 = data_2025_clean['Сумма'].sum()
        
        growth_percent = ((total_2025 - total_2024) / total_2024) * 100
        
        print(f"Общий доход 2024: {total_2024:,.2f}")
        print(f"Общий доход 2025: {total_2025:,.2f}")
        print(f"Рост: {growth_percent:.1f}%")
        
        # Анализ по месяцам
        monthly_2024 = data_2024_clean.groupby('Месяц')['Сумма'].sum()
        monthly_2025 = data_2025_clean.groupby('Месяц')['Сумма'].sum()
        
        print(f"\nДоходы по месяцам 2024:")
        for month, amount in monthly_2024.items():
            print(f"  {month}: {amount:,.2f}")
        
        print(f"\nДоходы по месяцам 2025:")
        for month, amount in monthly_2025.items():
            print(f"  {month}: {amount:,.2f}")
        
        return {
            'total_2024': total_2024,
            'total_2025': total_2025,
            'growth_percent': growth_percent,
            'monthly_2024': monthly_2024,
            'monthly_2025': monthly_2025
        }
    
    def analyze_clients(self):
        """Анализирует клиентскую базу"""
        print("\n=== АНАЛИЗ КЛИЕНТСКОЙ БАЗЫ ===")
        
        # Очищаем данные
        data_2024_clean = self.clean_data(self.data_2024, 2024)
        data_2025_clean = self.clean_data(self.data_2025, 2025)
        
        # Анализ клиентов 2024
        clients_2024 = data_2024_clean.groupby('Контрагент')['Сумма'].agg(['count', 'sum', 'mean']).round(2)
        clients_2024.columns = ['Заказов', 'Общая_сумма', 'Средний_чек']
        clients_2024 = clients_2024.sort_values('Общая_сумма', ascending=False)
        
        # Анализ клиентов 2025
        clients_2025 = data_2025_clean.groupby('Контрагент')['Сумма'].agg(['count', 'sum', 'mean']).round(2)
        clients_2025.columns = ['Заказов', 'Общая_сумма', 'Средний_чек']
        clients_2025 = clients_2025.sort_values('Общая_сумма', ascending=False)
        
        # Находим общих клиентов
        common_clients = set(clients_2024.index) & set(clients_2025.index)
        new_clients_2025 = set(clients_2025.index) - set(clients_2024.index)
        lost_clients_2024 = set(clients_2024.index) - set(clients_2025.index)
        
        print(f"Клиентов в 2024: {len(clients_2024)}")
        print(f"Клиентов в 2025: {len(clients_2025)}")
        print(f"Общих клиентов: {len(common_clients)}")
        print(f"Новых клиентов в 2025: {len(new_clients_2025)}")
        print(f"Потерянных клиентов: {len(lost_clients_2024)}")
        
        # Анализ изменений у общих клиентов
        client_changes = []
        for client in common_clients:
            if client in clients_2024.index and client in clients_2025.index:
                revenue_2024 = clients_2024.loc[client, 'Общая_сумма']
                revenue_2025 = clients_2025.loc[client, 'Общая_сумма']
                
                if revenue_2024 > 0:
                    change_percent = ((revenue_2025 - revenue_2024) / revenue_2024) * 100
                    client_changes.append({
                        'client': client,
                        'revenue_2024': revenue_2024,
                        'revenue_2025': revenue_2025,
                        'change_percent': change_percent
                    })
        
        # Сортируем по изменению
        client_changes.sort(key=lambda x: x['change_percent'])
        
        print(f"\nКлиенты с наибольшим снижением доходов:")
        for client in client_changes[:5]:
            print(f"  {client['client']}: {client['change_percent']:.1f}%")
        
        print(f"\nКлиенты с наибольшим ростом доходов:")
        for client in client_changes[-5:]:
            print(f"  {client['client']}: {client['change_percent']:.1f}%")
        
        return {
            'clients_2024': clients_2024,
            'clients_2025': clients_2025,
            'common_clients': common_clients,
            'new_clients_2025': new_clients_2025,
            'lost_clients_2024': lost_clients_2024,
            'client_changes': client_changes
        }
    
    def create_forecast(self):
        """Создает прогноз на оставшуюся часть 2025 года"""
        print("\n=== ПРОГНОЗ НА 2025 ГОД ===")
        
        # Очищаем данные
        data_2025_clean = self.clean_data(self.data_2025, 2025)
        
        # Анализ по месяцам
        monthly_data = data_2025_clean.groupby('Месяц')['Сумма'].sum()
        
        # Средний месячный доход
        avg_monthly = monthly_data.mean()
        
        # Прогноз на оставшиеся месяцы (октябрь-декабрь)
        remaining_months = 3
        forecast_remaining = avg_monthly * remaining_months
        
        # Общий прогноз на год
        current_total = monthly_data.sum()
        forecast_total = current_total + forecast_remaining
        
        print(f"Средний месячный доход: {avg_monthly:,.2f}")
        print(f"Текущий доход (январь-сентябрь): {current_total:,.2f}")
        print(f"Прогноз на оставшиеся месяцы: {forecast_remaining:,.2f}")
        print(f"Прогноз на весь 2025 год: {forecast_total:,.2f}")
        
        return {
            'avg_monthly': avg_monthly,
            'current_total': current_total,
            'forecast_remaining': forecast_remaining,
            'forecast_total': forecast_total
        }
    
    def identify_priority_clients(self, client_analysis):
        """Выявляет приоритетных клиентов для работы"""
        print("\n=== ПРИОРИТЕТНЫЕ КЛИЕНТЫ ===")
        
        clients_2025 = client_analysis['clients_2025']
        client_changes = client_analysis['client_changes']
        
        # Топ-10 клиентов по доходу 2025
        top_clients = clients_2025.head(10)
        print("Топ-10 клиентов по доходу 2025:")
        for i, (client, data) in enumerate(top_clients.iterrows(), 1):
            print(f"{i:2d}. {client}: {data['Общая_сумма']:,.2f}")
        
        # Клиенты с падающими показателями
        declining_clients = [c for c in client_changes if c['change_percent'] < -10]
        if declining_clients:
            print(f"\nКлиенты с падающими показателями (снижение >10%):")
            for client in declining_clients:
                print(f"  {client['client']}: {client['change_percent']:.1f}%")
        
        # Новые крупные клиенты
        new_clients = client_analysis['new_clients_2025']
        if new_clients:
            new_clients_data = clients_2025[clients_2025.index.isin(new_clients)]
            new_clients_data = new_clients_data.sort_values('Общая_сумма', ascending=False)
            
            print(f"\nНовые крупные клиенты:")
            for client, data in new_clients_data.head(5).iterrows():
                print(f"  {client}: {data['Общая_сумма']:,.2f}")
        
        return {
            'top_clients': top_clients,
            'declining_clients': declining_clients,
            'new_clients': new_clients_data if new_clients else None
        }
    
    def generate_recommendations(self, growth_analysis, client_analysis, forecast):
        """Генерирует рекомендации"""
        print("\n=== РЕКОМЕНДАЦИИ ===")
        
        recommendations = []
        
        # Анализ роста
        if growth_analysis['growth_percent'] > 50:
            recommendations.append("✅ Отличный рост! Продолжайте текущую стратегию")
        elif growth_analysis['growth_percent'] > 0:
            recommendations.append("⚠️ Рост есть, но можно ускорить")
        else:
            recommendations.append("🚨 Снижение доходов! Требуются срочные меры")
        
        # Анализ клиентов
        declining_count = len([c for c in client_analysis['client_changes'] if c['change_percent'] < -10])
        if declining_count > 0:
            recommendations.append(f"🎯 Сосредоточьтесь на {declining_count} клиентах с падающими показателями")
        
        new_clients_count = len(client_analysis['new_clients_2025'])
        if new_clients_count > 0:
            recommendations.append(f"🆕 Развивайте отношения с {new_clients_count} новыми клиентами")
        
        # Прогноз
        if forecast['forecast_total'] > growth_analysis['total_2024'] * 1.5:
            recommendations.append("📈 Прогноз показывает хорошие перспективы на конец года")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        return recommendations

def main():
    print("=== РАСШИРЕННЫЙ ФИНАНСОВЫЙ АНАЛИЗ 2024-2025 ===")
    
    analyzer = AdvancedFinancialAnalyzer()
    
    # Загружаем данные
    file_path = "/Users/bakirovresad/Downloads/Reshad 1/Отчет счета май-сентябрь 2025 (1).xlsx"
    if not analyzer.load_data(file_path):
        return
    
    # Анализируем рост
    growth_analysis = analyzer.analyze_growth()
    
    # Анализируем клиентов
    client_analysis = analyzer.analyze_clients()
    
    # Создаем прогноз
    forecast = analyzer.create_forecast()
    
    # Выявляем приоритетных клиентов
    priority_clients = analyzer.identify_priority_clients(client_analysis)
    
    # Генерируем рекомендации
    recommendations = analyzer.generate_recommendations(growth_analysis, client_analysis, forecast)
    
    print("\n=== АНАЛИЗ ЗАВЕРШЕН ===")

if __name__ == "__main__":
    main()
