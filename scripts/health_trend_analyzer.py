#!/usr/bin/env python3
"""
Анализатор трендов медицинских показателей

Анализирует динамику изменения показателей здоровья во времени
и создает отчеты с рекомендациями.

Использование:
    python scripts/health_trend_analyzer.py
    python scripts/health_trend_analyzer.py --parameter glucose
    python scripts/health_trend_analyzer.py --report
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import numpy as np

# Импортируем функцию проверки диапазонов
import sys
sys.path.append(str(Path(__file__).parent))

def load_medical_records(records_dir="Docs/Health/lab_results"):
    """Загружает все медицинские записи из JSON файлов"""
    records_path = Path(records_dir)
    
    if not records_path.exists():
        print(f"📁 Папка {records_path} не найдена")
        return []
    
    json_files = list(records_path.glob("analysis_*.json"))
    
    if not json_files:
        print(f"📄 JSON файлы с анализами не найдены в {records_path}")
        return []
    
    records = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                record = json.load(f)
                records.append(record)
        except Exception as e:
            print(f"⚠️  Ошибка при чтении {json_file}: {e}")
    
    # Сортируем по дате
    records.sort(key=lambda x: x['date'])
    return records

def create_trends_dataframe(records):
    """Создает DataFrame с трендами показателей"""
    if not records:
        return pd.DataFrame()
    
    # Собираем все данные в один DataFrame
    data_rows = []
    
    for record in records:
        date = record['date']
        order_number = record['order_number']
        
        for param, data in record['values'].items():
            data_rows.append({
                'date': pd.to_datetime(date),
                'order_number': order_number,
                'parameter': param,
                'value': data['value'],
                'unit': data['unit'],
                'in_range': data['in_range'],
                'normal_min': data['normal_range']['min'] if data['normal_range'] else None,
                'normal_max': data['normal_range']['max'] if data['normal_range'] else None,
            })
    
    df = pd.DataFrame(data_rows)
    return df

def analyze_parameter_trend(df, parameter):
    """Анализирует тренд конкретного параметра"""
    param_data = df[df['parameter'] == parameter].copy()
    
    if param_data.empty:
        return None
    
    param_data = param_data.sort_values('date')
    
    # Вычисляем статистики
    analysis = {
        'parameter': parameter,
        'count': len(param_data),
        'first_date': param_data['date'].min(),
        'last_date': param_data['date'].max(),
        'first_value': param_data['value'].iloc[0],
        'last_value': param_data['value'].iloc[-1],
        'min_value': param_data['value'].min(),
        'max_value': param_data['value'].max(),
        'mean_value': param_data['value'].mean(),
        'std_value': param_data['value'].std(),
        'unit': param_data['unit'].iloc[0] if not param_data['unit'].empty else '',
        'normal_min': param_data['normal_min'].iloc[0] if not param_data['normal_min'].empty else None,
        'normal_max': param_data['normal_max'].iloc[0] if not param_data['normal_max'].empty else None,
    }
    
    # Анализируем тренд
    if len(param_data) >= 2:
        # Простая линейная регрессия для определения тренда
        x = np.arange(len(param_data))
        y = param_data['value'].values
        
        slope = np.polyfit(x, y, 1)[0]
        
        if abs(slope) < 0.1:  # Порог для определения стабильности
            trend = "стабильный"
        elif slope > 0:
            trend = "растущий"
        else:
            trend = "убывающий"
        
        # Вычисляем изменение за период
        change = analysis['last_value'] - analysis['first_value']
        change_percent = (change / analysis['first_value']) * 100 if analysis['first_value'] != 0 else 0
        
        analysis.update({
            'trend': trend,
            'slope': slope,
            'change_absolute': change,
            'change_percent': change_percent,
        })
    
    # Анализируем нарушения нормы
    normal_violations = param_data[param_data['in_range'] == False]
    analysis['violations_count'] = len(normal_violations)
    analysis['violations_percent'] = (len(normal_violations) / len(param_data)) * 100
    
    return analysis

def create_trend_visualization(df, parameter, output_dir="Docs/Health/trends"):
    """Создает визуализацию тренда параметра"""
    try:
        import matplotlib.pyplot as plt
        plt.style.use('default')
    except ImportError:
        print("⚠️  matplotlib не установлен, график не будет создан")
        return None
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    param_data = df[df['parameter'] == parameter].copy()
    
    if param_data.empty:
        return None
    
    param_data = param_data.sort_values('date')
    
    plt.figure(figsize=(12, 8))
    
    # График значений
    plt.subplot(2, 1, 1)
    plt.plot(param_data['date'], param_data['value'], 'o-', linewidth=2, markersize=8, label='Значения')
    
    # Добавляем линии нормы
    if not param_data['normal_min'].isna().all():
        plt.axhline(y=param_data['normal_min'].iloc[0], color='green', linestyle='--', alpha=0.7, label='Нижняя норма')
        plt.axhline(y=param_data['normal_max'].iloc[0], color='green', linestyle='--', alpha=0.7, label='Верхняя норма')
        
        # Закрашиваем область нормы
        plt.fill_between(param_data['date'], 
                        param_data['normal_min'].iloc[0], 
                        param_data['normal_max'].iloc[0], 
                        alpha=0.2, color='green', label='Норма')
    
    plt.title(f'Динамика {parameter.replace("_", " ").title()}')
    plt.ylabel(f'Значение ({param_data["unit"].iloc[0]})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # График отклонений от нормы
    plt.subplot(2, 1, 2)
    if not param_data['normal_min'].isna().all():
        normal_center = (param_data['normal_min'].iloc[0] + param_data['normal_max'].iloc[0]) / 2
        deviations = ((param_data['value'] - normal_center) / normal_center) * 100
        
        colors = ['red' if not in_range else 'green' for in_range in param_data['in_range']]
        plt.bar(param_data['date'], deviations, color=colors, alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
        plt.title('Отклонение от нормы (%)')
        plt.ylabel('Отклонение (%)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Сохраняем график
    filename = f"trend_{parameter}_{datetime.now().strftime('%Y%m%d')}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filepath

def generate_health_report(records, output_path="Docs/Health/health_report.md"):
    """Генерирует общий отчет по здоровью"""
    if not records:
        print("📊 Нет данных для создания отчета")
        return
    
    df = create_trends_dataframe(records)
    
    # Анализируем все параметры
    parameters = df['parameter'].unique()
    parameter_analyses = {}
    
    for param in parameters:
        analysis = analyze_parameter_trend(df, param)
        if analysis:
            parameter_analyses[param] = analysis
    
    # Создаем отчет
    report_content = f"""# 📊 Отчет по здоровью

