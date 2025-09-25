#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация итогового отчета с объединенными клиентами Яндекса
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
        date_str = str(date_str)
        if len(date_str) >= 10:
            date_part = date_str[:10]
            return pd.to_datetime(date_part, format='%d.%m.%Y', errors='coerce')
        return pd.NaT
    except:
        return pd.NaT

def unify_yandex_clients(df):
    """Объединяет все варианты Яндекса в одного контрагента"""
    df_unified = df.copy()
    
    yandex_variants = [
        'ООО "ЯНДЕКС"',
        'ООО "ЯНДЕКС.ЕДА"',
        'ООО "ЯНДЕКС МАРКЕТ"',
        'ООО "ЯНДЕКС ПЭЙ"',
        'ООО "ЯНДЕКС.ЛАВКА"',
        'ЯНДЕКС Китай',
        'ЯНДЕКС',
        'Яндекс',
        'yandex'
    ]
    
    for variant in yandex_variants:
        mask = df_unified['Контрагент'].str.contains(variant, case=False, na=False)
        df_unified.loc[mask, 'Контрагент'] = 'ООО "ЯНДЕКС" (объединенный)'
    
    return df_unified

def generate_unified_report():
    """Генерирует итоговый отчет с объединенными данными"""
    
    file_path = "/Users/bakirovresad/Downloads/Reshad 1/Отчет счета май-сентябрь 2025 (1).xlsx"
    
    # Загружаем и объединяем данные
    df_2024 = pd.read_excel(file_path, sheet_name='2024')
    df_2025 = pd.read_excel(file_path, sheet_name='2025')
    
    df_2024_unified = unify_yandex_clients(df_2024)
    df_2025_unified = unify_yandex_clients(df_2025)
    
    # Очистка данных
    for df in [df_2024_unified, df_2025_unified]:
        df['Сумма_число'] = df['Сумма'].apply(clean_amount)
        df['Дата_чистая'] = df['Дата и время'].apply(clean_date)
    
    # Фильтрация
    df_2024_clean = df_2024_unified.dropna(subset=['Сумма_число', 'Дата_чистая', 'Контрагент'])
    df_2024_clean = df_2024_clean[df_2024_clean['Сумма_число'] > 0]
    
    df_2025_clean = df_2025_unified.dropna(subset=['Сумма_число', 'Дата_чистая', 'Контрагент'])
    df_2025_clean = df_2025_clean[df_2025_clean['Сумма_число'] > 0]
    
    # Анализ данных
    total_2024 = df_2024_clean['Сумма_число'].sum()
    total_2025 = df_2025_clean['Сумма_число'].sum()
    growth_percent = ((total_2025 - total_2024) / total_2024) * 100
    
    # Клиенты
    clients_2024 = df_2024_clean.groupby('Контрагент')['Сумма_число'].sum().sort_values(ascending=False)
    clients_2025 = df_2025_clean.groupby('Контрагент')['Сумма_число'].sum().sort_values(ascending=False)
    
    # Месячный анализ 2025
    df_2025_clean['Месяц'] = df_2025_clean['Дата_чистая'].dt.month
    monthly_2025 = df_2025_clean.groupby('Месяц')['Сумма_число'].sum()
    
    # Прогноз
    avg_monthly = monthly_2025.mean()
    forecast_total = total_2025 + (avg_monthly * 3)
    
    # Анализ изменений клиентов
    common_clients = set(clients_2024.index) & set(clients_2025.index)
    client_changes = []
    
    for client in common_clients:
        revenue_2024 = clients_2024[client]
        revenue_2025 = clients_2025[client]
        if revenue_2024 > 0:
            change_percent = ((revenue_2025 - revenue_2024) / revenue_2024) * 100
            client_changes.append({
                'client': client,
                'revenue_2024': revenue_2024,
                'revenue_2025': revenue_2025,
                'change_percent': change_percent
            })
    
    client_changes.sort(key=lambda x: x['change_percent'])
    declining_clients = [c for c in client_changes if c['change_percent'] < -10]
    new_clients_2025 = set(clients_2025.index) - set(clients_2024.index)
    
    # Создаем отчет
    report = f"""
# 📊 ФИНАНСОВЫЙ АНАЛИЗ 2024-2025 (ОБЪЕДИНЕННЫЕ ДАННЫЕ)
## Итоговый отчет с унифицированными клиентами

**Дата анализа:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

---

## 🔄 ОБЪЕДИНЕНИЕ КЛИЕНТОВ

**Все варианты Яндекса объединены в одного контрагента:**
- ООО "ЯНДЕКС" 
- ООО "ЯНДЕКС.ЕДА"
- ООО "ЯНДЕКС МАРКЕТ"
- ООО "ЯНДЕКС ПЭЙ"
- ООО "ЯНДЕКС.ЛАВКА"
- ЯНДЕКС Китай

**Результат:** Более точный анализ крупнейшего клиента

---

## 🎯 КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ

| Показатель | 2024 год | 2025 год | Изменение |
|------------|----------|----------|-----------|
| **Общий доход** | {total_2024:,.0f} руб. | {total_2025:,.0f} руб. | **+{growth_percent:.1f}%** |
| **Количество клиентов** | {len(clients_2024)} | {len(clients_2025)} | +{len(clients_2025) - len(clients_2024)} |
| **Средний чек 2024** | {total_2024/len(df_2024_clean):,.0f} руб. | - | - |
| **Средний чек 2025** | - | {total_2025/len(df_2025_clean):,.0f} руб. | - |

---

## 🚨 КРИТИЧЕСКИ ВАЖНЫЕ КЛИЕНТЫ (требуют немедленного внимания)

### Клиенты с падающими показателями:
"""
    
    if declining_clients:
        for client in declining_clients:
            report += f"""
**{client['client']}**
- Доход 2024: {client['revenue_2024']:,.0f} руб.
- Доход 2025: {client['revenue_2025']:,.0f} руб.
- **Снижение: {client['change_percent']:.1f}%**
- ⚠️ **ДЕЙСТВИЯ:** Срочная встреча, анализ причин, план восстановления
"""
    else:
        report += "\n✅ Клиентов с критическим снижением не выявлено\n"
    
    # Новые крупные клиенты
    if new_clients_2025:
        new_clients_data = clients_2025[clients_2025.index.isin(new_clients_2025)].head(10)
        
        report += f"""
## 🆕 НОВЫЕ КРУПНЫЕ КЛИЕНТЫ 2025

Развивайте отношения с новыми клиентами:
"""
        for i, (client, amount) in enumerate(new_clients_data.items(), 1):
            report += f"{i}. **{client}**: {amount:,.0f} руб.\n"
    
    # Топ клиенты
    report += f"""
## 🏆 ТОП-10 КЛИЕНТОВ 2025 ГОДА (ОБЪЕДИНЕННЫЕ)

| № | Клиент | Доход (руб.) | Доля от общего |
|---|--------|--------------|----------------|
"""
    
    for i, (client, amount) in enumerate(clients_2025.head(10).items(), 1):
        share = (amount / total_2025) * 100
        report += f"| {i} | {client} | {amount:,.0f} | {share:.1f}% |\n"
    
    # Месячный анализ
    month_names = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 
                   6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь'}
    
    report += f"""
## 📈 АНАЛИЗ ПО МЕСЯЦАМ 2025

| Месяц | Доход (руб.) | Доля |
|-------|--------------|------|
"""
    
    for month, amount in monthly_2025.items():
        share = (amount / total_2025) * 100
        report += f"| {month_names.get(month, month)} | {amount:,.0f} | {share:.1f}% |\n"
    
    # Прогноз
    report += f"""
## 🔮 ПРОГНОЗ НА 2025 ГОД

- **Средний месячный доход:** {avg_monthly:,.0f} руб.
- **Текущий доход (янв-сен):** {total_2025:,.0f} руб.
- **Прогноз на оставшиеся месяцы:** {avg_monthly * 3:,.0f} руб.
- **🎯 ПРОГНОЗ НА ВЕСЬ 2025 ГОД:** **{forecast_total:,.0f} руб.**

---

## 📋 РЕКОМЕНДАЦИИ

### Немедленные действия:
"""
    
    if declining_clients:
        report += f"1. **СРОЧНО** провести встречи с {len(declining_clients)} клиентами с падающими показателями\n"
        report += "2. Разработать план восстановления отношений\n"
        report += "3. Проанализировать причины снижения доходов\n"
    
    report += f"""
4. Развивать отношения с {len(new_clients_2025)} новыми клиентами
5. Поддерживать работу с топ-10 клиентами (дают {sum(clients_2025.head(10).values)/total_2025*100:.1f}% дохода)

### Особое внимание к Яндексу:
- **2024 год:** {clients_2024.get('ООО "ЯНДЕКС" (объединенный)', 0):,.0f} руб. ({clients_2024.get('ООО "ЯНДЕКС" (объединенный)', 0)/total_2024*100:.1f}% от оборота)
- **2025 год:** {clients_2025.get('ООО "ЯНДЕКС" (объединенный)', 0):,.0f} руб. ({clients_2025.get('ООО "ЯНДЕКС" (объединенный)', 0)/total_2025*100:.1f}% от оборота)
- **Изменение:** {client_changes[0]['change_percent']:.1f}% (если Яндекс в списке изменений)

### Стратегические задачи:
- Анализ сезонности (пик в июле-августе)
- Диверсификация клиентской базы
- Развитие долгосрочных отношений
- Мониторинг эффективности менеджеров

---

## 🎯 ЦЕЛИ НА ОСТАВШИЙСЯ 2025 ГОД

- **Минимальная цель:** {forecast_total * 0.9:,.0f} руб. (90% от прогноза)
- **Целевая цель:** {forecast_total:,.0f} руб. (базовый прогноз)
- **Амбициозная цель:** {forecast_total * 1.1:,.0f} руб. (110% от прогноза)

---

**Отчет подготовлен:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
**Версия:** Объединенные данные клиентов
"""
    
    return report

if __name__ == "__main__":
    report = generate_unified_report()
    
    # Сохраняем отчет
    with open("/Users/bakirovresad/Downloads/Reshad 1/projects/financial_analysis_2024_2025/UNIFIED_FINAL_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("✅ Обновленный отчет с объединенными данными сохранен в UNIFIED_FINAL_REPORT.md")
    print("\n" + "="*50)
    print(report)
