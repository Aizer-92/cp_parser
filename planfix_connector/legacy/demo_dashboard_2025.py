#!/usr/bin/env python3
"""
Демонстрационный дашборд Planfix 2025
Современный дизайн с тестовыми данными и правильным расчетом приоритетов
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class DemoDashboard2025:
    def __init__(self):
        self.db_path = 'output/planfix_tasks_correct.db'
        self.app = Flask(__name__)
        self.setup_routes()
        
    def calculate_priority(self, client_grade, order_percent, calculation_sum):
        """Расчет приоритета по формуле"""
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
            return "D", 0.0
    
    def generate_demo_data(self):
        """Генерация демонстрационных данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            tasks_df = pd.read_sql_query('''
                SELECT id, name, status_name, assigner, assignees, start_date_time
                FROM tasks
                LIMIT 100
            ''', conn)
            conn.close()
            
            # Генерируем демонстрационные данные
            demo_tasks = []
            priority_stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
            
            for _, task in tasks_df.iterrows():
                # Генерируем случайные значения для демонстрации
                client_grade = random.randint(1, 5)
                order_percent = random.randint(10, 100)
                calculation_sum = random.choice([
                    random.randint(100000, 250000),
                    random.randint(250000, 1000000),
                    random.randint(1000000, 5000000),
                    random.randint(5000000, 10000000),
                    random.randint(10000000, 50000000)
                ])
                
                # Рассчитываем приоритет
                priority, score = self.calculate_priority(client_grade, order_percent, calculation_sum)
                priority_stats[priority] += 1
                
                # Парсим дату
                create_date = None
                if task['start_date_time']:
                    try:
                        create_date = datetime.fromisoformat(task['start_date_time'].replace('Z', '+00:00'))
                    except:
                        create_date = datetime.now() - timedelta(days=random.randint(1, 30))
                else:
                    create_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                demo_task = {
                    'id': task['id'],
                    'name': task['name'],
                    'status': task['status_name'],
                    'assigner': task['assigner'],
                    'assignees': task['assignees'],
                    'create_date': create_date,
                    'client_grade': client_grade,
                    'order_percent': order_percent,
                    'calculation_sum': calculation_sum,
                    'priority': priority,
                    'priority_score': score
                }
                
                demo_tasks.append(demo_task)
            
            return demo_tasks, priority_stats
            
        except Exception as e:
            print(f"Ошибка генерации данных: {e}")
            return [], {}
    
    def calculate_analytics(self, tasks):
        """Расчет аналитики"""
        if not tasks:
            return {}
        
        # Базовые метрики
        total_tasks = len(tasks)
        
        # Статистика по статусам
        status_stats = {}
        for task in tasks:
            status = task['status']
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # Статистика по грейдам клиентов
        grade_stats = {}
        for task in tasks:
            grade = task['client_grade']
            grade_stats[grade] = grade_stats.get(grade, 0) + 1
        
        # Статистика по суммам просчетов
        sum_ranges = {
            '0-250k': 0,
            '250k-1M': 0,
            '1M-5M': 0,
            '5M-10M': 0,
            '10M+': 0
        }
        
        for task in tasks:
            sum_val = task['calculation_sum']
            if sum_val <= 250000:
                sum_ranges['0-250k'] += 1
            elif sum_val <= 1000000:
                sum_ranges['250k-1M'] += 1
            elif sum_val <= 5000000:
                sum_ranges['1M-5M'] += 1
            elif sum_val <= 10000000:
                sum_ranges['5M-10M'] += 1
            else:
                sum_ranges['10M+'] += 1
        
        # Временная аналитика
        daily_stats = {}
        weekly_stats = {}
        monthly_stats = {}
        hourly_stats = {}
        weekday_stats = {}
        
        for task in tasks:
            date = task['create_date']
            
            # По дням
            day_key = date.date()
            daily_stats[day_key] = daily_stats.get(day_key, 0) + 1
            
            # По неделям
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.date()
            weekly_stats[week_key] = weekly_stats.get(week_key, 0) + 1
            
            # По месяцам
            month_start = date.replace(day=1)
            month_key = month_start.date()
            monthly_stats[month_key] = monthly_stats.get(month_key, 0) + 1
            
            # По часам
            hour = date.hour
            hourly_stats[hour] = hourly_stats.get(hour, 0) + 1
            
            # По дням недели
            weekday = date.weekday()
            weekday_stats[weekday] = weekday_stats.get(weekday, 0) + 1
        
        # Топ задачи по приоритету
        high_priority_tasks = sorted(
            [t for t in tasks if t['priority'] in ['A', 'B']],
            key=lambda x: (x['priority'], x['calculation_sum']),
            reverse=True
        )[:20]
        
        # Финансовая аналитика
        total_sum = sum(t['calculation_sum'] for t in tasks)
        avg_sum = total_sum / len(tasks) if tasks else 0
        avg_percent = sum(t['order_percent'] for t in tasks) / len(tasks) if tasks else 0
        
        return {
            'total_tasks': total_tasks,
            'status_stats': status_stats,
            'grade_stats': grade_stats,
            'sum_ranges': sum_ranges,
            'daily_stats': daily_stats,
            'weekly_stats': weekly_stats,
            'monthly_stats': monthly_stats,
            'hourly_stats': hourly_stats,
            'weekday_stats': weekday_stats,
            'high_priority_tasks': high_priority_tasks,
            'financial_metrics': {
                'total_sum': total_sum,
                'avg_sum': avg_sum,
                'avg_percent': avg_percent
            },
            'recent_tasks': sorted(tasks, key=lambda x: x['create_date'], reverse=True)[:10]
        }
    
    def setup_routes(self):
        """Настройка маршрутов"""
        @self.app.route('/')
        def dashboard():
            return self.get_dashboard_html()
        
        @self.app.route('/api/data')
        def get_data():
            return jsonify(self.get_demo_data())
    
    def get_demo_data(self):
        """Получение демонстрационных данных"""
        tasks, priority_stats = self.generate_demo_data()
        return self.calculate_analytics(tasks)
    
    def get_dashboard_html(self):
        """Создание HTML дашборда"""
        data = self.get_demo_data()
        tasks, priority_stats = self.generate_demo_data()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Planfix Dashboard 2025 - Демо</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1920px;
            margin: 0 auto;
            padding: 20px;
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
            font-weight: 400;
        }}
        
        .demo-badge {{
            background: linear-gradient(135deg, #ff6b6b, #feca57);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            display: inline-block;
            margin-top: 16px;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }}
        
        .kpi-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 32px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }}
        
        .kpi-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .kpi-number {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .kpi-label {{
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #ffffff;
        }}
        
        .priority-a {{ color: #ff6b6b; font-weight: 600; }}
        .priority-b {{ color: #feca57; font-weight: 600; }}
        .priority-c {{ color: #48dbfb; font-weight: 600; }}
        .priority-d {{ color: #a8e6cf; font-weight: 600; }}
        
        .tasks-table {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 32px;
        }}
        
        .table-container {{
            overflow-x: auto;
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
        
        .refresh-btn {{
            position: fixed;
            bottom: 32px;
            right: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            width: 64px;
            height: 64px;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }}
        
        .refresh-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.6);
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
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Planfix Dashboard 2025</h1>
            <p>Профессиональная бизнес-аналитика в реальном времени</p>
            <div class="demo-badge">🎯 Демо-версия с тестовыми данными</div>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-number">{data.get('total_tasks', 0):,}</div>
                <div class="kpi-label">Всего задач</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-number">{priority_stats.get('A', 0)}</div>
                <div class="kpi-label">Приоритет A</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-number">{priority_stats.get('B', 0)}</div>
                <div class="kpi-label">Приоритет B</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-number">{data.get('financial_metrics', {}).get('total_sum', 0):,.0f} ₽</div>
                <div class="kpi-label">Общая сумма</div>
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
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">📊 Распределение по приоритетам</div>
                <canvas id="priorityChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">📈 Статусы задач</div>
                <canvas id="statusChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">💰 Распределение по суммам</div>
                <canvas id="sumChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">👥 Грейды клиентов</div>
                <canvas id="gradeChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="tasks-table">
            <div class="chart-title">🎯 Высокоприоритетные задачи (A & B)</div>
            <div class="table-container">
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
        high_priority_tasks = data.get('high_priority_tasks', [])
        for task in high_priority_tasks[:10]:
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
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄</button>
    
    <script>
        // Инициализация графиков
        const priorityData = {
            labels: ['A', 'B', 'C', 'D'],
            datasets: [{
                data: [
                    """ + str(priority_stats.get('A', 0)) + """,
                    """ + str(priority_stats.get('B', 0)) + """,
                    """ + str(priority_stats.get('C', 0)) + """,
                    """ + str(priority_stats.get('D', 0)) + """
                ],
                backgroundColor: [
                    'rgba(255, 107, 107, 0.8)',
                    'rgba(254, 202, 87, 0.8)',
                    'rgba(72, 219, 251, 0.8)',
                    'rgba(168, 230, 207, 0.8)'
                ],
                borderColor: [
                    'rgba(255, 107, 107, 1)',
                    'rgba(254, 202, 87, 1)',
                    'rgba(72, 219, 251, 1)',
                    'rgba(168, 230, 207, 1)'
                ],
                borderWidth: 2
            }]
        };
        
        const statusData = {
            labels: """ + json.dumps(list(data.get('status_stats', {}).keys())) + """,
            datasets: [{
                data: """ + json.dumps(list(data.get('status_stats', {}).values())) + """,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2
            }]
        };
        
        const sumData = {
            labels: ['0-250k', '250k-1M', '1M-5M', '5M-10M', '10M+'],
            datasets: [{
                data: """ + json.dumps(list(data.get('sum_ranges', {}).values())) + """,
                backgroundColor: 'rgba(118, 75, 162, 0.8)',
                borderColor: 'rgba(118, 75, 162, 1)',
                borderWidth: 2
            }]
        };
        
        const gradeData = {
            labels: """ + json.dumps([f'Грейд {i}' for i in range(1, 6)]) + """,
            datasets: [{
                data: """ + json.dumps([data.get('grade_stats', {}).get(i, 0) for i in range(1, 6)]) + """,
                backgroundColor: 'rgba(255, 193, 7, 0.8)',
                borderColor: 'rgba(255, 193, 7, 1)',
                borderWidth: 2
            }]
        };
        
        // Создание графиков
        new Chart(document.getElementById('priorityChart'), {
            type: 'doughnut',
            data: priorityData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            font: {
                                family: 'Inter'
                            }
                        }
                    }
                }
            }
        });
        
        new Chart(document.getElementById('statusChart'), {
            type: 'bar',
            data: statusData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
        
        new Chart(document.getElementById('sumChart'), {
            type: 'bar',
            data: sumData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
        
        new Chart(document.getElementById('gradeChart'), {
            type: 'bar',
            data: gradeData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
        
        function refreshData() {{
            location.reload();
        }}
        
        // Автообновление каждые 5 минут
        setInterval(refreshData, 300000);
    </script>
</body>
</html>
        """
        
        return html_content
    
    def run(self, host='0.0.0.0', port=8055, debug=False):
        """Запуск дашборда"""
        print("🚀 Запуск демонстрационного дашборда Planfix 2025...")
        print(f"🌐 Откройте браузер: http://localhost:{port}")
        print("⏰ Дашборд будет автоматически обновляться каждые 5 минут")
        print("🎯 Используются демонстрационные данные с правильным расчетом приоритетов")
        self.app.run(host=host, port=port, debug=debug)

def main():
    dashboard = DemoDashboard2025()
    dashboard.run()

if __name__ == "__main__":
    main()
