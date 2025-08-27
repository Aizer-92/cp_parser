#!/usr/bin/env python3
"""
Упрощенный анализатор дат создания задач Planfix
Работает с существующей базой данных
"""

import sqlite3
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

class SimpleDateAnalyzer:
    def __init__(self):
        self.db_path = 'output/planfix_tasks_correct.db'
        self.output_dir = 'output'
        
    def get_tasks_from_db(self):
        """Получение задач из базы данных"""
        print("🔍 Получение задач из базы данных...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем все задачи с датами
            cursor.execute('''
                SELECT id, name, status_name, assigner, assignees, 
                       start_date_time, export_timestamp
                FROM tasks 
                WHERE start_date_time IS NOT NULL
                ORDER BY start_date_time DESC
            ''')
            
            tasks = cursor.fetchall()
            conn.close()
            
            print(f"✅ Получено {len(tasks)} задач с датами из базы данных")
            return tasks
            
        except Exception as e:
            print(f"❌ Ошибка получения данных из БД: {e}")
            return []
    
    def analyze_creation_dates(self, tasks):
        """Анализ дат создания задач"""
        print("📊 Анализ дат создания задач...")
        
        # Преобразуем данные в удобный формат
        processed_tasks = []
        for task in tasks:
            task_id, name, status, assigner, assignees, start_date, export_timestamp = task
            
            try:
                # Парсим дату создания (используем start_date_time как дату создания)
                if start_date:
                    create_date_parsed = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    create_date_only = create_date_parsed.date()
                else:
                    create_date_parsed = None
                    create_date_only = None
                
                processed_tasks.append({
                    'id': task_id,
                    'name': name,
                    'status': status,
                    'assigner': assigner,
                    'assignees': assignees,
                    'create_date_parsed': create_date_parsed,
                    'create_date_only': create_date_only,
                    'export_timestamp': export_timestamp
                })
            except Exception as e:
                print(f"    ⚠️ Ошибка обработки даты для задачи {task_id}: {e}")
                continue
        
        # Фильтруем задачи с валидными датами
        valid_tasks = [t for t in processed_tasks if t['create_date_parsed'] is not None]
        print(f"✅ Задач с валидными датами создания: {len(valid_tasks)}")
        
        if not valid_tasks:
            print("❌ Нет задач с валидными датами создания")
            return None
        
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
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .summary {{
            background: #d1ecf1;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #17a2b8;
            margin: 20px 0;
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
            <div class="summary">
                <h3>📊 Общая статистика</h3>
                <p><strong>Всего задач:</strong> {total_tasks}</p>
                <p><strong>Период:</strong> {date_range.days} дней</p>
                <p><strong>Среднее задач в день:</strong> {avg_tasks_per_day:.1f}</p>
                <p><strong>Период анализа:</strong> с {df['create_date_parsed'].min().strftime('%d.%m.%Y')} по {df['create_date_parsed'].max().strftime('%d.%m.%Y')}</p>
            </div>
            
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
                                <td>{task['status']}</td>
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
        html_path = os.path.join(self.output_dir, 'simple_date_analysis_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML отчет создан: {html_path}")
        
        # Создаем Excel отчет
        excel_path = os.path.join(self.output_dir, 'simple_date_analysis_report.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Основные данные
            df[['id', 'name', 'status', 'create_date_parsed', 'assigner', 'export_timestamp']].to_excel(
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
    
    def run_analysis(self):
        """Запуск анализа"""
        print("🚀 Запуск упрощенного анализа дат создания задач")
        print("=" * 80)
        
        # Получаем задачи из БД
        tasks = self.get_tasks_from_db()
        
        if not tasks:
            print("❌ Не удалось получить задачи из базы данных")
            return
        
        # Анализируем даты
        analysis_data = self.analyze_creation_dates(tasks)
        
        if not analysis_data:
            print("❌ Не удалось проанализировать даты")
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
    analyzer = SimpleDateAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
