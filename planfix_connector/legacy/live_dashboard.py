#!/usr/bin/env python3
"""
Живой дашборд для Planfix Connector
Обновляемый в реальном времени с актуальными задачами
"""

import sqlite3
import json
import requests
from datetime import datetime, timedelta
import os
import pandas as pd
from flask import Flask, render_template_string, jsonify, request
import threading
import time

class LiveDashboard:
    def __init__(self):
        self.config = self.load_config()
        self.db_path = 'output/planfix_tasks_correct.db'
        self.app = Flask(__name__)
        self.setup_routes()
        self.last_update = None
        self.update_interval = 300  # 5 минут
        
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open('planfix_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return None
    
    def setup_routes(self):
        """Настройка маршрутов Flask"""
        
        @self.app.route('/')
        def dashboard():
            return self.get_dashboard_html()
        
        @self.app.route('/api/data')
        def get_data():
            return jsonify(self.get_current_data())
        
        @self.app.route('/api/update')
        def update_data():
            success = self.update_from_api()
            return jsonify({'success': success, 'timestamp': datetime.now().isoformat()})
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'update_interval': self.update_interval,
                'next_update': (self.last_update + timedelta(seconds=self.update_interval)).isoformat() if self.last_update else None
            })
    
    def get_current_data(self):
        """Получение текущих данных из БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Основная статистика
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE start_date_time IS NOT NULL AND start_date_time != ''")
            tasks_with_dates = cursor.fetchone()[0]
            
            # Статистика по статусам
            cursor.execute("""
                SELECT 
                    status_id,
                    status_name,
                    COUNT(*) as total,
                    COUNT(start_date_time) as with_dates
                FROM tasks 
                GROUP BY status_id, status_name
                ORDER BY status_id
            """)
            status_stats = cursor.fetchall()
            
            # Статистика по исполнителям
            cursor.execute("""
                SELECT 
                    assignees,
                    COUNT(*) as count
                FROM tasks 
                WHERE assignees IS NOT NULL AND assignees != ''
                GROUP BY assignees
                ORDER BY count DESC
                LIMIT 10
            """)
            assignee_stats = cursor.fetchall()
            
            # Статистика по постановщикам
            cursor.execute("""
                SELECT 
                    assigner,
                    COUNT(*) as count
                FROM tasks 
                WHERE assigner IS NOT NULL AND assigner != ''
                GROUP BY assigner
                ORDER BY count DESC
                LIMIT 10
            """)
            assigner_stats = cursor.fetchall()
            
            # Анализ по датам
            cursor.execute("""
                SELECT 
                    start_date_time,
                    COUNT(*) as count
                FROM tasks 
                WHERE start_date_time IS NOT NULL AND start_date_time != ''
                GROUP BY start_date_time
                ORDER BY start_date_time DESC
                LIMIT 20
            """)
            date_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_tasks': total_tasks,
                'tasks_with_dates': tasks_with_dates,
                'coverage_percentage': round(tasks_with_dates / total_tasks * 100, 1) if total_tasks > 0 else 0,
                'status_stats': [{'id': s[0], 'name': s[1], 'total': s[2], 'with_dates': s[3]} for s in status_stats],
                'assignee_stats': [{'name': a[0], 'count': a[1]} for a in assignee_stats],
                'assigner_stats': [{'name': a[0], 'count': a[1]} for a in assigner_stats],
                'date_stats': [{'date': d[0], 'count': d[1]} for d in date_stats],
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            print(f"❌ Ошибка получения данных: {e}")
            return {}
    
    def update_from_api(self):
        """Обновление данных из API"""
        print("🔄 Обновление данных из API...")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.config["rest_api"]["auth_token"]}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.config['rest_api']['base_url']}/task/list"
            
            request_data = {
                "offset": 0,
                "pageSize": 100,
                "filters": [
                    {
                        "type": 10,  # Статус
                        "operator": "equal",
                        "value": [127, 128, 129]  # Статусы: Поиск, Согласование, Согласовано
                    }
                ],
                "fields": "id,name,description,status,startDateTime,endDateTime,assigner,assignees"
            }
            
            response = requests.post(url, headers=headers, json=request_data)
            response.raise_for_status()
            
            data = response.json()
            if 'tasks' in data:
                tasks = data['tasks']
                print(f"✅ Получено {len(tasks)} актуальных задач")
                
                # Обновляем базу данных
                if self.update_database_with_new_data(tasks):
                    self.last_update = datetime.now()
                    print("✅ Данные успешно обновлены")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка обновления из API: {e}")
            return False
    
    def update_database_with_new_data(self, tasks):
        """Обновление базы данных новыми данными"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            for task in tasks:
                try:
                    # Извлекаем дату
                    date_value = None
                    if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                        date_value = task['endDateTime'].get('datetime')
                    elif task.get('startDateTime') and isinstance(task['startDateTime'], dict):
                        date_value = task['startDateTime'].get('datetime')
                    
                    if date_value:
                        date_str = date_value.split('+')[0].split('T')[0]
                        
                        # Обновляем или добавляем задачу
                        cursor.execute("""
                            INSERT OR REPLACE INTO tasks 
                            (id, name, description, status_id, status_name, assigner, assignees, start_date_time, export_timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            task['id'],
                            task.get('name', ''),
                            task.get('description', ''),
                            task.get('status', {}).get('id', 0),
                            task.get('status', {}).get('name', ''),
                            task.get('assigner', {}).get('name', '') if isinstance(task.get('assigner'), dict) else str(task.get('assigner', '')),
                            self.extract_assignees(task.get('assignees')),
                            date_str,
                            datetime.now().isoformat()
                        ))
                        
                        updated_count += 1
                        
                except Exception as e:
                    print(f"    ❌ Ошибка обновления задачи {task.get('id')}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Обновлено задач: {updated_count}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления БД: {e}")
            return False
    
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
    
    def get_dashboard_html(self):
        """Генерация HTML дашборда"""
        return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔄 Живой дашборд Planfix Connector</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .update-bar {
            background: #f8f9fa;
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        .update-button {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 0 10px;
        }
        .update-button:hover {
            background: #218838;
        }
        .update-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
        .content {
            padding: 40px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border-left: 5px solid #667eea;
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        .stat-label {
            font-size: 1.1em;
            color: #666;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }
        .loading {
            opacity: 0.5;
            pointer-events: none;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Живой дашборд</h1>
            <p>Planfix Connector - Обновляемый в реальном времени</p>
        </div>
        
        <div class="update-bar">
            <span class="status-indicator status-online" id="statusIndicator"></span>
            <span id="statusText">Подключено к API</span>
            <button class="update-button" onclick="updateData()" id="updateButton">
                🔄 Обновить данные
            </button>
            <span id="lastUpdate">Последнее обновление: Загрузка...</span>
        </div>
        
        <div class="content" id="dashboardContent">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="totalTasks">-</div>
                    <div class="stat-label">Всего задач</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="tasksWithDates">-</div>
                    <div class="stat-label">Задач с датами</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="coveragePercentage">-</div>
                    <div class="stat-label">Покрытие датами</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="uniqueAssignees">-</div>
                    <div class="stat-label">Уникальных исполнителей</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Статистика по статусам</h2>
                <div class="table-container">
                    <table id="statusTable">
                        <thead>
                            <tr>
                                <th>Статус</th>
                                <th>Всего задач</th>
                                <th>С датами</th>
                                <th>Покрытие</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="4">Загрузка...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>👥 Топ исполнителей</h2>
                <div class="table-container">
                    <table id="assigneeTable">
                        <thead>
                            <tr>
                                <th>Исполнитель</th>
                                <th>Количество задач</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="2">Загрузка...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📝 Топ постановщиков</h2>
                <div class="table-container">
                    <table id="assignerTable">
                        <thead>
                            <tr>
                                <th>Постановщик</th>
                                <th>Количество задач</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="2">Загрузка...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🔄 Planfix Connector - Живой дашборд | Автообновление каждые 5 минут</p>
        </div>
    </div>
    
    <script>
        let updateInterval;
        
        // Загрузка данных при старте
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
            startAutoUpdate();
        });
        
        function loadData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(error => {
                    console.error('Ошибка загрузки данных:', error);
                });
        }
        
        function updateData() {
            const updateButton = document.getElementById('updateButton');
            const statusText = document.getElementById('statusText');
            const statusIndicator = document.getElementById('statusIndicator');
            
            updateButton.disabled = true;
            updateButton.textContent = '🔄 Обновление...';
            statusText.textContent = 'Обновление данных...';
            statusIndicator.className = 'status-indicator pulse';
            
            fetch('/api/update')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusText.textContent = 'Данные обновлены';
                        statusIndicator.className = 'status-indicator status-online';
                        loadData(); // Перезагружаем данные
                    } else {
                        statusText.textContent = 'Ошибка обновления';
                        statusIndicator.className = 'status-indicator status-offline';
                    }
                })
                .catch(error => {
                    console.error('Ошибка обновления:', error);
                    statusText.textContent = 'Ошибка обновления';
                    statusIndicator.className = 'status-indicator status-offline';
                })
                .finally(() => {
                    updateButton.disabled = false;
                    updateButton.textContent = '🔄 Обновить данные';
                });
        }
        
        function updateDashboard(data) {
            // Обновляем основную статистику
            document.getElementById('totalTasks').textContent = data.total_tasks || 0;
            document.getElementById('tasksWithDates').textContent = data.tasks_with_dates || 0;
            document.getElementById('coveragePercentage').textContent = (data.coverage_percentage || 0) + '%';
            document.getElementById('uniqueAssignees').textContent = data.assignee_stats?.length || 0;
            
            // Обновляем таблицу статусов
            updateStatusTable(data.status_stats || []);
            
            // Обновляем таблицу исполнителей
            updateAssigneeTable(data.assignee_stats || []);
            
            // Обновляем таблицу постановщиков
            updateAssignerTable(data.assigner_stats || []);
            
            // Обновляем информацию о последнем обновлении
            if (data.last_update) {
                const lastUpdate = new Date(data.last_update);
                document.getElementById('lastUpdate').textContent = 
                    'Последнее обновление: ' + lastUpdate.toLocaleString('ru-RU');
            }
        }
        
        function updateStatusTable(statusStats) {
            const tbody = document.querySelector('#statusTable tbody');
            tbody.innerHTML = '';
            
            statusStats.forEach(status => {
                const coverage = status.total > 0 ? Math.round(status.with_dates / status.total * 100) : 0;
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td><strong>${status.name || 'Не указан'}</strong></td>
                    <td>${status.total}</td>
                    <td>${status.with_dates}</td>
                    <td>
                        ${coverage}%
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${coverage}%"></div>
                        </div>
                    </td>
                `;
            });
        }
        
        function updateAssigneeTable(assigneeStats) {
            const tbody = document.querySelector('#assigneeTable tbody');
            tbody.innerHTML = '';
            
            assigneeStats.forEach(assignee => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${assignee.name || 'Не указан'}</td>
                    <td>${assignee.count}</td>
                `;
            });
        }
        
        function updateAssignerTable(assignerStats) {
            const tbody = document.querySelector('#assignerTable tbody');
            tbody.innerHTML = '';
            
            assignerStats.forEach(assigner => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${assigner.name || 'Не указан'}</td>
                    <td>${assigner.count}</td>
                `;
            });
        }
        
        function startAutoUpdate() {
            updateInterval = setInterval(() => {
                loadData();
            }, 300000); // 5 минут
        }
        
        function stopAutoUpdate() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        }
        
        // Очистка при закрытии страницы
        window.addEventListener('beforeunload', stopAutoUpdate);
    </script>
</body>
</html>
        """
    
    def start_dashboard(self, port=8055):
        """Запуск дашборда"""
        print(f"🚀 Запуск живого дашборда на порту {port}")
        print("🌐 Откройте: http://localhost:" + str(port))
        
        # Первоначальное обновление данных
        self.update_from_api()
        
        # Запускаем Flask приложение
        self.app.run(host='0.0.0.0', port=port, debug=False)

def main():
    """Основная функция"""
    dashboard = LiveDashboard()
    dashboard.start_dashboard()

if __name__ == "__main__":
    main()

