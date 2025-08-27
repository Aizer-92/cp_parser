#!/usr/bin/env python3
"""
Калькулятор приоритетов Planfix
Правильный расчет приоритетов по формуле бизнес-аналитика
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
import os

class PriorityCalculator:
    def __init__(self):
        self.db_path = 'output/planfix_tasks_correct.db'
        self.output_dir = 'output'
        
    def calculate_priority_formula(self, client_grade, order_percent, calculation_sum):
        """
        Расчет приоритета по формуле:
        (0.4 * (client_grade / 5) + 0.4 * sum_factor + 0.2 * (order_percent / 100))
        """
        try:
            # Нормализация грейда клиента (1-5)
            client_grade = float(client_grade) if client_grade and client_grade != '' else 3.0
            client_grade = max(1, min(5, client_grade))
            
            # Нормализация % заказа (0-100)
            order_percent = float(order_percent) if order_percent and order_percent != '' else 50.0
            order_percent = max(0, min(100, order_percent))
            
            # Нормализация суммы просчета
            calculation_sum = float(calculation_sum) if calculation_sum and calculation_sum != '' else 1000000
            
            # Фактор суммы просчета
            if calculation_sum <= 250000:
                sum_factor = 0.2
            elif calculation_sum <= 1000000:
                sum_factor = 0.4
            elif calculation_sum <= 5000000:
                sum_factor = 0.6
            elif calculation_sum <= 10000000:
                sum_factor = 0.8
            else:
                sum_factor = 1.0
            
            # Расчет итогового приоритета
            priority_score = (
                0.4 * (client_grade / 5) +
                0.4 * sum_factor +
                0.2 * (order_percent / 100)
            )
            
            # Определение приоритета
            if priority_score >= 0.8:
                return "A", priority_score
            elif priority_score >= 0.6:
                return "B", priority_score
            elif priority_score >= 0.4:
                return "C", priority_score
            else:
                return "D", priority_score
                
        except Exception as e:
            print(f"Ошибка расчета приоритета: {e}")
            return "D", 0.0
    
    def get_tasks_with_custom_fields(self):
        """Получение задач с кастомными полями"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем все задачи
            tasks_df = pd.read_sql_query('''
                SELECT id, name, status_name, assigner, assignees, 
                       start_date_time, export_timestamp
                FROM tasks
            ''', conn)
            
            # Получаем кастомные поля
            custom_fields_df = pd.read_sql_query('''
                SELECT task_id, field_name, field_value
                FROM custom_field_values
            ''', conn)
            
            conn.close()
            
            return tasks_df, custom_fields_df
            
        except Exception as e:
            print(f"Ошибка получения данных: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def process_priorities(self):
        """Обработка приоритетов для всех задач"""
        print("🔍 Получение задач с кастомными полями...")
        
        tasks_df, custom_fields_df = self.get_tasks_with_custom_fields()
        
        if tasks_df.empty:
            print("❌ Нет задач для обработки")
            return
        
        print(f"✅ Получено {len(tasks_df)} задач")
        
        # Создаем словарь кастомных полей
        custom_fields_dict = {}
        for _, row in custom_fields_df.iterrows():
            task_id = row['task_id']
            field_name = row['field_name']
            field_value = row['field_value']
            
            if task_id not in custom_fields_dict:
                custom_fields_dict[task_id] = {}
            custom_fields_dict[task_id][field_name] = field_value
        
        # Обрабатываем задачи
        processed_tasks = []
        priority_stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        
        for _, task in tasks_df.iterrows():
            task_id = task['id']
            custom_fields = custom_fields_dict.get(task_id, {})
            
            # Извлекаем нужные поля
            client_grade = custom_fields.get('Грейд клиента', 3)
            order_percent = custom_fields.get('% заказа', 50)
            calculation_sum = custom_fields.get('Сумма просчета', 1000000)
            
            # Рассчитываем приоритет
            priority, score = self.calculate_priority_formula(client_grade, order_percent, calculation_sum)
            priority_stats[priority] += 1
            
            # Парсим дату
            create_date = None
            if task['start_date_time']:
                try:
                    create_date = datetime.fromisoformat(task['start_date_time'].replace('Z', '+00:00'))
                except:
                    pass
            
            processed_task = {
                'id': task_id,
                'name': task['name'],
                'status': task['status_name'],
                'assigner': task['assigner'],
                'assignees': task['assignees'],
                'create_date': create_date,
                'client_grade': client_grade,
                'order_percent': order_percent,
                'calculation_sum': calculation_sum,
                'priority': priority,
                'priority_score': score,
                'custom_fields': custom_fields
            }
            
            processed_tasks.append(processed_task)
        
        print("📊 Статистика приоритетов:")
        for priority, count in priority_stats.items():
            percentage = (count / len(processed_tasks)) * 100
            print(f"  {priority}: {count} ({percentage:.1f}%)")
        
        return processed_tasks
    
    def create_priority_report(self, processed_tasks):
        """Создание отчета по приоритетам"""
        print("📄 Создание отчета по приоритетам...")
        
        # Фильтруем задачи с валидными датами
        valid_tasks = [t for t in processed_tasks if t['create_date'] is not None]
        
        if not valid_tasks:
            print("❌ Нет задач с валидными датами")
            return
        
        # Создаем DataFrame
        df = pd.DataFrame(valid_tasks)
        
        # Сортируем по приоритету и сумме
        df = df.sort_values(['priority', 'calculation_sum'], ascending=[True, False])
        
        # Топ высокоприоритетные задачи
        high_priority = df[df['priority'].isin(['A', 'B'])].head(20)
        
        # Создаем HTML отчет
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Анализ приоритетов Planfix</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 32px;
            margin-bottom: 32px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        
        .header p {{
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.7);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .stat-label {{
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .priority-a {{ color: #ff6b6b; }}
        .priority-b {{ color: #feca57; }}
        .priority-c {{ color: #48dbfb; }}
        .priority-d {{ color: #a8e6cf; }}
        
        .table-container {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 32px;
        }}
        
        .table-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #ffffff;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: rgba(255, 255, 255, 0.1);
            padding: 16px;
            text-align: left;
            font-weight: 600;
            color: #ffffff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        td {{
            padding: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.8);
        }}
        
        tr:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .formula-box {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 32px;
        }}
        
        .formula-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 16px;
            color: #ffffff;
        }}
        
        .formula-text {{
            font-family: 'Courier New', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 16px;
            border-radius: 12px;
            color: #48dbfb;
            font-size: 0.9rem;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Анализ приоритетов</h1>
            <p>Правильный расчет приоритетов по формуле бизнес-аналитика</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number priority-a">{len(df[df['priority'] == 'A'])}</div>
                <div class="stat-label">Приоритет A</div>
            </div>
            <div class="stat-card">
                <div class="stat-number priority-b">{len(df[df['priority'] == 'B'])}</div>
                <div class="stat-label">Приоритет B</div>
            </div>
            <div class="stat-card">
                <div class="stat-number priority-c">{len(df[df['priority'] == 'C'])}</div>
                <div class="stat-label">Приоритет C</div>
            </div>
            <div class="stat-card">
                <div class="stat-number priority-d">{len(df[df['priority'] == 'D'])}</div>
                <div class="stat-label">Приоритет D</div>
            </div>
        </div>
        
        <div class="formula-box">
            <div class="formula-title">📐 Формула расчета приоритета</div>
            <div class="formula-text">
Приоритет = (0.4 × (Грейд клиента / 5) + 0.4 × Фактор суммы + 0.2 × (% заказа / 100))

Фактор суммы:
• ≤ 250k: 0.2
• ≤ 1M: 0.4  
• ≤ 5M: 0.6
• ≤ 10M: 0.8
• > 10M: 1.0

Классификация:
• ≥ 0.8: A (Высокий)
• ≥ 0.6: B (Средний)
• ≥ 0.4: C (Низкий)
• < 0.4: D (Минимальный)
            </div>
        </div>
        
        <div class="table-container">
            <div class="table-title">🎯 Топ высокоприоритетные задачи (A & B)</div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Название</th>
                        <th>Приоритет</th>
                        <th>Счет</th>
                        <th>Сумма</th>
                        <th>Грейд</th>
                        <th>% заказа</th>
                        <th>Статус</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Добавляем высокоприоритетные задачи
        for _, task in high_priority.iterrows():
            html_content += f"""
                    <tr>
                        <td><strong>{task['id']}</strong></td>
                        <td>{task['name'][:50]}{'...' if len(task['name']) > 50 else ''}</td>
                        <td><span class="priority-{task['priority'].lower()}">{task['priority']}</span></td>
                        <td>{task['priority_score']:.3f}</td>
                        <td>{task['calculation_sum']:,.0f} ₽</td>
                        <td>{task['client_grade']}</td>
                        <td>{task['order_percent']}%</td>
                        <td>{task['status']}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        
        # Сохраняем HTML отчет
        html_path = os.path.join(self.output_dir, 'priority_analysis_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML отчет создан: {html_path}")
        
        # Создаем Excel отчет
        excel_path = os.path.join(self.output_dir, 'priority_analysis_report.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Все задачи с приоритетами
            df[['id', 'name', 'priority', 'priority_score', 'calculation_sum', 'client_grade', 'order_percent', 'status']].to_excel(
                writer, sheet_name='Все задачи', index=False)
            
            # Высокоприоритетные задачи
            high_priority.to_excel(writer, sheet_name='Приоритет A&B', index=False)
            
            # Статистика по приоритетам
            priority_summary = df.groupby('priority').agg({
                'id': 'count',
                'calculation_sum': ['sum', 'mean'],
                'order_percent': 'mean'
            }).round(2)
            priority_summary.to_excel(writer, sheet_name='Статистика')
        
        print(f"✅ Excel отчет создан: {excel_path}")
        
        return html_path, excel_path
    
    def run_analysis(self):
        """Запуск анализа приоритетов"""
        print("🚀 Запуск анализа приоритетов Planfix")
        print("=" * 80)
        
        # Обрабатываем приоритеты
        processed_tasks = self.process_priorities()
        
        if not processed_tasks:
            print("❌ Не удалось обработать задачи")
            return
        
        # Создаем отчеты
        html_path, excel_path = self.create_priority_report(processed_tasks)
        
        print("\n🎉 Анализ приоритетов завершен успешно!")
        print(f"📊 Обработано задач: {len(processed_tasks)}")
        print(f"📄 HTML отчет: {html_path}")
        print(f"📊 Excel отчет: {excel_path}")

def main():
    calculator = PriorityCalculator()
    calculator.run_analysis()

if __name__ == "__main__":
    main()
