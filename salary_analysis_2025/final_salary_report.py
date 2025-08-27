#!/usr/bin/env python3
"""
Финальный отчет по среднегодовым зарплатам
Артем Василевский и Евгений Косицин
"""

import pandas as pd
from datetime import datetime

def generate_final_report():
    """Генерирует финальный отчет с расчетами"""
    
    print("🎯 ФИНАЛЬНЫЙ ОТЧЕТ ПО СРЕДНЕГОДОВЫМ ЗАРПЛАТАМ")
    print("=" * 60)
    
    # Данные Артема Василевского
    print("\n👤 АРТЕМ ВАСИЛЕВСКИЙ")
    print("-" * 40)
    print("💼 Должность: Руководитель отдела по работе с Китаем")
    print("💰 Базовая зарплата: 175,000 руб./месяц")
    print("➕ Дополнительные выплаты: 30,450 руб./месяц")
    print("📊 СС (страховые взносы): 305,337.69 руб.")
    
    # Расчеты для Артема
    artem_base_monthly = 175000
    artem_additional = 30450
    artem_total_monthly = artem_base_monthly + artem_additional
    artem_annual_base = artem_base_monthly * 12
    artem_annual_total = artem_total_monthly * 12
    
    print(f"\n📈 РАСЧЕТЫ АРТЕМА ВАСИЛЕВСКОГО:")
    print(f"   💵 Базовая месячная зарплата: {artem_base_monthly:,.2f} руб.")
    print(f"   📅 Базовая годовая зарплата: {artem_annual_base:,.2f} руб.")
    print(f"   💰 Месячная с доплатами: {artem_total_monthly:,.2f} руб.")
    print(f"   🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {artem_annual_total:,.2f} руб.")
    
    # Данные Евгения Косицина
    print("\n👤 ЕВГЕНИЙ КОСИЦИН")
    print("-" * 40)
    print("💼 Должность: Руководитель отдела по работе с Китаем")
    print("💰 Базовая зарплата: 120,000 руб./месяц")
    print("➕ Дополнительные выплаты: 36,846.94 руб./месяц")
    print("📊 СС (страховые взносы): 147,121.74 руб.")
    
    # Расчеты для Евгения
    eugene_base_monthly = 120000
    eugene_additional = 36846.94
    eugene_total_monthly = eugene_base_monthly + eugene_additional
    eugene_annual_base = eugene_base_monthly * 12
    eugene_annual_total = eugene_total_monthly * 12
    
    print(f"\n📈 РАСЧЕТЫ ЕВГЕНИЯ КОСИЦИНА:")
    print(f"   💵 Базовая месячная зарплата: {eugene_base_monthly:,.2f} руб.")
    print(f"   📅 Базовая годовая зарплата: {eugene_annual_base:,.2f} руб.")
    print(f"   💰 Месячная с доплатами: {eugene_total_monthly:,.2f} руб.")
    print(f"   🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {eugene_annual_total:,.2f} руб.")
    
    # Сравнительный анализ
    print("\n" + "=" * 60)
    print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ")
    print("=" * 60)
    
    print(f"\n📊 СРАВНЕНИЕ СРЕДНЕГОДОВЫХ ЗАРПЛАТ:")
    print(f"   👤 Артем Василевский: {artem_annual_total:,.2f} руб.")
    print(f"   👤 Евгений Косицин:   {eugene_annual_total:,.2f} руб.")
    print(f"   📈 Разница: {artem_annual_total - eugene_annual_total:,.2f} руб.")
    print(f"   📊 Артем получает на {((artem_annual_total / eugene_annual_total - 1) * 100):.1f}% больше")
    
    print(f"\n📊 СРАВНЕНИЕ БАЗОВЫХ ЗАРПЛАТ:")
    print(f"   👤 Артем Василевский: {artem_annual_base:,.2f} руб.")
    print(f"   👤 Евгений Косицин:   {eugene_annual_base:,.2f} руб.")
    print(f"   📈 Разница: {artem_annual_base - eugene_annual_base:,.2f} руб.")
    print(f"   📊 Артем получает на {((artem_annual_base / eugene_annual_base - 1) * 100):.1f}% больше")
    
    # Сохраняем финальный отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"final_salary_report_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ФИНАЛЬНЫЙ ОТЧЕТ ПО СРЕДНЕГОДОВЫМ ЗАРПЛАТАМ\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Источник: Табл выплаты 2025 (1).xlsx\n\n")
        
        f.write("АРТЕМ ВАСИЛЕВСКИЙ\n")
        f.write("-" * 40 + "\n")
        f.write("Должность: Руководитель отдела по работе с Китаем\n")
        f.write(f"Базовая зарплата: {artem_base_monthly:,.2f} руб./месяц\n")
        f.write(f"Дополнительные выплаты: {artem_additional:,.2f} руб./месяц\n")
        f.write(f"Общая месячная зарплата: {artem_total_monthly:,.2f} руб./месяц\n")
        f.write(f"СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {artem_annual_total:,.2f} руб.\n\n")
        
        f.write("ЕВГЕНИЙ КОСИЦИН\n")
        f.write("-" * 40 + "\n")
        f.write("Должность: Руководитель отдела по работе с Китаем\n")
        f.write(f"Базовая зарплата: {eugene_base_monthly:,.2f} руб./месяц\n")
        f.write(f"Дополнительные выплаты: {eugene_additional:,.2f} руб./месяц\n")
        f.write(f"Общая месячная зарплата: {eugene_total_monthly:,.2f} руб./месяц\n")
        f.write(f"СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {eugene_annual_total:,.2f} руб.\n\n")
        
        f.write("СРАВНИТЕЛЬНЫЙ АНАЛИЗ\n")
        f.write("-" * 40 + "\n")
        f.write(f"Разница в среднегодовых зарплатах: {artem_annual_total - eugene_annual_total:,.2f} руб.\n")
        f.write(f"Артем получает на {((artem_annual_total / eugene_annual_total - 1) * 100):.1f}% больше\n")
        f.write(f"Разница в базовых зарплатах: {artem_annual_base - eugene_annual_base:,.2f} руб.\n")
        f.write(f"Артем получает на {((artem_annual_base / eugene_annual_base - 1) * 100):.1f}% больше\n")
    
    print(f"\n📄 Финальный отчет сохранен в файл: {output_file}")
    
    # Создаем краткий отчет
    summary_file = "salary_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("КРАТКИЙ ОТЧЕТ ПО СРЕДНЕГОДОВЫМ ЗАРПЛАТАМ\n")
        f.write("=" * 50 + "\n\n")
        f.write("АРТЕМ ВАСИЛЕВСКИЙ: {:,} руб./год\n".format(int(artem_annual_total)))
        f.write("ЕВГЕНИЙ КОСИЦИН: {:,} руб./год\n".format(int(eugene_annual_total)))
        f.write("Разница: {:,} руб./год\n".format(int(artem_annual_total - eugene_annual_total)))
    
    print(f"📋 Краткий отчет сохранен в файл: {summary_file}")

if __name__ == "__main__":
    generate_final_report()
    print("\n✅ Финальный отчет готов!")
