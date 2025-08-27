"""
🍎 Apple-style Business Analytics Dashboard
Профессиональный дашборд с анализом сумм просчетов и приоритетности задач
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

class AppleStyleDashboard:
    """Профессиональный дашборд в стиле Apple"""
    
    def __init__(self, db_path: str = "output/planfix_tasks_correct.db"):
        self.db_path = db_path
        self.output_dir = "output"
        
    def analyze_apple_metrics(self):
        """Анализирует метрики и создает Apple-style дашборд"""
        
        if not os.path.exists(self.db_path):
            print(f"❌ База данных не найдена: {self.db_path}")
            return
        
        print("🍎 Анализируем метрики для Apple-style дашборда...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 1. Анализ по статусам
            print("📈 Анализируем статусы...")
            status_analysis = self._analyze_statuses(conn)
            
            # 2. Анализ по постановщикам
            print("👥 Анализируем постановщиков...")
            assigner_analysis = self._analyze_assigners(conn)
            
            # 3. Анализ по исполнителям
            print("👨‍💼 Анализируем исполнителей...")
            assignee_analysis = self._analyze_assignees(conn)
            
            # 4. Анализ кастомных полей (суммы, приоритеты)
            print("💰 Анализируем суммы и приоритеты...")
            custom_fields_analysis = self._analyze_custom_fields(conn)
            
            # 5. Анализ приоритетности задач
            print("🎯 Анализируем приоритетность...")
            priority_analysis = self._analyze_priority(conn)
            
            # 6. Анализ сложности
            print("📝 Анализируем сложность...")
            complexity_analysis = self._analyze_complexity(conn)
            
            # 7. Бизнес-метрики
            print("📊 Анализируем бизнес-метрики...")
            business_metrics = self._analyze_business_metrics(conn)
            
            conn.close()
            
            # Создаем Apple-style дашборд
            print("🍎 Создаем Apple-style дашборд...")
            self._create_apple_style_dashboard(
                status_analysis, assigner_analysis, assignee_analysis,
                custom_fields_analysis, priority_analysis, complexity_analysis, business_metrics
            )
            
            # Создаем Excel отчет
            print("📊 Создаем Excel отчет...")
            self._create_excel_report(
                status_analysis, assigner_analysis, assignee_analysis,
                custom_fields_analysis, priority_analysis, complexity_analysis, business_metrics
            )
            
            print("✅ Apple-style анализ завершен!")
            
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
        """Анализ по постановщикам"""
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
        """Анализ кастомных полей (суммы, приоритеты)"""
        try:
            query = """
            SELECT 
                field_name,
                COUNT(*) as total_count,
                COUNT(CASE WHEN field_value != '' AND field_value IS NOT NULL THEN 1 END) as filled_count,
                ROUND(COUNT(CASE WHEN field_value != '' AND field_value IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as fill_percentage,
                CASE 
                    WHEN field_name LIKE '%сумма%' OR field_name LIKE '%Сумма%' THEN 'Сумма'
                    WHEN field_name LIKE '%приоритет%' OR field_name LIKE '%Приоритет%' THEN 'Приоритет'
                    WHEN field_name LIKE '%грейд%' OR field_name LIKE '%Грейд%' THEN 'Грейд'
                    ELSE 'Другое'
                END as field_category
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
                'fill_percentage': [0],
                'field_category': ['Нет данных']
            })
    
    def _analyze_priority(self, conn):
        """Анализ приоритетности задач"""
        try:
            # Пытаемся найти поле с приоритетами
            query = """
            SELECT 
                field_value as priority_level,
                COUNT(*) as task_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM custom_field_values WHERE field_name LIKE '%приоритет%'), 1) as percentage
            FROM custom_field_values 
            WHERE field_name LIKE '%приоритет%' AND field_value != '' AND field_value IS NOT NULL
            GROUP BY field_value
            ORDER BY task_count DESC
            """
            result = pd.read_sql_query(query, conn)
            if not result.empty:
                return result
            else:
                # Если нет данных о приоритетах, создаем анализ по сложности названий
                return self._analyze_complexity_as_priority(conn)
        except:
            return self._analyze_complexity_as_priority(conn)
    
    def _analyze_complexity_as_priority(self, conn):
        """Анализ сложности как приоритетности"""
        query = """
        SELECT 
            CASE 
                WHEN LENGTH(name) < 50 THEN 'Низкий приоритет'
                WHEN LENGTH(name) < 100 THEN 'Средний приоритет'
                WHEN LENGTH(name) < 200 THEN 'Высокий приоритет'
                ELSE 'Критический приоритет'
            END as priority_level,
            COUNT(*) as task_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 1) as percentage
        FROM tasks 
        GROUP BY priority_level
        ORDER BY task_count DESC
        """
        return pd.read_sql_query(query, conn)
    
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
        total_tasks = pd.read_sql_query("SELECT COUNT(*) as total FROM tasks", conn).iloc[0]['total']
        
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
    
    def _create_apple_style_dashboard(self, status_df, assigner_df, assignee_df, 
                                     custom_fields_df, priority_df, complexity_df, business_metrics):
        """Создает Apple-style HTML дашборд"""
        
        # Статистика с проверками
        total_tasks = business_metrics['total_tasks'] or 0
        unique_assigners = business_metrics['assigner_metrics'].iloc[0]['unique_assigners'] or 0
        unique_assignees = business_metrics['assignee_metrics'].iloc[0]['unique_assignees'] or 0
        avg_tasks_per_assigner = business_metrics['assigner_metrics'].iloc[0]['avg_tasks_per_assigner'] or 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Planfix Apple-Style Analytics</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                * {{ 
                    margin: 0; 
                    padding: 0; 
                    box-sizing: border-box; 
                }}
                body {{ 
                    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                    background: #f5f5f7;
                    color: #1d1d1f;
                    line-height: 1.47059;
                    font-weight: 400;
                    letter-spacing: -.022em;
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px;
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 40px;
                    padding: 40px 0;
                }}
                .header h1 {{ 
                    font-size: 48px;
                    font-weight: 600;
                    letter-spacing: -.003em;
                    margin-bottom: 10px;
                    background: linear-gradient(135deg, #007AFF, #5856D6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                .header p {{ 
                    font-size: 21px;
                    font-weight: 400;
                    color: #86868b;
                    margin-bottom: 20px;
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 20px; 
                    margin-bottom: 40px;
                }}
                .stat-card {{ 
                    background: rgba(255, 255, 255, 0.8);
                    backdrop-filter: blur(20px);
                    border-radius: 20px;
                    padding: 30px;
                    text-align: center;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }}
                .stat-card:hover {{ 
                    transform: translateY(-8px);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                }}
                .stat-number {{ 
                    font-size: 48px;
                    font-weight: 700;
                    color: #007AFF;
                    margin-bottom: 10px;
                    letter-spacing: -.003em;
                }}
                .stat-label {{ 
                    font-size: 17px;
                    color: #86868b;
                    font-weight: 500;
                }}
                .section {{ 
                    background: rgba(255, 255, 255, 0.8);
                    backdrop-filter: blur(20px);
                    border-radius: 20px;
                    padding: 30px;
                    margin-bottom: 30px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }}
                .section h2 {{ 
                    font-size: 28px;
                    font-weight: 600;
                    margin-bottom: 25px;
                    color: #1d1d1f;
                    display: flex;
                    align-items: center;
                    letter-spacing: -.003em;
                }}
                .section h2::before {{
                    content: attr(data-icon);
                    margin-right: 15px;
                    font-size: 24px;
                }}
                .data-table {{ 
                    width: 100%; 
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                .data-table th, .data-table td {{ 
                    padding: 16px; 
                    text-align: left; 
                    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                    font-size: 15px;
                }}
                .data-table th {{ 
                    background: rgba(0, 122, 255, 0.1);
                    color: #007AFF;
                    font-weight: 600;
                    font-size: 15px;
                    letter-spacing: -.003em;
                }}
                .data-table tr:hover {{ 
                    background: rgba(0, 122, 255, 0.05);
                    transition: background 0.2s ease;
                }}
                .data-table tr:nth-child(even) {{ 
                    background: rgba(0, 0, 0, 0.02);
                }}
                .highlight {{ 
                    background: rgba(0, 122, 255, 0.1);
                    color: #007AFF;
                    font-weight: 600;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 14px;
                }}
                .percentage {{ 
                    color: #34C759;
                    font-weight: 600;
                    font-size: 14px;
                }}
                .priority-high {{
                    color: #FF3B30;
                    font-weight: 600;
                }}
                .priority-medium {{
                    color: #FF9500;
                    font-weight: 600;
                }}
                .priority-low {{
                    color: #34C759;
                    font-weight: 600;
                }}
                .footer {{ 
                    text-align: center; 
                    color: #86868b; 
                    padding: 40px 0;
                    font-size: 15px;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .metric-card {{
                    background: rgba(0, 122, 255, 0.05);
                    padding: 20px;
                    border-radius: 16px;
                    border-left: 4px solid #007AFF;
                }}
                .metric-title {{
                    font-weight: 500;
                    color: #1d1d1f;
                    margin-bottom: 10px;
                    font-size: 15px;
                }}
                .metric-value {{
                    font-size: 24px;
                    color: #007AFF;
                    font-weight: 700;
                }}
                @media (max-width: 768px) {{
                    .container {{ padding: 10px; }}
                    .header h1 {{ font-size: 36px; }}
                    .stat-card {{ padding: 20px; }}
                    .section {{ padding: 20px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Planfix Analytics</h1>
                    <p>Профессиональный анализ в стиле Apple</p>
                    <p>Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_tasks:,}</div>
                        <div class="stat-label">Всего задач</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{unique_assigners}</div>
                        <div class="stat-label">Постановщиков</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{unique_assignees}</div>
                        <div class="stat-label">Исполнителей</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{avg_tasks_per_assigner}</div>
                        <div class="stat-label">Среднее на постановщика</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2 data-icon="📈">Распределение по статусам</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Статус</th>
                                <th>Название</th>
                                <th>Количество</th>
                                <th>Процент</th>
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
                
                <div class="section">
                    <h2 data-icon="👥">Топ постановщиков</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Постановщик</th>
                                <th>Всего задач</th>
                                <th>Статус 127</th>
                                <th>Статус 128</th>
                                <th>Статус 129</th>
                                <th>Доля</th>
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
                            ''' for _, row in assigner_df.head(15).iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2 data-icon="👨‍💼">Топ исполнителей</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Исполнитель</th>
                                <th>Всего задач</th>
                                <th>Статус 127</th>
                                <th>Статус 128</th>
                                <th>Статус 129</th>
                                <th>Доля</th>
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
                            ''' for _, row in assignee_df.head(15).iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2 data-icon="🎯">Анализ приоритетности</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Уровень приоритета</th>
                                <th>Количество задач</th>
                                <th>Процент</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td class="priority-{'high' if 'высокий' in row['priority_level'].lower() or 'критический' in row['priority_level'].lower() else 'medium' if 'средний' in row['priority_level'].lower() else 'low'}">{row['priority_level']}</td>
                                <td class="highlight"><strong>{row['task_count']:,}</strong></td>
                                <td class="percentage">{row['percentage']}%</td>
                            </tr>
                            ''' for _, row in priority_df.iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2 data-icon="💰">Анализ кастомных полей</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Поле</th>
                                <th>Категория</th>
                                <th>Всего</th>
                                <th>Заполнено</th>
                                <th>Заполненность</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([f'''
                            <tr>
                                <td>{row['field_name']}</td>
                                <td>{row['field_category']}</td>
                                <td>{row['total_count']:,}</td>
                                <td class="highlight"><strong>{row['filled_count']:,}</strong></td>
                                <td class="percentage">{row['fill_percentage']}%</td>
                            </tr>
                            ''' for _, row in custom_fields_df.iterrows()])}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2 data-icon="📊">Дополнительные метрики</h2>
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="metric-title">Максимум задач у постановщика</div>
                            <div class="metric-value">{business_metrics['assigner_metrics'].iloc[0]['max_tasks_per_assigner'] or 0:,}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Максимум задач у исполнителя</div>
                            <div class="metric-value">{business_metrics['assignee_metrics'].iloc[0]['max_tasks_per_assignee'] or 0:,}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">Среднее задач на исполнителя</div>
                            <div class="metric-value">{business_metrics['assignee_metrics'].iloc[0]['avg_tasks_per_assignee'] or 0}</div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Planfix Apple-Style Analytics Dashboard</strong></p>
                    <p>Профессиональный анализ в стиле Apple | Создан автоматически</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(f"{self.output_dir}/apple_style_dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🍎 Apple-style дашборд сохранен: {self.output_dir}/apple_style_dashboard.html")
    
    def _create_excel_report(self, status_df, assigner_df, assignee_df, 
                            custom_fields_df, priority_df, complexity_df, business_metrics):
        """Создает Excel отчет с метриками"""
        
        with pd.ExcelWriter(f"{self.output_dir}/apple_style_report.xlsx", engine='openpyxl') as writer:
            
            # Лист со статусами
            status_df.to_excel(writer, sheet_name='Статусы', index=False)
            
            # Лист с постановщиками
            assigner_df.to_excel(writer, sheet_name='Постановщики', index=False)
            
            # Лист с исполнителями
            assignee_df.to_excel(writer, sheet_name='Исполнители', index=False)
            
            # Лист с приоритетами
            priority_df.to_excel(writer, sheet_name='Приоритеты', index=False)
            
            # Лист с кастомными полями
            custom_fields_df.to_excel(writer, sheet_name='Кастомные поля', index=False)
            
            # Лист со сложностью
            complexity_df.to_excel(writer, sheet_name='Сложность', index=False)
            
            # Сводный лист
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
        
        print(f"📊 Excel отчет сохранен: {self.output_dir}/apple_style_report.xlsx")

if __name__ == "__main__":
    print("🍎 Apple-style Business Analytics Dashboard")
    print("=" * 50)
    
    dashboard = AppleStyleDashboard()
    dashboard.analyze_apple_metrics()
    
    print("\n✅ Apple-style анализ завершен!")
    print("📁 Файлы сохранены в папке output/")
    print("   - apple_style_dashboard.html - Apple-style HTML дашборд")
    print("   - apple_style_report.xlsx - Excel отчет с метриками")
