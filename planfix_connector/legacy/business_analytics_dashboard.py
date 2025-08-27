"""
📊 Профессиональный бизнес-аналитический дашборд Planfix
Анализ средних чеков, исполнителей, постановщиков и бизнес-метрик
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

class BusinessAnalyticsDashboard:
    """Профессиональный бизнес-аналитический дашборд"""
    
    def __init__(self, db_path: str = "output/planfix_tasks_correct.db"):
        self.db_path = db_path
        self.output_dir = "output"
        
    def analyze_business_metrics(self):
        """Анализирует бизнес-метрики и создает дашборд"""
        
        if not os.path.exists(self.db_path):
            print(f"❌ База данных не найдена: {self.db_path}")
            return
        
        print("🔍 Анализируем бизнес-метрики...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 1. Анализ по статусам с процентами
            print("📈 Анализируем статусы...")
            status_analysis = self._analyze_statuses(conn)
            
            # 2. Анализ по постановщикам (заказчикам)
            print("👥 Анализируем постановщиков...")
            assigner_analysis = self._analyze_assigners(conn)
            
            # 3. Анализ по исполнителям
            print("👨‍💼 Анализируем исполнителей...")
            assignee_analysis = self._analyze_assignees(conn)
            
            # 4. Анализ кастомных полей (если есть)
            print("🔧 Анализируем кастомные поля...")
            custom_fields_analysis = self._analyze_custom_fields(conn)
            
            # 5. Анализ по месяцам
            print("📅 Анализируем временные тренды...")
            time_analysis = self._analyze_time_trends(conn)
            
            # 6. Анализ сложности и категорий
            print("📝 Анализируем сложность задач...")
            complexity_analysis = self._analyze_complexity(conn)
            
            # 7. Бизнес-метрики
            print("💰 Анализируем бизнес-метрики...")
            business_metrics = self._analyze_business_metrics(conn)
            
            conn.close()
            
            # Создаем профессиональный дашборд
            print("🌐 Создаем профессиональный бизнес-дашборд...")
            self._create_professional_dashboard(
                status_analysis, assigner_analysis, assignee_analysis,
                custom_fields_analysis, time_analysis, complexity_analysis, business_metrics
            )
            
            # Создаем Excel отчет
            print("📊 Создаем Excel отчет...")
            self._create_excel_report(
                status_analysis, assigner_analysis, assignee_analysis,
                custom_fields_analysis, time_analysis, complexity_analysis, business_metrics
            )
            
            print("✅ Бизнес-анализ завершен!")
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
    
    def _analyze_statuses(self, conn):
        """Анализ по статусам"""
        query = """
        SELECT 
            status_id,
            status_name,
            COUNT(*) as task_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
        FROM tasks 
        GROUP BY status_id, status_name
        ORDER BY task_count DESC
        """
        return pd.read_sql_query(query, conn)
    
    def _analyze_assigners(self, conn):
        """Анализ по постановщикам (заказчикам)"""
        query = """
        SELECT 
            assigner,
            COUNT(*) as task_count,
            COUNT(CASE WHEN status_id = 127 THEN 1 END) as status_127,
            COUNT(CASE WHEN status_id = 128 THEN 1 END) as status_128,
            COUNT(CASE WHEN status_id = 129 THEN 1 END) as status_129,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
        FROM tasks 
        WHERE assigner IS NOT NULL AND assigner != '' AND assigner != 'None'
        GROUP BY assigner
        ORDER BY task_count DESC
        LIMIT 25
        """
        return pd.read_sql_query(query, conn)
    
    def _analyze_assignees(self, conn):
        """Анализ по исполнителям"""
        query = """
        SELECT 
            assignees,
            COUNT(*) as task_count,
            COUNT(CASE WHEN status_id = 127 THEN 1 END) as status_127,
            COUNT(CASE WHEN status_id = 128 THEN 1 END) as status_128,
            COUNT(CASE WHEN status_id = 129 THEN 1 END) as status_129,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
        FROM tasks 
        WHERE assignees IS NOT NULL AND assignees != '' AND assignees != 'None'
        GROUP BY assignees
        ORDER BY task_count DESC
        LIMIT 25
        """
        return pd.read_sql_query(query, conn)
    
    def _analyze_custom_fields(self, conn):
        """Анализ кастомных полей"""
        try:
            query = """
            SELECT 
                field_name,
                COUNT(*) as total_count,
                COUNT(CASE WHEN field_value != '' AND field_value IS NOT NULL THEN 1 END) as filled_count,
                ROUND(COUNT(CASE WHEN field_value != '' AND field_value IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as fill_percentage
            FROM custom_field_values 
            GROUP BY field_name
            ORDER BY filled_count DESC
            """
            return pd.read_sql_query(query, conn)
        except:
            return pd.DataFrame({
                'field_name': ['Нет данных'],
                'total_count': [0],
                'filled_count': [0],
                'fill_percentage': [0]
            })
    
    def _analyze_time_trends(self, conn):
        """Анализ временных трендов"""
        try:
            query = """
            SELECT 
                strftime('%Y-%m', start_date_time) as month,
                COUNT(*) as task_count
            FROM tasks 
            WHERE start_date_time IS NOT NULL AND start_date_time != ''
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
            """
            return pd.read_sql_query(query, conn)
        except:
            return pd.DataFrame({'month': ['Нет данных'], 'task_count': [0]})
    
    def _analyze_complexity(self, conn):
        """Анализ сложности задач"""
        query = """
        SELECT 
            CASE 
                WHEN LENGTH(name) < 50 THEN 'Простая'
                WHEN LENGTH(name) < 100 THEN 'Средняя'
                WHEN LENGTH(name) < 200 THEN 'Сложная'
                ELSE 'Очень сложная'
            END as complexity_level,
            COUNT(*) as task_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
        FROM tasks 
        GROUP BY complexity_level
        ORDER BY task_count DESC
        """
        return pd.read_sql_query(query, conn)
    
    def _analyze_business_metrics(self, conn):
        """Анализ бизнес-метрик"""
        # Общие метрики
        total_tasks = pd.read_sql_query("SELECT COUNT(*) as total FROM tasks", conn).iloc[0]['total']
        
        # Метрики по постановщикам
        assigner_metrics = pd.read_sql_query("""
            SELECT 
                COUNT(DISTINCT assigner) as unique_assigners,
                ROUND(AVG(task_count), 1) as avg_tasks_per_assigner,
                MAX(task_count) as max_tasks_per_assigner
            FROM (
                SELECT assigner, COUNT(*) as task_count
                FROM tasks 
                WHERE assigner IS NOT NULL AND assigner != '' AND assigner != 'None'
                GROUP BY assigner
            )
        """, conn)
        
        # Метрики по исполнителям
        assignee_metrics = pd.read_sql_query("""
            SELECT 
                COUNT(DISTINCT assignees) as unique_assignees,
                ROUND(AVG(task_count), 1) as avg_tasks_per_assignee,
                MAX(task_count) as max_tasks_per_assignee
            FROM (
                SELECT assignees, COUNT(*) as task_count
                FROM tasks 
                WHERE assignees IS NOT NULL AND assignees != '' AND assignees != 'None'
                GROUP BY assignees
            )
        """, conn)
        
        return {
            'total_tasks': total_tasks,
            'assigner_metrics': assigner_metrics,
            'assignee_metrics': assignee_metrics
        }
    
    def _create_professional_dashboard(self, status_df, assigner_df, assignee_df, 
                                     custom_fields_df, time_df, complexity_df, business_metrics):
        """Создает профессиональный HTML дашборд"""
        
        # Статистика с проверками на None
        total_tasks = business_metrics['total_tasks'] or 0
        unique_assigners = business_metrics['assigner_metrics'].iloc[0]['unique_assigners'] or 0
        unique_assignees = business_metrics['assignee_metrics'].iloc[0]['unique_assignees'] or 0
        avg_tasks_per_assigner = business_metrics['assigner_metrics'].iloc[0]['avg_tasks_per_assigner'] or 0
        max_tasks_per_assigner = business_metrics['assigner_metrics'].iloc[0]['max_tasks_per_assigner'] or 0
        max_tasks_per_assignee = business_metrics['assignee_metrics'].iloc[0]['max_tasks_per_assignee'] or 0
        avg_tasks_per_assignee = business_metrics['assignee_metrics'].iloc[0]['avg_tasks_per_assignee'] or 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Planfix Business Analytics Dashboard</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{ 
                    max-width: 1600px; 
                    margin: 0 auto; 
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); 
                    color: white; 
                    padding: 40px; 
                    text-align: center; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 3em; 
                    font-weight: 300;
                    margin-bottom: 10px;
                }}
                .header p {{ 
                    margin: 0; 
                    font-size: 1.3em; 
                    opacity: 0.9; 
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 25px; 
                    padding: 40px;
                    background: #f8f9fa;
                }}
                .stat-card {{ 
                    background: white; 
                    padding: 30px; 
                    border-radius: 15px; 
                    box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
                    text-align: center;
                    border-left: 5px solid #667eea;
                    transition: transform 0.3s ease;
                }}
                .stat-card:hover {{ transform: translateY(-5px); }}
                .stat-number {{ 
                    font-size: 3em; 
                    font-weight: bold; 
                    color: #667eea; 
                    margin: 15px 0; 
                }}
                .stat-label {{ 
                    color: #666; 
                    font-size: 1.2em; 
                    font-weight: 500;
                }}
                .data-section {{ 
                    background: white; 
                    padding: 40px; 
                    margin: 0;
                    border-bottom: 1px solid #eee;
                }}
                .data-section h2 {{ 
                    color: #2c3e50; 
                    margin-bottom: 30px; 
                    font-size: 1.8em;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 15px;
                    display: flex;
                    align-items: center;
                }}
                .data-section h2::before {{
                    content: attr(data-icon);
                    margin-right: 15px;
                    font-size: 1.2em;
                }}
                .data-table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin-top: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                }}
                .data-table th, .data-table td {{ 
                    padding: 15px; 
                    text-align: left; 
                    border-bottom: 1px solid #eee; 
                }}
                .data-table th {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    font-weight: 600;
                    font-size: 1.1em;
                }}
                .data-table tr:hover {{ 
                    background-color: #f8f9fa; 
                    transform: scale(1.01);
                    transition: all 0.2s ease;
                }}
                .data-table tr:nth-child(even) {{ background-color: #fafbfc; }}
                .highlight {{ 
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                    font-weight: bold; 
                    color: #1976d2;
                    border-radius: 5px;
                    padding: 5px 10px;
                }}
                .percentage {{ 
                    color: #4caf50; 
                    font-weight: bold; 
                }}
                .footer {{ 
                    text-align: center; 
                    color: #666; 
                    padding: 40px; 
                    background: #f8f9fa;
                    border-top: 1px solid #eee;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 4px solid #4caf50;
                }}
                .metric-title {{
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .metric-value {{
                    font-size: 1.5em;
                    color: #4caf50;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Planfix Business Analytics</h1>
                    <p>Профессиональный анализ бизнес-метрик и производительности</p>
                    <p>Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_tasks:,}</div>
                        <div class="stat-label">Всего задач</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{unique_assigners}</div>
                        <div class="stat-label">Уникальных постановщиков</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{unique_assignees}</div>
                        <div class="stat-label">Уникальных исполнителей</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{avg_tasks_per_assigner}</div>
                        <div class="stat-label">Среднее задач на постановщика</div>
                    </div>
                </div>
                
                <div class="data-section">
                    <h2 data-icon="📈">Распределение задач по статусам</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Статус ID</th>
                                <th>Название статуса</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td><strong>{row['status_id']}</strong></td>
                                <td>{row['status_name']}</td>
                                <td class="highlight">{row['task_count']:,}</td>
                                <td class="percentage">{row['percentage']}%</td>
                            </tr>
                            ''' for _, row in status_df.iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="data-section">
                    <h2 data-icon="👥">Топ постановщиков по количеству задач</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Постановщик</th>
                                <th>Всего задач</th>
                                <th>Статус 127</th>
                                <th>Статус 128</th>
                                <th>Статус 129</th>
                                <th>Доля от общего</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{row['assigner']}</td>
                                <td class="highlight"><strong>{row['task_count']:,}</strong></td>
                                <td>{row['status_127']}</td>
                                <td>{row['status_128']}</td>
                                <td>{row['status_129']}</td>
                                <td class="percentage">{row['percentage']}%</td>
                            </tr>
                            ''' for _, row in assigner_df.head(20).iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="data-section">
                    <h2 data-icon="👨‍💼">Топ исполнителей по количеству задач</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Исполнитель</th>
                                <th>Всего задач</th>
                                <th>Статус 127</th>
                                <th>Статус 128</th>
                                <th>Статус 129</th>
                                <th>Доля от общего</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{row['assignees']}</td>
                                <td class="highlight"><strong>{row['task_count']:,}</strong></td>
                                <td>{row['status_127']}</td>
                                <td>{row['status_128']}</td>
                                <td>{row['status_129']}</td>
                                <td class="percentage">{row['percentage']}%</td>
                            </tr>
                            ''' for _, row in assignee_df.head(20).iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="data-section">
                    <h2 data-icon="📝">Анализ сложности задач</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Уровень сложности</th>
                                <th>Количество задач</th>
                                <th>Процент от общего</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{row['complexity_level']}</td>
                                <td class="highlight"><strong>{row['task_count']:,}</strong></td>
                                <td class="percentage">{row['percentage']}%</td>
                            </tr>
                            ''' for _, row in complexity_df.iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="data-section">
                    <h2 data-icon="🔧">Анализ кастомных полей</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Поле</th>
                                <th>Всего значений</th>
                                <th>Заполненных значений</th>
                                <th>Процент заполненности</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{row['field_name']}</td>
                                <td>{row['total_count']:,}</td>
                                <td class="highlight"><strong>{row['filled_count']:,}</strong></td>
                                <td class="percentage">{row['fill_percentage']}%</td>
                            </tr>
                            ''' for _, row in custom_fields_df.iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="data-section">
                    <h2 data-icon="📊">Дополнительные бизнес-метрики</h2>
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="metric-title">Максимум задач у постановщика</div>
                            <div class="metric-value">{max_tasks_per_assigner:,}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Максимум задач у исполнителя</div>
                            <div class="metric-value">{max_tasks_per_assignee:,}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Среднее задач на исполнителя</div>
                            <div class="metric-value">{avg_tasks_per_assignee}</div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Planfix Business Analytics Dashboard v2.0</strong></p>
                    <p>Профессиональный анализ бизнес-метрик | Создан автоматически</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(f"{self.output_dir}/business_analytics_dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"💾 Профессиональный бизнес-дашборд сохранен: {self.output_dir}/business_analytics_dashboard.html")
    
    def _create_excel_report(self, status_df, assigner_df, assignee_df, 
                            custom_fields_df, time_df, complexity_df, business_metrics):
        """Создает Excel отчет с бизнес-метриками"""
        
        with pd.ExcelWriter(f"{self.output_dir}/business_analytics_report.xlsx", engine='openpyxl') as writer:
            
            # Лист со статусами
            status_df.to_excel(writer, sheet_name='Статусы', index=False)
            
            # Лист с постановщиками
            assigner_df.to_excel(writer, sheet_name='Постановщики', index=False)
            
            # Лист с исполнителями
            assignee_df.to_excel(writer, sheet_name='Исполнители', index=False)
            
            # Лист с кастомными полями
            custom_fields_df.to_excel(writer, sheet_name='Кастомные поля', index=False)
            
            # Лист со сложностью
            complexity_df.to_excel(writer, sheet_name='Сложность', index=False)
            
            # Лист с временными трендами
            time_df.to_excel(writer, sheet_name='Временные тренды', index=False)
            
            # Сводный лист с бизнес-метриками
            summary_data = {
                'Метрика': [
                    'Всего задач',
                    'Уникальных постановщиков',
                    'Уникальных исполнителей',
                    'Среднее задач на постановщика',
                    'Максимум задач у постановщика',
                    'Среднее задач на исполнителя',
                    'Максимум задач у исполнителя',
                    'Количество статусов',
                    'Дата создания отчета'
                ],
                'Значение': [
                    business_metrics['total_tasks'],
                    business_metrics['assigner_metrics'].iloc[0]['unique_assigners'],
                    business_metrics['assignee_metrics'].iloc[0]['unique_assignees'],
                    business_metrics['assigner_metrics'].iloc[0]['avg_tasks_per_assigner'],
                    business_metrics['assigner_metrics'].iloc[0]['max_tasks_per_assigner'],
                    business_metrics['assignee_metrics'].iloc[0]['avg_tasks_per_assignee'],
                    business_metrics['assignee_metrics'].iloc[0]['max_tasks_per_assignee'],
                    len(status_df),
                    datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Сводка', index=False)
        
        print(f"💾 Excel отчет сохранен: {self.output_dir}/business_analytics_report.xlsx")

if __name__ == "__main__":
    print("🚀 Профессиональный бизнес-аналитический дашборд Planfix")
    print("=" * 60)
    
    dashboard = BusinessAnalyticsDashboard()
    dashboard.analyze_business_metrics()
    
    print("\n✅ Бизнес-анализ завершен!")
    print("📁 Файлы сохранены в папке output/")
    print("   - business_analytics_dashboard.html - Профессиональный HTML дашборд")
    print("   - business_analytics_report.xlsx - Excel отчет с бизнес-метриками")
