#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ процентных данных Флориды
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

def analyze_florida_percentages():
    """Анализ процентных данных Флориды"""
    
    # Загружаем данные Флориды
    florida_file = "output/florida_data_final.xlsx"
    if not os.path.exists(florida_file):
        print("❌ Файл с данными Флориды не найден")
        return
    
    df = pd.read_excel(florida_file)
    print(f"📊 Загружено {len(df)} записей Флориды")
    
    # Анализируем все числовые колонки
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print(f"📈 Числовые колонки: {numeric_cols}")
    
    # Ищем потенциальные процентные данные
    percentage_candidates = []
    
    for col in numeric_cols:
        values = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(values) > 0:
            avg_value = values.mean()
            min_value = values.min()
            max_value = values.max()
            
            # Критерии для определения процентов
            is_percentage = False
            reason = ""
            
            if avg_value <= 100 and max_value <= 100:
                is_percentage = True
                reason = "Значения в диапазоне 0-100"
            elif 'процент' in str(col).lower() or '%' in str(col):
                is_percentage = True
                reason = "Название колонки содержит 'процент' или '%'"
            elif avg_value <= 1 and max_value <= 1:
                is_percentage = True
                reason = "Значения в диапазоне 0-1 (десятичные проценты)"
            
            if is_percentage:
                percentage_candidates.append({
                    'колонка': col,
                    'среднее': avg_value,
                    'мин': min_value,
                    'макс': max_value,
                    'количество': len(values),
                    'причина': reason
                })
    
    print(f"\n📊 Найдено {len(percentage_candidates)} потенциальных процентных колонок:")
    
    for candidate in percentage_candidates:
        print(f"\nКолонка: {candidate['колонка']}")
        print(f"  Среднее: {candidate['среднее']:.2f}")
        print(f"  Мин: {candidate['мин']:.2f}")
        print(f"  Макс: {candidate['макс']:.2f}")
        print(f"  Количество: {candidate['количество']}")
        print(f"  Причина: {candidate['причина']}")
    
    # Анализируем ставки (СС)
    if 'СС' in df.columns:
        ss_values = pd.to_numeric(df['СС'], errors='coerce').dropna()
        if len(ss_values) > 0:
            print(f"\n📈 АНАЛИЗ СТАВОК (СС):")
            print(f"  Средняя ставка: {ss_values.mean():,.2f} руб.")
            print(f"  Медиана: {ss_values.median():,.2f} руб.")
            print(f"  Минимум: {ss_values.min():,.2f} руб.")
            print(f"  Максимум: {ss_values.max():,.2f} руб.")
            print(f"  Стандартное отклонение: {ss_values.std():,.2f} руб.")
            print(f"  Количество значений: {len(ss_values)}")
            
            # Рассчитываем процент от оклада
            if 'Unnamed: 7' in df.columns:  # Оклад
                salary_values = pd.to_numeric(df['Unnamed: 7'], errors='coerce').dropna()
                if len(salary_values) > 0:
                    # Создаем DataFrame для анализа
                    analysis_df = pd.DataFrame({
                        'Оклад': salary_values,
                        'Ставка_СС': ss_values[:len(salary_values)] if len(ss_values) >= len(salary_values) else ss_values
                    })
                    
                    # Рассчитываем процент ставки от оклада
                    analysis_df['Процент_от_оклада'] = (analysis_df['Ставка_СС'] / analysis_df['Оклад']) * 100
                    
                    print(f"\n📊 ПРОЦЕНТ СТАВКИ ОТ ОКЛАДА:")
                    print(f"  Средний процент: {analysis_df['Процент_от_оклада'].mean():.2f}%")
                    print(f"  Медиана: {analysis_df['Процент_от_оклада'].median():.2f}%")
                    print(f"  Минимум: {analysis_df['Процент_от_оклада'].min():.2f}%")
                    print(f"  Максимум: {analysis_df['Процент_от_оклада'].max():.2f}%")
                    
                    # Сохраняем анализ
                    analysis_df.to_excel("output/florida_percentage_analysis.xlsx", index=False)
                    print(f"✅ Анализ сохранен в: output/florida_percentage_analysis.xlsx")
    
    # Создаем график процентного анализа
    if percentage_candidates:
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Детальный анализ процентных данных Флориды', fontsize=16, fontweight='bold')
        
        # График 1: Средние значения процентных колонок
        cols = [c['колонка'] for c in percentage_candidates]
        means = [c['среднее'] for c in percentage_candidates]
        
        axes[0, 0].bar(range(len(cols)), means, color='lightgreen', alpha=0.7)
        axes[0, 0].set_title('Средние значения процентных колонок')
        axes[0, 0].set_xticks(range(len(cols)))
        axes[0, 0].set_xticklabels(cols, rotation=45, ha='right')
        axes[0, 0].set_ylabel('Значение')
        
        # Добавляем значения на столбцы
        for i, v in enumerate(means):
            axes[0, 0].text(i, v + max(means)*0.01, f'{v:.2f}', 
                           ha='center', va='bottom', fontweight='bold')
        
        # График 2: Диапазон значений
        mins = [c['мин'] for c in percentage_candidates]
        maxs = [c['макс'] for c in percentage_candidates]
        
        x = np.arange(len(cols))
        width = 0.35
        
        axes[0, 1].bar(x - width/2, mins, width, label='Минимум', color='lightcoral', alpha=0.7)
        axes[0, 1].bar(x + width/2, maxs, width, label='Максимум', color='lightblue', alpha=0.7)
        axes[0, 1].set_title('Диапазон значений')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(cols, rotation=45, ha='right')
        axes[0, 1].legend()
        
        # График 3: Количество значений
        counts = [c['количество'] for c in percentage_candidates]
        
        axes[1, 0].bar(range(len(cols)), counts, color='orange', alpha=0.7)
        axes[1, 0].set_title('Количество значений')
        axes[1, 0].set_xticks(range(len(cols)))
        axes[1, 0].set_xticklabels(cols, rotation=45, ha='right')
        axes[1, 0].set_ylabel('Количество')
        
        # График 4: Распределение по месяцам (если есть данные)
        if 'sheet_name' in df.columns:
            month_counts = df['sheet_name'].value_counts()
            axes[1, 1].pie(month_counts.values, labels=month_counts.index, autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title('Распределение данных по месяцам')
        
        plt.tight_layout()
        plt.savefig("output/florida_percentage_analysis.png", dpi=300, bbox_inches='tight')
        print(f"✅ График сохранен: output/florida_percentage_analysis.png")
        plt.show()
    
    # Создаем итоговый отчет
    with open("output/florida_percentage_report.txt", 'w', encoding='utf-8') as f:
        f.write("ДЕТАЛЬНЫЙ АНАЛИЗ ПРОЦЕНТНЫХ ДАННЫХ ФЛОРИДЫ\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Дата анализа: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Общее количество записей: {len(df)}\n\n")
        
        f.write("ПРОЦЕНТНЫЕ КОЛОНКИ:\n")
        f.write("-" * 30 + "\n")
        
        if percentage_candidates:
            for candidate in percentage_candidates:
                f.write(f"\nКолонка: {candidate['колонка']}\n")
                f.write(f"  Среднее: {candidate['среднее']:.2f}\n")
                f.write(f"  Мин: {candidate['мин']:.2f}\n")
                f.write(f"  Макс: {candidate['макс']:.2f}\n")
                f.write(f"  Количество: {candidate['количество']}\n")
                f.write(f"  Причина: {candidate['причина']}\n")
        else:
            f.write("Процентные колонки не найдены\n")
        
        # Анализ ставок
        if 'СС' in df.columns:
            ss_values = pd.to_numeric(df['СС'], errors='coerce').dropna()
            if len(ss_values) > 0:
                f.write(f"\n\nАНАЛИЗ СТАВОК (СС):\n")
                f.write("-" * 30 + "\n")
                f.write(f"Средняя ставка: {ss_values.mean():,.2f} руб.\n")
                f.write(f"Медиана: {ss_values.median():,.2f} руб.\n")
                f.write(f"Минимум: {ss_values.min():,.2f} руб.\n")
                f.write(f"Максимум: {ss_values.max():,.2f} руб.\n")
                f.write(f"Стандартное отклонение: {ss_values.std():,.2f} руб.\n")
                f.write(f"Количество значений: {len(ss_values)}\n")
        
        f.write(f"\n\nИТОГОВЫЕ ВЫВОДЫ:\n")
        f.write("-" * 30 + "\n")
        f.write(f"1. Найдено {len(percentage_candidates)} потенциальных процентных колонок\n")
        f.write(f"2. Средняя ставка СС: {ss_values.mean():,.2f} руб.\n")
        if 'Unnamed: 7' in df.columns:
            salary_avg = pd.to_numeric(df['Unnamed: 7'], errors='coerce').dropna().mean()
            f.write(f"3. Средний оклад: {salary_avg:,.2f} руб.\n")
            f.write(f"4. Средний процент ставки от оклада: {(ss_values.mean()/salary_avg)*100:.2f}%\n")
    
    print(f"✅ Итоговый отчет сохранен: output/florida_percentage_report.txt")

if __name__ == "__main__":
    analyze_florida_percentages()
