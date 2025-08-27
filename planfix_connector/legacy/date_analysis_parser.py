#!/usr/bin/env python3
"""
Анализатор дат создания задач Planfix
Фокус на распределение по датам постановки задач на просчет
"""

import sqlite3
import json
import requests
from datetime import datetime, timedelta
import os
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter
import numpy as np

class DateAnalysisParser:
    def __init__(self):
        self.config = self.load_config()
        self.db_path = 'output/planfix_tasks_correct.db'
        self.output_dir = 'output'
        
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open('planfix_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return None
    
    def get_tasks_with_creation_dates(self):
        """Получение задач с датами создания из API"""
        print("🔍 Получение задач с датами создания из API...")
        
        headers = {
            'Authorization': f'Bearer {self.config["rest_api"]["auth_token"]}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.config['rest_api']['base_url']}/task/list"
        
        all_tasks = []
        offset = 0
        page_size = 100
        
        while True:
            request_data = {
                "offset": offset,
                "pageSize": page_size,
                "filters": [
                    {
                        "type": 10,  # Статус
                        "operator": "equal",
                        "value": [127, 128, 129]  # Статусы: Поиск, Согласование, Согласовано
                    }
                ],
                "fields": "id,name,description,status,startDateTime,endDateTime,deadline,assigner,assignees,priority,importance,workTime,planTime,factTime,createDate,modifyDate,closeDate,startDate,finishDate"
            }
            
            try:
                print(f"  📊 Получение задач (offset: {offset}, pageSize: {page_size})...")
                
                response = requests.post(url, headers=headers, json=request_data)
                response.raise_for_status()
                
                data = response.json()
                if 'tasks' in data:
                    tasks = data['tasks']
                    print(f"    ✅ Получено {len(tasks)} задач")
                    
                    if not tasks:
                        break
                    
                    # Извлекаем данные с датами создания
                    for task in tasks:
                        task_data = self.extract_task_with_dates(task)
                        if task_data:
                            all_tasks.append(task_data)
                    
                    if len(tasks) < page_size:
                        break
                    
                    offset += page_size
                    
                    if offset > 1000:  # Защита от бесконечного цикла
                        print("⚠️ Достигнут лимит offset (1000)")
                        break
                else:
                    print(f"    ⚠️ Нет поля 'tasks' в ответе")
                    break
                    
            except Exception as e:
                print(f"    ❌ Ошибка получения задач: {e}")
                break
        
        print(f"📅 Всего задач с датами создания: {len(all_tasks)}")
        return all_tasks
    
    def extract_task_with_dates(self, task):
        """Извлечение данных задачи с датами"""
        try:
            task_id = task.get('id')
            name = task.get('name', '')
            status = task.get('status', {})
            status_name = status.get('name', 'Неизвестно') if status else 'Неизвестно'
            
            # Даты создания и изменения
            create_date = task.get('createDate')
            modify_date = task.get('modifyDate')
            start_date = task.get('startDateTime')
            end_date = task.get('endDateTime')
            deadline = task.get('deadline')
            
            # Приоритеты
            priority = task.get('priority', 0)
            importance = task.get('importance', 0)
            
            # Исполнители
            assignees = task.get('assignees', [])
            assignees_names = [a.get('name', '') for a in assignees] if assignees else []
            assigner = task.get('assigner', {})
            assigner_name = assigner.get('name', '') if assigner else ''
            
            # Время
            work_time = task.get('workTime', 0)
            plan_time = task.get('planTime', 0)
            fact_time = task.get('factTime', 0)
            
            return {
                'id': task_id,
                'name': name,
                'status_name': status_name,
                'create_date': create_date,
                'modify_date': modify_date,
                'start_date': start_date,
                'end_date': end_date,
                'deadline': deadline,
                'priority': priority,
                'importance': importance,
                'assignees': assignees_names,
                'assigner': assigner_name,
                'work_time': work_time,
                'plan_time': plan_time,
                'fact_time': fact_time
            }
        except Exception as e:
            print(f"    ❌ Ошибка извлечения данных задачи {task.get('id', 'unknown')}: {e}")
            return None
    
    def analyze_creation_dates(self, tasks):
        """Анализ дат создания задач"""
        print("📊 Анализ дат создания задач...")
        
        # Преобразуем даты
        for task in tasks:
            if task['create_date']:
                try:
                    # Парсим дату создания
                    create_date = datetime.fromisoformat(task['create_date'].replace('Z', '+00:00'))
                    task['create_date_parsed'] = create_date
                    task['create_date_only'] = create_date.date()
                except:
                    task['create_date_parsed'] = None
                    task['create_date_only'] = None
            
            if task['modify_date']:
                try:
                    modify_date = datetime.fromisoformat(task['modify_date'].replace('Z', '+00:00'))
                    task['modify_date_parsed'] = modify_date
                except:
                    task['modify_date_parsed'] = None
        
        # Фильтруем задачи с валидными датами создания
        valid_tasks = [t for t in tasks if t['create_date_parsed'] is not None]
        print(f"✅ Задач с валидными датами создания: {len(valid_tasks)}")
        
        # Анализ по дням
        daily_stats = defaultdict(int)
        for task in valid_tasks:
            date_key = task['create_date_only']
            daily_stats[date_key] += 1
        
        # Анализ по неделям
        weekly_stats = defaultdict(int)
        for task in valid_tasks:
            week_start = task['create_date_parsed'] - timedelta(days=task['create_date_parsed'].weekday())
            week_key = week_start.date()
            weekly_stats[week_key] += 1
        
        # Анализ по месяцам
        monthly_stats = defaultdict(int)
        for task in valid_tasks:
            month_key = task['create_date_parsed'].replace(day=1).date()
            monthly_stats[month_key] += 1
        
        # Анализ по часам дня
        hourly_stats = defaultdict(int)
        for task in valid_tasks:
            hour = task['create_date_parsed'].hour
            hourly_stats[hour] += 1
        
        # Анализ по дням недели
        weekday_stats = defaultdict(int)
        for task in valid_tasks:
            weekday = task['create_date_parsed'].weekday()
            weekday_stats[weekday] += 1
        
        return {
            'daily_stats': dict(daily_stats),
            'weekly_stats': dict(weekly_stats),
            'monthly_stats': dict(monthly_stats),
            'hourly_stats': dict(hourly_stats),
            'weekday_stats': dict(weekday_stats),
            'valid_tasks': valid_tasks
        }
    
    def create_date_analysis_report(self, analysis_data):
        """Создание отчета по анализу дат"""
        print("📄 Создание отчета по анализу дат...")
        
        valid_tasks = analysis_data['valid_tasks']
        
        # Создаем DataFrame для анализа
        df = pd.DataFrame(valid_tasks)
        
        # Сортируем по дате создания
        df = df.sort_values('create_date_parsed')
        
        # Статистика
        total_tasks = len(valid_tasks)
        date_range = df['create_date_parsed'].max() - df['create_date_parsed'].min()
        avg_tasks_per_day = total_tasks / max(date_range.days, 1)
        
        # Топ дней по количеству задач
        daily_df = pd.DataFrame(list(analysis_data['daily_stats'].items()), 
                              columns=['date', 'count'])
        daily_df = daily_df.sort_values('count', ascending=False)
        
        # Топ недель
        weekly_df = pd.DataFrame(list(analysis_data['weekly_stats'].items()), 
                               columns=['week_start', 'count'])
        weekly_df = weekly_df.sort_values('count', ascending=False)
        
        # Топ месяцев
        monthly_df = pd.DataFrame(list(analysis_data['monthly_stats'].items()), 
                                columns=['month_start', 'count'])
        monthly_df = monthly_df.sort_values('count', ascending=False)
        
        # Создаем HTML отчет
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📅 Анализ дат создания задач Planfix</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border-left: 5px solid #667eea;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 1.1em;
            color: #666;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }}
        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 10px;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Анализ дат создания задач</h1>
            <p>Распределение задач по датам постановки на просчет</p>
        </div>
        
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_tasks}</div>
                    <div class="stat-label">Всего задач</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{date_range.days}</div>
                    <div class="stat-label">Дней в периоде</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{avg_tasks_per_day:.1f}</div>
                    <div class="stat-label">Среднее задач в день</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{daily_df['count'].max() if not daily_df.empty else 0}</div>
                    <div class="stat-label">Максимум задач в день</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Топ дней по количеству задач</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Добавляем топ дней
        for _, row in daily_df.head(20).iterrows():
            date_str = row['date'].strftime('%d.%m.%Y')
            count = row['count']
            percentage = (count / total_tasks) * 100
            html_content += f"""
                            <tr>
                                <td><strong>{date_str}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Топ недель по количеству задач</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Неделя (начало)</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Добавляем топ недель
        for _, row in weekly_df.head(15).iterrows():
            week_str = row['week_start'].strftime('%d.%m.%Y')
            count = row['count']
            percentage = (count / total_tasks) * 100
            html_content += f"""
                            <tr>
                                <td><strong>{week_str}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📅 Топ месяцев по количеству задач</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Месяц</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Добавляем топ месяцев
        for _, row in monthly_df.head(12).iterrows():
            month_str = row['month_start'].strftime('%B %Y')
            count = row['count']
            percentage = (count / total_tasks) * 100
            html_content += f"""
                            <tr>
                                <td><strong>{month_str}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>🕐 Распределение по часам дня</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Час</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Добавляем распределение по часам
        for hour in range(24):
            count = analysis_data['hourly_stats'].get(hour, 0)
            percentage = (count / total_tasks) * 100 if total_tasks > 0 else 0
            html_content += f"""
                            <tr>
                                <td><strong>{hour:02d}:00</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📅 Распределение по дням недели</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>День недели</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Добавляем распределение по дням недели
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        for i, weekday in enumerate(weekdays):
            count = analysis_data['weekday_stats'].get(i, 0)
            percentage = (count / total_tasks) * 100 if total_tasks > 0 else 0
            html_content += f"""
                            <tr>
                                <td><strong>{weekday}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Последние задачи</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Название</th>
                                <th>Статус</th>
                                <th>Дата создания</th>
                                <th>Постановщик</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Добавляем последние задачи
        recent_tasks = sorted(valid_tasks, key=lambda x: x['create_date_parsed'], reverse=True)[:20]
        for task in recent_tasks:
            create_date_str = task['create_date_parsed'].strftime('%d.%m.%Y %H:%M')
            html_content += f"""
                            <tr>
                                <td><strong>{task['id']}</strong></td>
                                <td>{task['name'][:50]}{'...' if len(task['name']) > 50 else ''}</td>
                                <td>{task['status_name']}</td>
                                <td>{create_date_str}</td>
                                <td>{task['assigner']}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="highlight">
                <h3>💡 Ключевые выводы:</h3>
                <ul>
                    <li><strong>Пиковые дни:</strong> Наибольшая активность по постановке задач</li>
                    <li><strong>Рабочие часы:</strong> Распределение по времени суток</li>
                    <li><strong>Недельная динамика:</strong> Активность по дням недели</li>
                    <li><strong>Месячные тренды:</strong> Сезонность в постановке задач</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        # Сохраняем HTML отчет
        html_path = os.path.join(self.output_dir, 'date_analysis_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML отчет создан: {html_path}")
        
        # Создаем Excel отчет
        excel_path = os.path.join(self.output_dir, 'date_analysis_report.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Основные данные
            df[['id', 'name', 'status_name', 'create_date_parsed', 'assigner', 'priority']].to_excel(
                writer, sheet_name='Все задачи', index=False)
            
            # Дневная статистика
            daily_df.to_excel(writer, sheet_name='По дням', index=False)
            
            # Недельная статистика
            weekly_df.to_excel(writer, sheet_name='По неделям', index=False)
            
            # Месячная статистика
            monthly_df.to_excel(writer, sheet_name='По месяцам', index=False)
            
            # По часам
            hourly_df = pd.DataFrame(list(analysis_data['hourly_stats'].items()), 
                                   columns=['hour', 'count'])
            hourly_df = hourly_df.sort_values('hour')
            hourly_df.to_excel(writer, sheet_name='По часам', index=False)
            
            # По дням недели
            weekday_df = pd.DataFrame(list(analysis_data['weekday_stats'].items()), 
                                    columns=['weekday_num', 'count'])
            weekday_df['weekday_name'] = weekday_df['weekday_num'].map({
                0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 
                3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
            })
            weekday_df = weekday_df.sort_values('weekday_num')
            weekday_df.to_excel(writer, sheet_name='По дням недели', index=False)
        
        print(f"✅ Excel отчет создан: {excel_path}")
        
        return html_path, excel_path
    
    def run_date_analysis(self):
        """Запуск полного анализа дат"""
        print("🚀 Запуск анализа дат создания задач")
        print("=" * 80)
        
        # Получаем задачи с датами
        tasks = self.get_tasks_with_creation_dates()
        
        if not tasks:
            print("❌ Не удалось получить задачи")
            return
        
        # Анализируем даты
        analysis_data = self.analyze_creation_dates(tasks)
        
        if not analysis_data['valid_tasks']:
            print("❌ Нет задач с валидными датами создания")
            return
        
        # Создаем отчеты
        html_path, excel_path = self.create_date_analysis_report(analysis_data)
        
        print("\n🎉 Анализ дат завершен успешно!")
        print(f"📊 Обработано задач: {len(analysis_data['valid_tasks'])}")
        print(f"📄 HTML отчет: {html_path}")
        print(f"📊 Excel отчет: {excel_path}")
        
        # Показываем ключевую статистику
        daily_stats = analysis_data['daily_stats']
        if daily_stats:
            max_day = max(daily_stats.items(), key=lambda x: x[1])
            print(f"📅 Максимум задач в день: {max_day[1]} ({max_day[0].strftime('%d.%m.%Y')})")
        
        return html_path, excel_path

def main():
    parser = DateAnalysisParser()
    parser.run_date_analysis()

if __name__ == "__main__":
    main()
