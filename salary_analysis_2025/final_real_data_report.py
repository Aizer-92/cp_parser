#!/usr/bin/env python3
"""
Финальный отчет на основе реальных данных из сводных листов
"""

import pandas as pd
from datetime import datetime

def generate_final_real_data_report():
    """Генерирует финальный отчет на основе реальных данных"""
    
    print("🎯 ФИНАЛЬНЫЙ ОТЧЕТ НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ")
    print("=" * 70)
    print("📊 Данные из сводных листов Excel файла")
    print("=" * 70)
    
    # Данные Артема Василевского (из листа "Сводная по зп")
    print("\n👤 АРТЕМ ВАСИЛЕВСКИЙ")
    print("-" * 50)
    print("💼 Должность: Руководитель отдела по работе с Китаем")
    print("📊 Источник данных: Лист 'Сводная по зп'")
    print("📅 Период: Июнь - Декабрь 2024")
    
    # Реальные данные Артема
    artem_total = 1918268
    artem_monthly_data = {
        'Июнь': 243406,
        'Июль': 284179,
        'Август': 323759,
        'Сентябрь': 363819,
        'Октябрь': 328727,
        'Ноябрь': 374378,
        'Декабрь': 458225
    }
    
    months_count = len(artem_monthly_data)
    avg_monthly_artem = artem_total / months_count
    annual_artem = avg_monthly_artem * 12
    
    print(f"💰 Общий доход за {months_count} месяцев: {artem_total:,.2f} руб.")
    print(f"📅 Месячные данные: {artem_monthly_data}")
    print(f"📊 Среднемесячно: {avg_monthly_artem:,.2f} руб.")
    print(f"🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {annual_artem:,.2f} руб.")
    
    # Данные Евгения Косицина (из листа "Сводная по зп")
    print("\n👤 ЕВГЕНИЙ КОСИЦИН")
    print("-" * 50)
    print("💼 Должность: Руководитель отдела по работе с Китаем")
    print("📊 Источник данных: Лист 'Сводная по зп'")
    print("📅 Период: Июнь - Декабрь 2024")
    
    # Реальные данные Евгения
    eugene_total = 963857
    eugene_monthly_data = {
        'Июнь': 131189,
        'Июль': 153971,
        'Август': 151119,
        'Сентябрь': 185245,
        'Октябрь': 206200,
        'Ноябрь': 136133,
        'Декабрь': 211490
    }
    
    months_count_eugene = len(eugene_monthly_data)
    avg_monthly_eugene = eugene_total / months_count_eugene
    annual_eugene = avg_monthly_eugene * 12
    
    print(f"💰 Общий доход за {months_count_eugene} месяцев: {eugene_total:,.2f} руб.")
    print(f"📅 Месячные данные: {eugene_monthly_data}")
    print(f"📊 Среднемесячно: {avg_monthly_eugene:,.2f} руб.")
    print(f"🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {annual_eugene:,.2f} руб.")
    
    # Сравнительный анализ
    print("\n" + "=" * 70)
    print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ")
    print("=" * 70)
    
    print(f"\n📊 СРАВНЕНИЕ ОБЩИХ ДОХОДОВ:")
    print(f"   👤 Артем Василевский: {artem_total:,.2f} руб.")
    print(f"   👤 Евгений Косицин:   {eugene_total:,.2f} руб.")
    print(f"   📈 Разница: {artem_total - eugene_total:,.2f} руб.")
    print(f"   📊 Артем получает на {((artem_total / eugene_total - 1) * 100):.1f}% больше")
    
    print(f"\n📊 СРАВНЕНИЕ СРЕДНЕМЕСЯЧНЫХ ДОХОДОВ:")
    print(f"   👤 Артем Василевский: {avg_monthly_artem:,.2f} руб./месяц")
    print(f"   👤 Евгений Косицин:   {avg_monthly_eugene:,.2f} руб./месяц")
    print(f"   📈 Разница: {avg_monthly_artem - avg_monthly_eugene:,.2f} руб./месяц")
    print(f"   📊 Артем получает на {((avg_monthly_artem / avg_monthly_eugene - 1) * 100):.1f}% больше")
    
    print(f"\n📊 СРАВНЕНИЕ СРЕДНЕГОДОВЫХ ЗАРПЛАТ:")
    print(f"   👤 Артем Василевский: {annual_artem:,.2f} руб./год")
    print(f"   👤 Евгений Косицин:   {annual_eugene:,.2f} руб./год")
    print(f"   📈 Разница: {annual_artem - annual_eugene:,.2f} руб./год")
    print(f"   📊 Артем получает на {((annual_artem / annual_eugene - 1) * 100):.1f}% больше")
    
    # Динамика роста
    print(f"\n📈 АНАЛИЗ ДИНАМИКИ РОСТА:")
    
    # Артем - динамика
    artem_values = list(artem_monthly_data.values())
    artem_growth = ((artem_values[-1] / artem_values[0] - 1) * 100) if artem_values[0] > 0 else 0
    print(f"   👤 Артем: рост с {artem_values[0]:,.0f} до {artem_values[-1]:,.0f} руб. ({artem_growth:+.1f}%)")
    
    # Евгений - динамика
    eugene_values = list(eugene_monthly_data.values())
    eugene_growth = ((eugene_values[-1] / eugene_values[0] - 1) * 100) if eugene_values[0] > 0 else 0
    print(f"   👤 Евгений: рост с {eugene_values[0]:,.0f} до {eugene_values[-1]:,.0f} руб. ({eugene_growth:+.1f}%)")
    
    # Сохраняем финальный отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"final_real_data_report_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ФИНАЛЬНЫЙ ОТЧЕТ НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Источник: Лист 'Сводная по зп' из файла 'Табл выплаты 2025 (1).xlsx'\n")
        f.write("Период: Июнь - Декабрь 2024\n\n")
        
        f.write("АРТЕМ ВАСИЛЕВСКИЙ\n")
        f.write("-" * 50 + "\n")
        f.write("Должность: Руководитель отдела по работе с Китаем\n")
        f.write(f"Общий доход за 7 месяцев: {artem_total:,.2f} руб.\n")
        f.write(f"Среднемесячно: {avg_monthly_artem:,.2f} руб.\n")
        f.write(f"СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {annual_artem:,.2f} руб.\n")
        f.write("Месячные данные:\n")
        for month, amount in artem_monthly_data.items():
            f.write(f"  {month}: {amount:,.2f} руб.\n")
        
        f.write("\nЕВГЕНИЙ КОСИЦИН\n")
        f.write("-" * 50 + "\n")
        f.write("Должность: Руководитель отдела по работе с Китаем\n")
        f.write(f"Общий доход за 7 месяцев: {eugene_total:,.2f} руб.\n")
        f.write(f"Среднемесячно: {avg_monthly_eugene:,.2f} руб.\n")
        f.write(f"СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {annual_eugene:,.2f} руб.\n")
        f.write("Месячные данные:\n")
        for month, amount in eugene_monthly_data.items():
            f.write(f"  {month}: {amount:,.2f} руб.\n")
        
        f.write("\nСРАВНИТЕЛЬНЫЙ АНАЛИЗ\n")
        f.write("-" * 50 + "\n")
        f.write(f"Разница в общих доходах: {artem_total - eugene_total:,.2f} руб.\n")
        f.write(f"Артем получает на {((artem_total / eugene_total - 1) * 100):.1f}% больше\n")
        f.write(f"Разница в среднемесячных доходах: {avg_monthly_artem - avg_monthly_eugene:,.2f} руб.\n")
        f.write(f"Артем получает на {((avg_monthly_artem / avg_monthly_eugene - 1) * 100):.1f}% больше\n")
        f.write(f"Разница в среднегодовых зарплатах: {annual_artem - annual_eugene:,.2f} руб.\n")
        f.write(f"Артем получает на {((annual_artem / annual_eugene - 1) * 100):.1f}% больше\n")
        
        f.write(f"\nДИНАМИКА РОСТА:\n")
        f.write(f"Артем: {artem_growth:+.1f}% за период\n")
        f.write(f"Евгений: {eugene_growth:+.1f}% за период\n")
    
    print(f"\n📄 Финальный отчет сохранен в файл: {output_file}")
    
    # Создаем краткий отчет
    summary_file = "real_data_salary_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("КРАТКИЙ ОТЧЕТ ПО РЕАЛЬНЫМ ДАННЫМ\n")
        f.write("=" * 50 + "\n\n")
        f.write("АРТЕМ ВАСИЛЕВСКИЙ: {:,} руб./год\n".format(int(annual_artem)))
        f.write("ЕВГЕНИЙ КОСИЦИН: {:,} руб./год\n".format(int(annual_eugene)))
        f.write("Разница: {:,} руб./год\n".format(int(annual_artem - annual_eugene)))
        f.write("Артем получает на {:.1f}% больше\n".format((annual_artem / annual_eugene - 1) * 100))
        f.write("\nИсточник: Лист 'Сводная по зп', период Июнь-Декабрь 2024\n")
    
    print(f"📋 Краткий отчет сохранен в файл: {summary_file}")

if __name__ == "__main__":
    generate_final_real_data_report()
    print("\n✅ Финальный отчет на основе реальных данных готов!")
