#!/usr/bin/env python3
"""
Анализ эозинофилов за 2023 год
Данные из медицинских отчетов
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

# Данные об эозинофилах за 2023 год
eosinophils_data = [
    {
        'date': '2023-04-07',
        'eosinophils_percent': None,  # Нет данных в отчете
        'eosinophils_absolute': None,
        'notes': 'Нет данных об эозинофилах в отчете'
    },
    {
        'date': '2023-09-12',
        'eosinophils_percent': 6.7,
        'eosinophils_absolute': None,
        'notes': 'Сезонная аллергия - пик полыни/амброзии'
    },
    {
        'date': '2023-10-27',
        'eosinophils_percent': 10.7,
        'eosinophils_absolute': 0.71,
        'notes': 'Продолжение аллергического сезона'
    },
    {
        'date': '2023-11-17',
        'eosinophils_percent': 9.7,
        'eosinophils_absolute': None,
        'notes': 'Снижение, но остается повышенным'
    },
    {
        'date': '2023-12-05',
        'eosinophils_percent': 12.1,
        'eosinophils_absolute': None,
        'notes': 'Максимальное значение за период'
    },
    {
        'date': '2023-12-20',
        'eosinophils_percent': 6.4,
        'eosinophils_absolute': 0.41,
        'notes': 'Резкое улучшение - снижение вдвое'
    }
]

def create_eosinophils_chart():
    """Создает график динамики эозинофилов за 2023 год"""
    
    # Фильтруем данные с доступными значениями
    available_data = [d for d in eosinophils_data if d['eosinophils_percent'] is not None]
    
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in available_data]
    values = [d['eosinophils_percent'] for d in available_data]
    notes = [d['notes'] for d in available_data]
    
    # Создаем график
    plt.figure(figsize=(12, 8))
    
    # Основной график
    plt.plot(dates, values, 'o-', linewidth=2, markersize=8, color='#2E86AB', label='Эозинофилы %')
    
    # Линия нормы
    normal_range = [4.4] * len(dates)
    plt.axhline(y=4.4, color='red', linestyle='--', alpha=0.7, label='Верхняя граница нормы (4.4%)')
    
    # Заполнение области выше нормы
    plt.fill_between(dates, values, normal_range, where=[v > 4.4 for v in values], 
                    alpha=0.3, color='red', label='Область выше нормы')
    
    # Настройка осей
    plt.xlabel('Дата', fontsize=12, fontweight='bold')
    plt.ylabel('Эозинофилы (%)', fontsize=12, fontweight='bold')
    plt.title('Динамика эозинофилов за 2023 год', fontsize=14, fontweight='bold', pad=20)
    
    # Форматирование дат
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()
    
    # Добавление значений на точки
    for i, (date, value) in enumerate(zip(dates, values)):
        plt.annotate(f'{value}%', (date, value), 
                    textcoords="offset points", xytext=(0,10), 
                    ha='center', fontsize=10, fontweight='bold')
    
    # Добавление заметок
    for i, (date, value, note) in enumerate(zip(dates, values, notes)):
        y_offset = 15 if value < 8 else -15
        plt.annotate(note, (date, value), 
                    textcoords="offset points", xytext=(0, y_offset), 
                    ha='center', fontsize=8, alpha=0.8, 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # Настройка сетки
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    
    # Настройка пределов осей
    plt.ylim(0, max(values) * 1.2)
    
    # Добавление статистики
    stats_text = f"""
Статистика за 2023 год:
• Максимальное значение: {max(values)}% (05.12.2023)
• Минимальное значение: {min(values)}% (20.12.2023)
• Среднее значение: {np.mean(values):.1f}%
• Количество измерений: {len(values)}
• Норма: 0.0-4.4%
    """
    
    plt.figtext(0.02, 0.02, stats_text, fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    plt.tight_layout()
    return plt

def print_summary():
    """Выводит сводку по эозинофилам за 2023 год"""
    print("=" * 60)
    print("📊 АНАЛИЗ ЭОЗИНОФИЛОВ ЗА 2023 ГОД")
    print("=" * 60)
    
    available_data = [d for d in eosinophils_data if d['eosinophils_percent'] is not None]
    
    print(f"\n📈 Динамика значений:")
    for data in available_data:
        status = "⚠️ ВЫШЕ НОРМЫ" if data['eosinophils_percent'] > 4.4 else "✅ НОРМА"
        print(f"  {data['date']}: {data['eosinophils_percent']}% {status}")
        print(f"    Примечание: {data['notes']}")
    
    values = [d['eosinophils_percent'] for d in available_data]
    
    print(f"\n📊 Статистика:")
    print(f"  • Максимальное значение: {max(values)}% (05.12.2023)")
    print(f"  • Минимальное значение: {min(values)}% (20.12.2023)")
    print(f"  • Среднее значение: {np.mean(values):.1f}%")
    print(f"  • Норма: 0.0-4.4%")
    
    print(f"\n🎯 Ключевые наблюдения:")
    print(f"  • Все значения выше нормы (4.4%)")
    print(f"  • Пик в декабре (12.1%) - максимальное значение")
    print(f"  • Значительное улучшение к концу года (6.4%)")
    print(f"  • Связь с сезонной аллергией (полынь, амброзия)")
    
    print(f"\n💡 Рекомендации:")
    print(f"  • Продолжить аллергологическое обследование")
    print(f"  • Мониторинг в сезон цветения аллергенов")
    print(f"  • Рассмотреть АСИТ (аллерген-специфическую иммунотерапию)")

if __name__ == "__main__":
    # Выводим сводку
    print_summary()
    
    # Создаем график
    plt = create_eosinophils_chart()
    
    # Сохраняем график
    output_file = "eosinophils_2023_chart.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n📊 График сохранен: {output_file}")
    
    # Показываем график
    plt.show()
