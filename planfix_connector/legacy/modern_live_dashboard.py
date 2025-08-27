from flask import Flask, render_template_string, jsonify, request
import sqlite3
import requests
import json
import pandas as pd
from datetime import datetime
import re
from typing import Dict, List, Any, Optional
import threading
import time

class ModernLiveDashboard:
    def __init__(self):
        self.config = self.load_config()
        self.db_path = 'output/planfix_tasks_correct.db'
        self.app = Flask(__name__)
        self.setup_routes()
        self.last_update = None
        self.update_interval = 300  # 5 минут
        self.is_updating = False
        
    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из JSON файла"""
        try:
            with open('planfix_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return {}
    
    def setup_routes(self):
        """Настраивает маршруты Flask"""
        @self.app.route('/')
        def dashboard():
            return self.get_dashboard_html()
        
        @self.app.route('/api/data')
        def get_data():
            return jsonify(self.get_current_data())
        
        @self.app.route('/api/update', methods=['POST'])
        def update_data():
            return jsonify(self.update_from_api())
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'last_update': self.last_update,
                'is_updating': self.is_updating,
                'total_tasks': self.get_total_tasks_count()
            })
    
    def get_current_data(self) -> Dict[str, Any]:
        """Получает текущие данные из базы данных для дашборда"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем основные данные
            cursor.execute('''
                SELECT id, name, description, status_name, assignees, assigner, start_date_time
                FROM tasks 
                ORDER BY id DESC 
                LIMIT 50
            ''')
            tasks = cursor.fetchall()
            
            # Получаем кастомные поля
            cursor.execute('''
                SELECT task_id, field_name, field_value 
                FROM custom_field_values 
                WHERE task_id IN (SELECT id FROM tasks ORDER BY id DESC LIMIT 50)
            ''')
            custom_fields = cursor.fetchall()
            
            # Получаем статистику
            cursor.execute('SELECT COUNT(*) FROM tasks')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT status_name, COUNT(*) FROM tasks GROUP BY status_name')
            status_stats = dict(cursor.fetchall())
            
            conn.close()
            
            # Формируем данные для дашборда
            dashboard_data = {
                'tasks': [],
                'total_tasks': total_tasks,
                'status_stats': status_stats,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
            # Обрабатываем задачи
            for task in tasks:
                task_id, name, description, status, assignees, assigner, start_date = task
                
                # Получаем кастомные поля для этой задачи
                task_custom_fields = {}
                for cf in custom_fields:
                    if cf[0] == task_id:
                        task_custom_fields[cf[1]] = cf[2]
                
                # Рассчитываем приоритет по новой формуле
                calculated_priority = self.calculate_advanced_priority(task_custom_fields)
                
                dashboard_data['tasks'].append({
                    'id': task_id,
                    'name': name[:100] + '...' if len(name) > 100 else name,
                    'status': status,
                    'assignees': assignees or 'Не назначен',
                    'assigner': assigner or 'Не указан',
                    'start_date': start_date,
                    'client_grade': task_custom_fields.get('Грейд клиента', 'Н/Д'),
                    'order_percentage': task_custom_fields.get('% заказа', 'Н/Д'),
                    'deal_sum': task_custom_fields.get('Сумма сделки', 'Н/Д'),
                    'calculation_sum': task_custom_fields.get('Сумма просчета', 'Н/Д'),
                    'calculated_priority': calculated_priority
                })
            
            return dashboard_data
            
        except Exception as e:
            print(f"❌ Ошибка получения данных: {e}")
            return {'error': str(e)}
    
    def calculate_advanced_priority(self, custom_fields: Dict[str, str]) -> str:
        """Рассчитывает приоритет по новой формуле"""
        try:
            # Получаем значения полей
            client_grade = self.parse_numeric(custom_fields.get('Грейд клиента'), 3.0)
            order_percentage = self.parse_numeric(custom_fields.get('% заказа'), 50.0)
            deal_sum = self.parse_numeric(custom_fields.get('Сумма сделки'), 0)
            calculation_sum = self.parse_numeric(custom_fields.get('Сумма просчета'), 0)
            
            # Используем максимальную сумму из двух полей
            max_sum = max(deal_sum, calculation_sum)
            
            # Формула приоритета (адаптированная из Excel)
            grade_score = (client_grade / 5.0) * 0.4
            
            # Расчет по сумме
            if max_sum <= 250000:
                sum_score = 0.2
            elif max_sum <= 1000000:
                sum_score = 0.4
            elif max_sum <= 5000000:
                sum_score = 0.6
            elif max_sum <= 10000000:
                sum_score = 0.8
            else:
                sum_score = 1.0
            
            sum_score = sum_score * 0.4
            
            # Расчет по проценту заказа
            percentage_score = (order_percentage / 100.0) * 0.2
            
            # Итоговый балл
            total_score = grade_score + sum_score + percentage_score
            
            # Определение приоритета
            if total_score >= 0.8:
                return 'A'
            elif total_score >= 0.6:
                return 'B'
            elif total_score >= 0.4:
                return 'C'
            else:
                return 'D'
                
        except Exception as e:
            print(f"❌ Ошибка расчета приоритета: {e}")
            return 'D'
    
    def parse_numeric(self, value: Any, default: float = 0.0) -> float:
        """Парсит числовое значение из строки"""
        if value is None:
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Убираем все нечисловые символы, кроме точки и минуса
            cleaned = re.sub(r'[^\d.-]', '', value)
            try:
                return float(cleaned) if cleaned else default
            except ValueError:
                return default
        
        return default
    
    def update_from_api(self) -> Dict[str, Any]:
        """Обновляет данные из API"""
        if self.is_updating:
            return {'status': 'error', 'message': 'Обновление уже выполняется'}
        
        try:
            self.is_updating = True
            
            # Получаем задачи из API
            headers = {
                'Authorization': f'Bearer {self.config["rest_api"]["auth_token"]}',
                'Content-Type': 'application/json'
            }
            
            fields = [
                'id', 'name', 'description', 'status', 'startDateTime', 'endDateTime', 
                'deadline', 'assigner', 'assignees', 'priority', 'importance'
            ]
            
            # Добавляем кастомные поля
            custom_fields = [
                'custom_1', 'custom_2', 'custom_3', 'custom_4', 'custom_5',
                'custom_6', 'custom_7', 'custom_8', 'custom_9', 'custom_10'
            ]
            fields.extend(custom_fields)
            
            request_data = {
                'offset': 0,
                'pageSize': 100,
                'filters': [
                    {
                        "type": 10,  # Статус
                        "operator": "equal",
                        "value": [127, 128, 129]  # Статусы: Поиск, Согласование, Согласовано
                    }
                ],
                'fields': ','.join(fields)
            }
            
            response = requests.post(
                f"{self.config['rest_api']['base_url']}/task/list",
                headers=headers,
                json=request_data,
                timeout=self.config['rest_api']['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('tasks', [])
                
                # Обновляем базу данных
                self.update_database_with_new_data(tasks)
                
                self.last_update = datetime.now()
                return {
                    'status': 'success',
                    'message': f'Обновлено {len(tasks)} задач',
                    'tasks_count': len(tasks)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Ошибка API: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка обновления: {str(e)}'
            }
        finally:
            self.is_updating = False
    
    def update_database_with_new_data(self, tasks: List[Dict[str, Any]]):
        """Обновляет базу данных новыми данными"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу для кастомных полей, если её нет
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_field_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    field_name TEXT,
                    field_value TEXT,
                    field_type TEXT,
                    UNIQUE(task_id, field_name)
                )
            ''')
            
            for task in tasks:
                # Обновляем основную таблицу
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (id, name, description, status_id, status_name, assignees, assigner, start_date_time, export_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.get('id'),
                    task.get('name', ''),
                    task.get('description', ''),
                    self.get_status_id(task.get('status', {}).get('name', '')),
                    task.get('status', {}).get('name', ''),
                    self.extract_assignees(task.get('assignees', [])),
                    task.get('assigner', {}).get('name', '') if task.get('assigner') else '',
                    self.extract_date(task),
                    datetime.now().isoformat()
                ))
                
                # Добавляем кастомные поля
                custom_fields = [
                    ('Грейд клиента', self.extract_custom_field_value(task, 'Грейд клиента'), 'numeric'),
                    ('% заказа', self.extract_custom_field_value(task, '% заказа'), 'percentage'),
                    ('Сумма сделки', self.extract_custom_field_value(task, 'Сумма сделки'), 'currency'),
                    ('Расчет - Приоритет просчета', self.extract_custom_field_value(task, 'Расчет - Приоритет просчета'), 'text'),
                    ('Сумма просчета', self.extract_custom_field_value(task, 'Сумма просчета'), 'currency')
                ]
                
                for field_name, field_value, field_type in custom_fields:
                    if field_value is not None:
                        cursor.execute('''
                            INSERT OR REPLACE INTO custom_field_values 
                            (task_id, field_name, field_value, field_type)
                            VALUES (?, ?, ?, ?)
                        ''', (task.get('id'), field_name, str(field_value), field_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Ошибка обновления базы данных: {e}")
    
    def extract_custom_field_value(self, task: Dict[str, Any], field_name: str) -> Optional[Any]:
        """Извлекает значение кастомного поля из задачи"""
        if 'customFields' in task:
            for field in task['customFields']:
                if field.get('name') == field_name:
                    return field.get('value')
        
        for key in task.keys():
            if field_name.lower() in key.lower():
                return task.get(key)
        
        return None
    
    def extract_date(self, task: Dict[str, Any]) -> Optional[str]:
        """Извлекает дату из задачи"""
        if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
            return task['endDateTime'].get('datetime')
        if task.get('startDateTime') and isinstance(task['startDateTime'], dict):
            return task['startDateTime'].get('datetime')
        if task.get('createDate'):
            return task['createDate']
        return None
    
    def extract_assignees(self, assignees) -> str:
        """Извлекает список исполнителей"""
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
    
    def get_status_id(self, status_name: str) -> int:
        """Возвращает ID статуса по имени"""
        status_mapping = {
            'Поиск и расчет товара': 128,
            'КП Согласование': 129,
            'КП Согласовано': 127
        }
        return status_mapping.get(status_name, 128)
    
    def get_total_tasks_count(self) -> int:
        """Возвращает общее количество задач"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM tasks')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def get_dashboard_html(self) -> str:
        """Генерирует HTML для современного дашборда"""
        return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Современный Дашборд Planfix 2025</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #2c3e50;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            z-index: -1;
        }
        
        .header h1 {
            font-size: 3.5em;
            margin-bottom: 15px;
            font-weight: 300;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            font-size: 1.3em;
            color: #7f8c8d;
            margin-bottom: 20px;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 50px;
            font-size: 1em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.9);
            color: #2c3e50;
            border: 2px solid #ecf0f1;
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 1);
            transform: translateY(-2px);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(45deg, #667eea, #764ba2);
        }
        
        .stat-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 30px 60px rgba(0,0,0,0.15);
        }
        
        .stat-card h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.4em;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .stat-value {
            font-size: 3em;
            font-weight: 700;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
        }
        
        .stat-description {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .main-content {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .content-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .content-header h2 {
            font-size: 2em;
            font-weight: 400;
            color: #2c3e50;
        }
        
        .refresh-info {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .tasks-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .tasks-table th {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 18px 15px;
            text-align: left;
            font-weight: 500;
            font-size: 1.1em;
        }
        
        .tasks-table td {
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            transition: background 0.3s ease;
        }
        
        .tasks-table tr:hover td {
            background: #f8f9fa;
        }
        
        .priority-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            text-align: center;
            min-width: 30px;
        }
        
        .priority-a { background: #ff6b6b; color: white; }
        .priority-b { background: #feca57; color: white; }
        .priority-c { background: #48dbfb; color: white; }
        .priority-d { background: #95a5a6; color: white; }
        
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 500;
            font-size: 0.9em;
            background: #ecf0f1;
            color: #2c3e50;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5em;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .controls {
                flex-direction: column;
                align-items: center;
            }
            
            .content-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Современный Дашборд Planfix 2025</h1>
            <p>Реальное время • Автообновление • Новая формула приоритетов</p>
            <div class="controls">
                <button class="btn btn-primary" onclick="updateData()">
                    🔄 Обновить данные
                </button>
                <button class="btn btn-secondary" onclick="location.reload()">
                    📊 Обновить страницу
                </button>
                <span class="refresh-info">
                    <span id="lastUpdate">Последнее обновление: Загрузка...</span>
                </span>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 Общее количество задач</h3>
                <div class="stat-value" id="totalTasks">-</div>
                <div class="stat-description">Активных задач в системе</div>
            </div>
            
            <div class="stat-card">
                <h3>📈 Задач в статусе "Поиск"</h3>
                <div class="stat-value" id="statusSearch">-</div>
                <div class="stat-description">Требуют расчета</div>
            </div>
            
            <div class="stat-card">
                <h3>📋 Задач в статусе "КП Согласование"</h3>
                <div class="stat-value" id="statusKp">-</div>
                <div class="stat-description">Ожидают согласования</div>
            </div>
            
            <div class="stat-card">
                <h3>✅ Задач в статусе "КП Согласовано"</h3>
                <div class="stat-value" id="statusApproved">-</div>
                <div class="stat-description">Успешно согласованы</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="content-header">
                <h2>📋 Последние задачи</h2>
                <div class="refresh-info">
                    <span id="updateStatus">Готов к обновлению</span>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Обновление данных...</p>
            </div>
            
            <div id="tasksContainer">
                <table class="tasks-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Название</th>
                            <th>Статус</th>
                            <th>Приоритет</th>
                            <th>Грейд клиента</th>
                            <th>% заказа</th>
                            <th>Сумма сделки</th>
                            <th>Исполнитель</th>
                            <th>Постановщик</th>
                        </tr>
                    </thead>
                    <tbody id="tasksTableBody">
                        <tr>
                            <td colspan="9" style="text-align: center; padding: 40px; color: #7f8c8d;">
                                Загрузка данных...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Дашборд автоматически обновляется каждые 5 минут • Последнее обновление: <span id="footerUpdate">-</span></p>
        </div>
    </div>
    
    <script>
        let updateInterval;
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
            startAutoUpdate();
        });
        
        // Загрузка данных
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                if (data.error) {
                    console.error('Ошибка загрузки данных:', data.error);
                    return;
                }
                
                updateDashboard(data);
            } catch (error) {
                console.error('Ошибка загрузки данных:', error);
            }
        }
        
        // Обновление данных
        async function updateData() {
            const loading = document.getElementById('loading');
            const updateStatus = document.getElementById('updateStatus');
            
            loading.classList.add('show');
            updateStatus.textContent = 'Обновление...';
            
            try {
                const response = await fetch('/api/update', { method: 'POST' });
                const result = await response.json();
                
                if (result.status === 'success') {
                    updateStatus.textContent = `Обновлено: ${result.tasks_count} задач`;
                    await loadData(); // Перезагружаем данные
                } else {
                    updateStatus.textContent = `Ошибка: ${result.message}`;
                }
            } catch (error) {
                updateStatus.textContent = 'Ошибка обновления';
                console.error('Ошибка обновления:', error);
            } finally {
                loading.classList.remove('show');
            }
        }
        
        // Обновление дашборда
        function updateDashboard(data) {
            // Обновляем статистику
            document.getElementById('totalTasks').textContent = data.total_tasks || 0;
            document.getElementById('statusSearch').textContent = data.status_stats['Поиск и расчет товара'] || 0;
            document.getElementById('statusKp').textContent = data.status_stats['КП Согласование'] || 0;
            document.getElementById('statusApproved').textContent = data.status_stats['КП Согласовано'] || 0;
            
            // Обновляем таблицу задач
            const tbody = document.getElementById('tasksTableBody');
            tbody.innerHTML = '';
            
            if (data.tasks && data.tasks.length > 0) {
                data.tasks.forEach(task => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${task.id}</td>
                        <td>${task.name}</td>
                        <td><span class="status-badge">${task.status}</span></td>
                        <td><span class="priority-badge priority-${task.calculated_priority.toLowerCase()}">${task.calculated_priority}</span></td>
                        <td>${task.client_grade}</td>
                        <td>${task.order_percentage}</td>
                        <td>${task.deal_sum}</td>
                        <td>${task.assignees}</td>
                        <td>${task.assigner}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" style="text-align: center; padding: 40px; color: #7f8c8d;">
                            Нет данных для отображения
                        </td>
                    </tr>
                `;
            }
            
            // Обновляем информацию о последнем обновлении
            if (data.last_update) {
                const lastUpdate = new Date(data.last_update);
                document.getElementById('lastUpdate').textContent = `Последнее обновление: ${lastUpdate.toLocaleString('ru-RU')}`;
                document.getElementById('footerUpdate').textContent = lastUpdate.toLocaleString('ru-RU');
            }
        }
        
        // Автообновление
        function startAutoUpdate() {
            updateInterval = setInterval(loadData, 300000); // 5 минут
        }
        
        // Остановка автообновления при закрытии страницы
        window.addEventListener('beforeunload', function() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>
        """
    
    def start_dashboard(self, port: int = 8055):
        """Запускает дашборд"""
        print(f"🚀 Запуск современного дашборда на порту {port}...")
        print(f"🌐 Откройте браузер: http://localhost:{port}")
        print("⏰ Дашборд будет автоматически обновляться каждые 5 минут")
        
        try:
            self.app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        except Exception as e:
            print(f"❌ Ошибка запуска дашборда: {e}")

if __name__ == "__main__":
    dashboard = ModernLiveDashboard()
    dashboard.start_dashboard()