**Дата создания:** {datetime.now().strftime('%d.%m.%Y %H:%M')}  
**Период анализа:** {df['date'].min().strftime('%d.%m.%Y')} - {df['date'].max().strftime('%d.%m.%Y')}  
**Количество анализов:** {len(records)}

## 📈 Общая статистика

- **Всего показателей отслеживается:** {len(parameters)}
- **Всего измерений:** {len(df)}
- **Последний анализ:** {records[-1]['date']}

## 🩺 Анализ по показателям

"""
    
    # Сортируем параметры по важности (по количеству нарушений)
    sorted_params = sorted(parameter_analyses.items(), 
                          key=lambda x: x[1]['violations_percent'], 
                          reverse=True)
    
    for param, analysis in sorted_params:
        param_name = param.replace('_', ' ').title()
        
        # Определяем статус
        if analysis['violations_percent'] == 0:
            status = "✅ Отлично"
        elif analysis['violations_percent'] < 25:
            status = "⚠️ Внимание"
        else:
            status = "❌ Требует внимания"
        
        # Определяем тренд
        if analysis.get('trend'):
            if analysis['trend'] == 'стабильный':
                trend_icon = "📊"
            elif analysis['trend'] == 'растущий':
                trend_icon = "📈"
            else:
                trend_icon = "📉"
            trend_text = f"{trend_icon} {analysis['trend']}"
        else:
            trend_text = "📊 недостаточно данных"
        
        report_content += f"""### {param_name} {status}

- **Текущее значение:** {analysis['last_value']} {analysis['unit']}
- **Тренд:** {trend_text}
- **Изменение за период:** {analysis.get('change_absolute', 0):.1f} {analysis['unit']} ({analysis.get('change_percent', 0):+.1f}%)
- **Нарушений нормы:** {analysis['violations_count']}/{analysis['count']} ({analysis['violations_percent']:.1f}%)
- **Норма:** {analysis['normal_min']}-{analysis['normal_max']} {analysis['unit']}

