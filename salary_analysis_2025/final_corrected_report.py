#!/usr/bin/env python3
"""
Финальный исправленный отчет по среднегодовым зарплатам
с учетом процентов из столбца даты
"""

import pandas as pd
from datetime import datetime

def generate_final_corrected_report():
    """Генерирует финальный исправленный отчет с правильными расчетами"""
    
    print("🎯 ФИНАЛЬНЫЙ ИСПРАВЛЕННЫЙ ОТЧЕТ ПО СРЕДНЕГОДОВЫМ ЗАРПЛАТАМ")
    print("=" * 70)
    print("📊 С учетом процентов из столбца даты 2019-08-23")
    print("=" * 70)
    
    # Данные Артема Василевского
    print("\n👤 АРТЕМ ВАСИЛЕВСКИЙ")
    print("-" * 50)
    print("💼 Должность: Руководитель отдела по работе с Китаем")
    print("💰 Базовая зарплата: 175,000 руб./месяц")
    print("📊 Процент дополнительной выплаты: 100% (из столбца даты)")
    print("➕ Дополнительные выплаты: 30,450 руб./месяц")
    print("📊 СС (страховые взносы): 305,337.69 руб.")
    
    # Расчеты для Артема
    artem_base_monthly = 175000
    artem_percentage = 100  # 100% из столбца даты
    artem_percentage_payment = artem_base_monthly * (artem_percentage / 100)
    artem_additional = 30450
    artem_total_monthly = artem_base_monthly + artem_percentage_payment + artem_additional
    artem_annual_total = artem_total_monthly * 12
    
    print(f"\n📈 РАСЧЕТЫ АРТЕМА ВАСИЛЕВСКОГО:")
    print(f"   💵 Базовая зарплата: {artem_base_monthly:,.2f} руб.")
    print(f"   📊 Доплата по проценту (100%): {artem_percentage_payment:,.2f} руб.")
    print(f"   ➕ Дополнительные выплаты: {artem_additional:,.2f} руб.")
    print(f"   💰 Общая месячная зарплата: {artem_total_monthly:,.2f} руб.")
    print(f"   🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {artem_annual_total:,.2f} руб.")
    
    # Данные Евгения Косицина
    print("\n👤 ЕВГЕНИЙ КОСИЦИН")
    print("-" * 50)
    print("💼 Должность: Руководитель отдела по работе с Китаем")
    print("💰 Базовая зарплата: 120,000 руб./месяц")
    print("📊 Процент дополнительной выплаты: 0% (нет данных в столбце даты)")
    print("➕ Дополнительные выплаты: 36,846.94 руб./месяц")
    print("📊 СС (страховые взносы): 147,121.74 руб.")
    
    # Расчеты для Евгения
    eugene_base_monthly = 120000
    eugene_percentage = 0  # Нет процента в столбце даты
    eugene_percentage_payment = eugene_base_monthly * (eugene_percentage / 100)
    eugene_additional = 36846.94
    eugene_total_monthly = eugene_base_monthly + eugene_percentage_payment + eugene_additional
    eugene_annual_total = eugene_total_monthly * 12
    
    print(f"\n📈 РАСЧЕТЫ ЕВГЕНИЯ КОСИЦИНА:")
    print(f"   💵 Базовая зарплата: {eugene_base_monthly:,.2f} руб.")
    print(f"   📊 Доплата по проценту (0%): {eugene_percentage_payment:,.2f} руб.")
    print(f"   ➕ Дополнительные выплаты: {eugene_additional:,.2f} руб.")
    print(f"   💰 Общая месячная зарплата: {eugene_total_monthly:,.2f} руб.")
    print(f"   🎯 СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {eugene_annual_total:,.2f} руб.")
    
    # Сравнительный анализ
    print("\n" + "=" * 70)
    print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ")
    print("=" * 70)
    
    print(f"\n📊 СРАВНЕНИЕ СРЕДНЕГОДОВЫХ ЗАРПЛАТ:")
    print(f"   👤 Артем Василевский: {artem_annual_total:,.2f} руб.")
    print(f"   👤 Евгений Косицин:   {eugene_annual_total:,.2f} руб.")
    print(f"   📈 Разница: {artem_annual_total - eugene_annual_total:,.2f} руб.")
    print(f"   📊 Артем получает на {((artem_annual_total / eugene_annual_total - 1) * 100):.1f}% больше")
    
    print(f"\n📊 СРАВНЕНИЕ МЕСЯЧНЫХ ЗАРПЛАТ:")
    print(f"   👤 Артем Василевский: {artem_total_monthly:,.2f} руб./месяц")
    print(f"   👤 Евгений Косицин:   {eugene_total_monthly:,.2f} руб./месяц")
    print(f"   📈 Разница: {artem_total_monthly - eugene_total_monthly:,.2f} руб./месяц")
    print(f"   📊 Артем получает на {((artem_total_monthly / eugene_total_monthly - 1) * 100):.1f}% больше")
    
    print(f"\n📊 СРАВНЕНИЕ БАЗОВЫХ ЗАРПЛАТ:")
    print(f"   👤 Артем Василевский: {artem_base_monthly:,.2f} руб./месяц")
    print(f"   👤 Евгений Косицин:   {eugene_base_monthly:,.2f} руб./месяц")
    print(f"   📈 Разница: {artem_base_monthly - eugene_base_monthly:,.2f} руб./месяц")
    print(f"   📊 Артем получает на {((artem_base_monthly / eugene_base_monthly - 1) * 100):.1f}% больше")
    
    # Сохраняем финальный исправленный отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"final_corrected_salary_report_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ФИНАЛЬНЫЙ ИСПРАВЛЕННЫЙ ОТЧЕТ ПО СРЕДНЕГОДОВЫМ ЗАРПЛАТАМ\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("Источник: Табл выплаты 2025 (1).xlsx\n")
        f.write("Примечание: Проценты учитываются из столбца даты 2019-08-23\n\n")
        
        f.write("АРТЕМ ВАСИЛЕВСКИЙ\n")
        f.write("-" * 50 + "\n")
        f.write("Должность: Руководитель отдела по работе с Китаем\n")
        f.write(f"Базовая зарплата: {artem_base_monthly:,.2f} руб./месяц\n")
        f.write(f"Процент дополнительной выплаты: {artem_percentage}%\n")
        f.write(f"Доплата по проценту: {artem_percentage_payment:,.2f} руб./месяц\n")
        f.write(f"Дополнительные выплаты: {artem_additional:,.2f} руб./месяц\n")
        f.write(f"Общая месячная зарплата: {artem_total_monthly:,.2f} руб./месяц\n")
        f.write(f"СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {artem_annual_total:,.2f} руб.\n\n")
        
        f.write("ЕВГЕНИЙ КОСИЦИН\n")
        f.write("-" * 50 + "\n")
        f.write("Должность: Руководитель отдела по работе с Китаем\n")
        f.write(f"Базовая зарплата: {eugene_base_monthly:,.2f} руб./месяц\n")
        f.write(f"Процент дополнительной выплаты: {eugene_percentage}%\n")
        f.write(f"Доплата по проценту: {eugene_percentage_payment:,.2f} руб./месяц\n")
        f.write(f"Дополнительные выплаты: {eugene_additional:,.2f} руб./месяц\n")
        f.write(f"Общая месячная зарплата: {eugene_total_monthly:,.2f} руб./месяц\n")
        f.write(f"СРЕДНЕГОДОВАЯ ЗАРПЛАТА: {eugene_annual_total:,.2f} руб.\n\n")
        
        f.write("СРАВНИТЕЛЬНЫЙ АНАЛИЗ\n")
        f.write("-" * 50 + "\n")
        f.write(f"Разница в среднегодовых зарплатах: {artem_annual_total - eugene_annual_total:,.2f} руб.\n")
        f.write(f"Артем получает на {((artem_annual_total / eugene_annual_total - 1) * 100):.1f}% больше\n")
        f.write(f"Разница в месячных зарплатах: {artem_total_monthly - eugene_total_monthly:,.2f} руб.\n")
        f.write(f"Артем получает на {((artem_total_monthly / eugene_total_monthly - 1) * 100):.1f}% больше\n")
        f.write(f"Разница в базовых зарплатах: {artem_base_monthly - eugene_base_monthly:,.2f} руб.\n")
        f.write(f"Артем получает на {((artem_base_monthly / eugene_base_monthly - 1) * 100):.1f}% больше\n")
    
    print(f"\n📄 Финальный исправленный отчет сохранен в файл: {output_file}")
    
    # Создаем краткий исправленный отчет
    summary_file = "corrected_salary_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("ИСПРАВЛЕННЫЙ КРАТКИЙ ОТЧЕТ ПО СРЕДНЕГОДОВЫМ ЗАРПЛАТАМ\n")
        f.write("=" * 60 + "\n\n")
        f.write("АРТЕМ ВАСИЛЕВСКИЙ: {:,} руб./год\n".format(int(artem_annual_total)))
        f.write("ЕВГЕНИЙ КОСИЦИН: {:,} руб./год\n".format(int(eugene_annual_total)))
        f.write("Разница: {:,} руб./год\n".format(int(artem_annual_total - eugene_annual_total)))
        f.write("Артем получает на {:.1f}% больше\n".format((artem_annual_total / eugene_annual_total - 1) * 100))
    
    print(f"📋 Исправленный краткий отчет сохранен в файл: {summary_file}")

if __name__ == "__main__":
    generate_final_corrected_report()
    print("\n✅ Финальный исправленный отчет готов!")
