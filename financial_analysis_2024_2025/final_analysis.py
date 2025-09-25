#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальный анализ финансовых данных 2024-2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def clean_amount(amount_str):
    """Очищает и преобразует сумму в число"""
    if pd.isna(amount_str) or amount_str == '':
        return np.nan
    
    # Убираем пробелы и заменяем запятую на точку
    amount_str = str(amount_str).replace(' ', '').replace(',', '.')
    
    try:
        return float(amount_str)
    except:
        return np.nan

def clean_date(date_str):
    """Очищает и преобразует дату"""
    if pd.isna(date_str) or date_str == '':
        return pd.NaT
    
    try:
        # Формат: 19.08.202416:21
        date_str = str(date_str)
        if len(date_str) >= 10:
            date_part = date_str[:10]  # Берем только дату
            return pd.to_datetime(date_part, format='%d.%m.%Y', errors='coerce')
        return pd.NaT
    except:
        return pd.NaT

def analyze_financial_data():
    """Основной анализ финансовых данных"""
    print("=== ФИНАНСОВЫЙ АНАЛИЗ 2024-2025 ===\n")
    
    file_path = "/Users/bakirovresad/Downloads/Reshad 1/Отчет счета май-сентябрь 2025 (1).xlsx"
    
    # Загружаем данные
    df_2024 = pd.read_excel(file_path, sheet_name='2024')
    df_2025 = pd.read_excel(file_path, sheet_name='2025')
    
    print(f"Загружено данных 2024: {len(df_2024)} строк")
    print(f"Загружено данных 2025: {len(df_2025)} строк")
    
    # Очищаем данные 2024
    print("\n=== ОЧИСТКА ДАННЫХ 2024 ===")
    df_2024_clean = df_2024.copy()
    df_2024_clean['Сумма_число'] = df_2024_clean['Сумма'].apply(clean_amount)
    df_2024_clean['Дата_чистая'] = df_2024_clean['Дата и время'].apply(clean_date)
    
    # Убираем строки с пустыми суммами или датами
    df_2024_clean = df_2024_clean.dropna(subset=['Сумма_число', 'Дата_чистая', 'Контрагент'])
    df_2024_clean = df_2024_clean[df_2024_clean['Сумма_число'] > 0]
    
    print(f"После очистки 2024: {len(df_2024_clean)} строк")
    
    # Очищаем данные 2025
    print("\n=== ОЧИСТКА ДАННЫХ 2025 ===")
    df_2025_clean = df_2025.copy()
    df_2025_clean['Сумма_число'] = df_2025_clean['Сумма'].apply(clean_amount)
    df_2025_clean['Дата_чистая'] = df_2025_clean['Дата и время'].apply(clean_date)
    
    # Убираем строки с пустыми суммами или датами
    df_2025_clean = df_2025_clean.dropna(subset=['Сумма_число', 'Дата_чистая', 'Контрагент'])
    df_2025_clean = df_2025_clean[df_2025_clean['Сумма_число'] > 0]
    
    print(f"После очистки 2025: {len(df_2025_clean)} строк")
    
    # Анализ роста
    print("\n=== АНАЛИЗ РОСТА ===")
    total_2024 = df_2024_clean['Сумма_число'].sum()
    total_2025 = df_2025_clean['Сумма_число'].sum()
    growth_percent = ((total_2025 - total_2024) / total_2024) * 100
    
    print(f"Общий доход 2024: {total_2024:,.2f} руб.")
    print(f"Общий доход 2025: {total_2025:,.2f} руб.")
    print(f"Рост: {growth_percent:.1f}%")
    
    # Анализ клиентов 2024
    print("\n=== ТОП-10 КЛИЕНТОВ 2024 ===")
    clients_2024 = df_2024_clean.groupby('Контрагент')['Сумма_число'].agg(['count', 'sum', 'mean']).round(2)
    clients_2024.columns = ['Заказов', 'Общая_сумма', 'Средний_чек']
    clients_2024 = clients_2024.sort_values('Общая_сумма', ascending=False)
    
    for i, (client, data) in enumerate(clients_2024.head(10).iterrows(), 1):
        print(f"{i:2d}. {client}: {data['Общая_сумма']:,.2f} руб. ({data['Заказов']} заказов)")
    
    # Анализ клиентов 2025
    print("\n=== ТОП-10 КЛИЕНТОВ 2025 ===")
    clients_2025 = df_2025_clean.groupby('Контрагент')['Сумма_число'].agg(['count', 'sum', 'mean']).round(2)
    clients_2025.columns = ['Заказов', 'Общая_сумма', 'Средний_чек']
    clients_2025 = clients_2025.sort_values('Общая_сумма', ascending=False)
    
    for i, (client, data) in enumerate(clients_2025.head(10).iterrows(), 1):
        print(f"{i:2d}. {client}: {data['Общая_сумма']:,.2f} руб. ({data['Заказов']} заказов)")
    
    # Сравнение клиентов
    print("\n=== СРАВНЕНИЕ КЛИЕНТОВ ===")
    common_clients = set(clients_2024.index) & set(clients_2025.index)
    new_clients_2025 = set(clients_2025.index) - set(clients_2024.index)
    lost_clients_2024 = set(clients_2024.index) - set(clients_2025.index)
    
    print(f"Общих клиентов: {len(common_clients)}")
    print(f"Новых клиентов в 2025: {len(new_clients_2025)}")
    print(f"Потерянных клиентов: {len(lost_clients_2024)}")
    
    # Анализ изменений у общих клиентов
    print("\n=== ИЗМЕНЕНИЯ У ОБЩИХ КЛИЕНТОВ ===")
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
    
    print("Клиенты с наибольшим снижением доходов:")
    for client in client_changes[:5]:
        print(f"  {client['client']}: {client['change_percent']:.1f}% ({client['revenue_2024']:,.0f} → {client['revenue_2025']:,.0f})")
    
    print("\nКлиенты с наибольшим ростом доходов:")
    for client in client_changes[-5:]:
        print(f"  {client['client']}: {client['change_percent']:.1f}% ({client['revenue_2024']:,.0f} → {client['revenue_2025']:,.0f})")
    
    # Анализ по месяцам 2025
    print("\n=== АНАЛИЗ ПО МЕСЯЦАМ 2025 ===")
    df_2025_clean['Месяц'] = df_2025_clean['Дата_чистая'].dt.month
    monthly_2025 = df_2025_clean.groupby('Месяц')['Сумма_число'].sum()
    
    month_names = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 
                   6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь'}
    
    for month, amount in monthly_2025.items():
        print(f"  {month_names.get(month, month)}: {amount:,.2f} руб.")
    
    # Прогноз на 2025
    print("\n=== ПРОГНОЗ НА 2025 ГОД ===")
    avg_monthly = monthly_2025.mean()
    current_total = monthly_2025.sum()
    remaining_months = 3  # Октябрь-декабрь
    forecast_remaining = avg_monthly * remaining_months
    forecast_total = current_total + forecast_remaining
    
    print(f"Средний месячный доход: {avg_monthly:,.2f} руб.")
    print(f"Текущий доход (январь-сентябрь): {current_total:,.2f} руб.")
    print(f"Прогноз на оставшиеся месяцы: {forecast_remaining:,.2f} руб.")
    print(f"Прогноз на весь 2025 год: {forecast_total:,.2f} руб.")
    
    # Рекомендации
    print("\n=== РЕКОМЕНДАЦИИ ===")
    
    # Клиенты для работы
    declining_clients = [c for c in client_changes if c['change_percent'] < -10]
    if declining_clients:
        print(f"🚨 КРИТИЧЕСКИ ВАЖНО: Работайте с {len(declining_clients)} клиентами с падающими показателями:")
        for client in declining_clients:
            print(f"   - {client['client']}: снижение на {client['change_percent']:.1f}%")
    
    # Новые крупные клиенты
    if new_clients_2025:
        new_clients_data = clients_2025[clients_2025.index.isin(new_clients_2025)]
        new_clients_data = new_clients_data.sort_values('Общая_сумма', ascending=False)
        
        print(f"\n🆕 Развивайте отношения с новыми крупными клиентами:")
        for client, data in new_clients_data.head(5).iterrows():
            print(f"   - {client}: {data['Общая_сумма']:,.2f} руб.")
    
    # Общие рекомендации
    if growth_percent > 50:
        print(f"\n✅ Отличный рост {growth_percent:.1f}%! Продолжайте текущую стратегию")
    elif growth_percent > 0:
        print(f"\n⚠️ Рост {growth_percent:.1f}% есть, но можно ускорить")
    else:
        print(f"\n🚨 Снижение доходов на {abs(growth_percent):.1f}%! Требуются срочные меры")
    
    # Анализ менеджеров
    print("\n=== АНАЛИЗ МЕНЕДЖЕРОВ 2025 ===")
    managers_2025 = df_2025_clean.groupby('Менеджер')['Сумма_число'].agg(['count', 'sum', 'mean']).round(2)
    managers_2025.columns = ['Заказов', 'Общая_сумма', 'Средний_чек']
    managers_2025 = managers_2025.sort_values('Общая_сумма', ascending=False)
    
    for manager, data in managers_2025.iterrows():
        if pd.notna(manager):
            print(f"  {manager}: {data['Общая_сумма']:,.2f} руб. ({data['Заказов']} заказов)")
    
    return {
        'total_2024': total_2024,
        'total_2025': total_2025,
        'growth_percent': growth_percent,
        'clients_2024': clients_2024,
        'clients_2025': clients_2025,
        'declining_clients': declining_clients,
        'new_clients': new_clients_2025,
        'forecast_total': forecast_total
    }

if __name__ == "__main__":
    results = analyze_financial_data()
    print("\n=== АНАЛИЗ ЗАВЕРШЕН ===")