"""
    
    # Добавляем рекомендации
    report_content += """## 🎯 Рекомендации

### Приоритетные действия
"""
    
    # Находим параметры, требующие внимания
    problem_params = [param for param, analysis in parameter_analyses.items() 
                     if analysis['violations_percent'] > 25]
    
    if problem_params:
        for param in problem_params:
            param_name = param.replace('_', ' ').title()
            report_content += f"- [ ] **{param_name}**: Обратиться к врачу для коррекции\n"
    else:
        report_content += "- ✅ Все показатели в пределах нормы\n"
    
    report_content += """
### Общие рекомендации
- [ ] Регулярно сдавать анализы (каждые 6 месяцев)
- [ ] Поддерживать здоровый образ жизни
- [ ] Отслеживать динамику показателей
- [ ] При отклонениях консультироваться с врачом

## 📅 План следующих анализов

- **Следующий плановый анализ:** {(datetime.now() + timedelta(days=180)).strftime('%d.%m.%Y')}
- **Контрольные анализы при лечении:** по назначению врача

## 📊 Графики трендов

[Графики сохраняются в папке Docs/Health/trends/]

---
*Отчет создан автоматически на основе данных анализов*
"""
    
    # Сохраняем отчет
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📋 Отчет по здоровью сохранен: {output_path}")
    
    return parameter_analyses

def main():
    parser = argparse.ArgumentParser(description='Анализатор трендов медицинских показателей')
    parser.add_argument('--parameter', help='Анализировать конкретный параметр')
    parser.add_argument('--report', action='store_true', help='Создать общий отчет по здоровью')
    parser.add_argument('--records-dir', default='Docs/Health/lab_results', help='Папка с записями анализов')
    
    args = parser.parse_args()
    
    # Загружаем записи
    records = load_medical_records(args.records_dir)
    
    if not records:
        print("📊 Нет данных для анализа")
        print("💡 Сначала используйте medical_pdf_parser.py для обработки PDF файлов анализов")
        return
    
    print(f"📊 Загружено {len(records)} записей анализов")
    
    df = create_trends_dataframe(records)
    
    if args.parameter:
        # Анализируем конкретный параметр
        analysis = analyze_parameter_trend(df, args.parameter)
        
        if analysis:
            print(f"\n📈 Анализ параметра: {args.parameter}")
            print(f"Количество измерений: {analysis['count']}")
            print(f"Период: {analysis['first_date'].strftime('%d.%m.%Y')} - {analysis['last_date'].strftime('%d.%m.%Y')}")
            print(f"Текущее значение: {analysis['last_value']} {analysis['unit']}")
            
            if analysis.get('trend'):
                print(f"Тренд: {analysis['trend']}")
                print(f"Изменение: {analysis['change_absolute']:+.1f} {analysis['unit']} ({analysis['change_percent']:+.1f}%)")
            
            print(f"Нарушений нормы: {analysis['violations_count']}/{analysis['count']} ({analysis['violations_percent']:.1f}%)")
            
            # Создаем график
            chart_path = create_trend_visualization(df, args.parameter)
            if chart_path:
                print(f"📊 График сохранен: {chart_path}")
        else:
            print(f"❌ Параметр {args.parameter} не найден")
    
    elif args.report:
        # Создаем общий отчет
        generate_health_report(records)
        
        # Создаем графики для всех параметров
        parameters = df['parameter'].unique()
        print(f"\n📊 Создаю графики для {len(parameters)} параметров...")
        
        for param in parameters:
            chart_path = create_trend_visualization(df, param)
            if chart_path:
                print(f"📈 График {param}: {chart_path.name}")
    
    else:
        # Показываем общую статистику
        parameters = df['parameter'].unique()
        print(f"\n📊 Доступные параметры ({len(parameters)}):")
        
        for i, param in enumerate(parameters, 1):
            param_data = df[df['parameter'] == param]
            print(f"{i:2d}. {param.replace('_', ' ').title()} ({len(param_data)} измерений)")
        
        print(f"\n💡 Примеры использования:")
        print(f"   python scripts/health_trend_analyzer.py --parameter glucose")
        print(f"   python scripts/health_trend_analyzer.py --report")

if __name__ == "__main__":
    main()
