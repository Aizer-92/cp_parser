#!/usr/bin/env python3
"""
Профессиональный парсер дат для Planfix Connector
Полный анализ всех задач с приоритетами и максимально разными срезами
"""

import sqlite3
import json
import requests
from datetime import datetime, timedelta
import os
import pandas as pd
from collections import defaultdict

class ProfessionalDatesParser:
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
    
    def get_all_tasks_with_dates(self):
        """Получение всех задач с датами из API"""
        print("🔍 Получение всех задач с датами из API...")
        
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
                    
                    # Извлекаем даты и приоритеты
                    for task in tasks:
                        task_data = self.extract_task_data(task)
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
        
        print(f"📅 Всего задач с данными: {len(all_tasks)}")
        return all_tasks
    
    def extract_task_data(self, task):
        """Извлечение данных из задачи"""
        # Пробуем получить дату из разных полей
        date_value = None
        date_source = None
        
        if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
            date_value = task['endDateTime'].get('datetime')
            date_source = 'endDateTime'
        elif task.get('startDateTime') and isinstance(task['startDateTime'], dict):
            date_value = task['startDateTime'].get('datetime')
            date_source = 'startDateTime'
        elif task.get('createDate'):
            date_value = task['createDate']
            date_source = 'createDate'
        elif task.get('modifyDate'):
            date_value = task['modifyDate']
            date_source = 'modifyDate'
        
        if date_value:
            return {
                'id': task.get('id'),
                'name': task.get('name', ''),
                'description': task.get('description', ''),
                'dateTime': date_value,
                'date_source': date_source,
                'status_id': task.get('status', {}).get('id', 0),
                'status_name': task.get('status', {}).get('name', ''),
                'priority': task.get('priority', 'NotUrgent'),
                'importance': task.get('importance'),
                'assigner': task.get('assigner', {}).get('name', '') if isinstance(task.get('assigner'), dict) else str(task.get('assigner', '')),
                'assignees': self.extract_assignees(task.get('assignees')),
                'work_time': task.get('workTime'),
                'plan_time': task.get('planTime'),
                'fact_time': task.get('factTime')
            }
        return None
    
    def extract_assignees(self, assignees):
        """Извлечение исполнителей"""
        if not assignees:
            return ''
        
        if isinstance(assignees, list):
            names = []
            for assignee in assignees:
                if isinstance(assignee, dict):
                    names.append(assignee.get('name', ''))
                else:
                    names.append(str(assignee))
            return ', '.join(filter(None, names))
        elif isinstance(assignees, dict):
            return assignees.get('name', '')
        else:
            return str(assignees)
    
    def update_database_dates(self, tasks_with_dates):
        """Обновление дат в базе данных"""
        print("💾 Обновление дат в базе данных...")
        
        if not os.path.exists(self.db_path):
            print(f"❌ База данных не найдена: {self.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем, есть ли поле start_date_time
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'start_date_time' not in columns:
                print("❌ Поле start_date_time не найдено в таблице tasks")
                return False
            
            # Обновляем даты
            updated_count = 0
            for task in tasks_with_dates:
                try:
                    if task['dateTime']:
                        # Парсим дату из ISO формата
                        date_str = task['dateTime'].split('+')[0].split('T')[0]
                        
                        cursor.execute("""
                            UPDATE tasks 
                            SET start_date_time = ? 
                            WHERE id = ?
                        """, (date_str, task['id']))
                        
                        if cursor.rowcount > 0:
                            updated_count += 1
                            
                except Exception as e:
                    print(f"    ❌ Ошибка обновления задачи {task['id']}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Обновлено дат: {updated_count}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления базы данных: {e}")
            return False
    
    def calculate_priorities(self, tasks_with_dates):
        """Вычисление приоритетов для задач"""
        print("🎯 Вычисление приоритетов...")
        
        for task in tasks_with_dates:
            # Анализируем название задачи
            name = task['name'].lower()
            
            # Определяем приоритет на основе названия
            priority = 'D'  # По умолчанию
            
            if any(word in name for word in ['срочно', 'urgent', 'критично', 'critical']):
                priority = 'A'
            elif any(word in name for word in ['важно', 'important', 'приоритет', 'priority']):
                priority = 'B'
            elif any(word in name for word in ['обычно', 'normal', 'стандарт', 'standard']):
                priority = 'C'
            
            # Анализируем описание
            description = task['description'].lower() if task['description'] else ''
            if any(word in description for word in ['срочно', 'urgent', 'критично', 'critical', 'немедленно']):
                priority = 'A'
            elif any(word in description for word in ['важно', 'important', 'приоритет', 'priority']):
                if priority == 'D':
                    priority = 'B'
            
            # Анализируем статус
            status_id = task['status_id']
            if status_id == 127:  # Поиск и расчет товара
                if priority == 'D':
                    priority = 'C'
            elif status_id == 128:  # КП Согласование
                if priority == 'D':
                    priority = 'B'
            elif status_id == 129:  # КП Согласовано
                if priority == 'D':
                    priority = 'A'
            
            task['calculated_priority'] = priority
        
        print(f"✅ Приоритеты вычислены для {len(tasks_with_dates)} задач")
        return tasks_with_dates
    
    def create_comprehensive_report(self, tasks_with_dates):
        """Создание комплексного отчета"""
        print("📊 Создание комплексного отчета...")
        
        # Создаем DataFrame для анализа
        df = pd.DataFrame(tasks_with_dates)
        
        # Анализ по статусам
        status_analysis = df.groupby('status_name').agg({
            'id': 'count',
            'calculated_priority': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # Анализ по приоритетам
        priority_analysis = df['calculated_priority'].value_counts()
        
        # Анализ по датам
        df['date'] = pd.to_datetime(df['dateTime'].str.split('T').str[0])
        df['month'] = df['date'].dt.to_period('M')
        monthly_analysis = df.groupby('month').size()
        
        # Анализ по исполнителям
        assignee_analysis = df['assignees'].value_counts().head(10)
        
        # Анализ по постановщикам
        assigner_analysis = df['assigner'].value_counts().head(10)
        
        # Создаем HTML отчет
        html_content = self.generate_html_report(
            df, status_analysis, priority_analysis, 
            monthly_analysis, assignee_analysis, assigner_analysis
        )
        
        # Сохраняем отчет
        output_path = os.path.join(self.output_dir, 'comprehensive_analysis_report.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Комплексный отчет создан: {output_path}")
        
        # Создаем Excel отчет
        excel_path = os.path.join(self.output_dir, 'comprehensive_analysis_report.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Все задачи', index=False)
            status_analysis.to_excel(writer, sheet_name='Анализ по статусам', index=False)
            priority_analysis.to_frame('Количество').to_excel(writer, sheet_name='Анализ по приоритетам')
            monthly_analysis.to_frame('Количество задач').to_excel(writer, sheet_name='Анализ по месяцам')
            assignee_analysis.to_frame('Количество задач').to_excel(writer, sheet_name='Топ исполнителей')
            assigner_analysis.to_frame('Количество задач').to_excel(writer, sheet_name='Топ постановщиков')
        
        print(f"✅ Excel отчет создан: {excel_path}")
        
        return output_path, excel_path
    
    def generate_html_report(self, df, status_analysis, priority_analysis, 
                           monthly_analysis, assignee_analysis, assigner_analysis):
        """Генерация HTML отчета"""
        
        # Статистика
        total_tasks = len(df)
        tasks_with_dates = df['dateTime'].notna().sum()
        coverage_percentage = round(tasks_with_dates / total_tasks * 100, 1) if total_tasks > 0 else 0
        
        # Анализ приоритетов
        priority_stats = priority_analysis.to_dict()
        
        # Анализ статусов
        status_stats = []
        for _, row in status_analysis.iterrows():
            status_stats.append({
                'name': row['status_name'],
                'count': row['id'],
                'priorities': row['calculated_priority']
            })
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Комплексный анализ Planfix Connector</title>
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
        .priority-a {{ color: #dc3545; font-weight: bold; }}
        .priority-b {{ color: #fd7e14; font-weight: bold; }}
        .priority-c {{ color: #ffc107; font-weight: bold; }}
        .priority-d {{ color: #6c757d; font-weight: bold; }}
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
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        .chart {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Комплексный анализ</h1>
            <p>Planfix Connector - Полный анализ задач с приоритетами</p>
        </div>
        
        <div class="content">
            <!-- Основная статистика -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_tasks}</div>
                    <div class="stat-label">Всего задач</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{tasks_with_dates}</div>
                    <div class="stat-label">Задач с датами</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{coverage_percentage}%</div>
                    <div class="stat-label">Покрытие датами</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(df['assignees'].unique())}</div>
                    <div class="stat-label">Уникальных исполнителей</div>
                </div>
            </div>
            
            <!-- Анализ по приоритетам -->
            <div class="section">
                <h2>📊 Анализ по приоритетам</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number priority-a">{priority_stats.get('A', 0)}</div>
                        <div class="stat-label">Приоритет A (Критично)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number priority-b">{priority_stats.get('B', 0)}</div>
                        <div class="stat-label">Приоритет B (Важно)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number priority-c">{priority_stats.get('C', 0)}</div>
                        <div class="stat-label">Приоритет C (Обычно)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number priority-d">{priority_stats.get('D', 0)}</div>
                        <div class="stat-label">Приоритет D (Низкий)</div>
                    </div>
                </div>
            </div>
            
            <!-- Анализ по статусам -->
            <div class="section">
                <h2>🎯 Анализ по статусам</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Статус</th>
                                <th>Количество задач</th>
                                <th>Приоритет A</th>
                                <th>Приоритет B</th>
                                <th>Приоритет C</th>
                                <th>Приоритет D</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for status in status_stats:
            priorities = status['priorities']
            html_content += f"""
                            <tr>
                                <td><strong>{status['name']}</strong></td>
                                <td>{status['count']}</td>
                                <td class="priority-a">{priorities.get('A', 0)}</td>
                                <td class="priority-b">{priorities.get('B', 0)}</td>
                                <td class="priority-c">{priorities.get('C', 0)}</td>
                                <td class="priority-d">{priorities.get('D', 0)}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Топ исполнителей -->
            <div class="section">
                <h2>👥 Топ исполнителей</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Исполнитель</th>
                                <th>Количество задач</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for assignee, count in assignee_analysis.items():
            html_content += f"""
                            <tr>
                                <td>{assignee}</td>
                                <td>{count}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Топ постановщиков -->
            <div class="section">
                <h2>📝 Топ постановщиков</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Постановщик</th>
                                <th>Количество задач</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for assigner, count in assigner_analysis.items():
            html_content += f"""
                            <tr>
                                <td>{assigner}</td>
                                <td>{count}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Анализ по месяцам -->
            <div class="section">
                <h2>📅 Анализ по месяцам</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Месяц</th>
                                <th>Количество задач</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for month, count in monthly_analysis.items():
            html_content += f"""
                            <tr>
                                <td>{month}</td>
                                <td>{count}</td>
                            </tr>
            """
        
        html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Рекомендации -->
            <div class="section">
                <h2>💡 Рекомендации по управлению</h2>
                <div style="background: #e8f5e8; padding: 20px; border-radius: 15px;">
                    <h3 style="color: #28a745; margin-top: 0;">🎯 Стратегические рекомендации</h3>
                    <ul>
                        <li><strong>Приоритет A ({priority_stats.get('A', 0)} задач):</strong> Требуют немедленного внимания, возможны срочные дедлайны</li>
                        <li><strong>Приоритет B ({priority_stats.get('B', 0)} задач):</strong> Важные задачи, планируйте ресурсы заранее</li>
                        <li><strong>Приоритет C ({priority_stats.get('C', 0)} задач):</strong> Стандартные задачи, можно выполнять в обычном режиме</li>
                        <li><strong>Приоритет D ({priority_stats.get('D', 0)} задач):</strong> Низкоприоритетные, можно отложить при необходимости</li>
                    </ul>
                    
                    <h3 style="color: #17a2b8; margin-top: 20px;">📊 Операционные рекомендации</h3>
                    <ul>
                        <li><strong>Распределение нагрузки:</strong> Анализируйте топ исполнителей для равномерного распределения задач</li>
                        <li><strong>Мониторинг статусов:</strong> Отслеживайте переходы между статусами для выявления узких мест</li>
                        <li><strong>Временной анализ:</strong> Используйте месячную статистику для планирования ресурсов</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🎯 Planfix Connector - Комплексный анализ | Создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def run_full_analysis(self):
        """Запуск полного анализа"""
        print("🚀 Запуск профессионального анализа Planfix Connector")
        print("=" * 80)
        
        # Получаем все задачи с датами
        tasks_with_dates = self.get_all_tasks_with_dates()
        if not tasks_with_dates:
            print("❌ Не удалось получить задачи с датами")
            return
        
        # Вычисляем приоритеты
        tasks_with_priorities = self.calculate_priorities(tasks_with_dates)
        
        # Обновляем базу данных
        if self.update_database_dates(tasks_with_priorities):
            print("✅ Даты успешно обновлены в базе данных")
            
            # Создаем комплексный отчет
            html_path, excel_path = self.create_comprehensive_report(tasks_with_priorities)
            
            print("\n🎉 Полный анализ завершен успешно!")
            print(f"📊 Обработано задач: {len(tasks_with_priorities)}")
            print(f"📄 HTML отчет: {html_path}")
            print(f"📊 Excel отчет: {excel_path}")
            
            # Открываем отчеты
            os.startfile(html_path)
            os.startfile(excel_path)
        else:
            print("❌ Не удалось обновить даты в базе данных")

def main():
    """Основная функция"""
    parser = ProfessionalDatesParser()
    parser.run_full_analysis()

if __name__ == "__main__":
    main()

