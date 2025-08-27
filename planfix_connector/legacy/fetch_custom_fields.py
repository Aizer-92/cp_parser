#!/usr/bin/env python3
"""
Получение кастомных полей из API Planfix
"""

import sqlite3
import json
import requests
import pandas as pd
from datetime import datetime
import os

class CustomFieldsFetcher:
    def __init__(self):
        self.config = self.load_config()
        self.db_path = 'output/planfix_tasks_correct.db'
        
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open('planfix_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return {}
    
    def get_task_custom_fields(self, task_id):
        """Получение кастомных полей для конкретной задачи"""
        try:
            headers = {
                'Authorization': f'Bearer {self.config["rest_api"]["auth_token"]}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.config['rest_api']['base_url']}/task/{task_id}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'task' in data:
                task = data['task']
                custom_fields = task.get('customFieldData', [])
                return custom_fields
            
            return []
            
        except Exception as e:
            print(f"❌ Ошибка получения кастомных полей для задачи {task_id}: {e}")
            return []
    
    def get_all_task_ids(self):
        """Получение всех ID задач из базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM tasks')
            task_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return task_ids
            
        except Exception as e:
            print(f"❌ Ошибка получения ID задач: {e}")
            return []
    
    def save_custom_fields_to_db(self, custom_fields_data):
        """Сохранение кастомных полей в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Очищаем существующие данные
            cursor.execute('DELETE FROM custom_field_values')
            
            # Вставляем новые данные
            for task_id, fields in custom_fields_data.items():
                for field_name, field_value in fields.items():
                    cursor.execute('''
                        INSERT INTO custom_field_values (task_id, field_name, field_value, field_type)
                        VALUES (?, ?, ?, ?)
                    ''', (task_id, field_name, str(field_value), 'text'))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Сохранено {len(custom_fields_data)} задач с кастомными полями")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в БД: {e}")
    
    def fetch_all_custom_fields(self, limit=None):
        """Получение кастомных полей для всех задач"""
        print("🔍 Получение ID всех задач...")
        task_ids = self.get_all_task_ids()
        
        if limit:
            task_ids = task_ids[:limit]
        
        print(f"📊 Получение кастомных полей для {len(task_ids)} задач...")
        
        custom_fields_data = {}
        processed = 0
        
        for task_id in task_ids:
            try:
                custom_fields = self.get_task_custom_fields(task_id)
                
                if custom_fields:
                    # Преобразуем в удобный формат
                    fields_dict = {}
                    for field in custom_fields:
                        field_name = field.get('name', '')
                        field_value = field.get('value', '')
                        if field_name and field_value:
                            fields_dict[field_name] = field_value
                    
                    if fields_dict:
                        custom_fields_data[task_id] = fields_dict
                
                processed += 1
                if processed % 10 == 0:
                    print(f"  ✅ Обработано {processed}/{len(task_ids)} задач")
                
                # Небольшая задержка для избежания rate limiting
                import time
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ⚠️ Ошибка обработки задачи {task_id}: {e}")
                continue
        
        print(f"✅ Получено кастомных полей для {len(custom_fields_data)} задач")
        
        # Сохраняем в базу данных
        self.save_custom_fields_to_db(custom_fields_data)
        
        return custom_fields_data
    
    def run_fetch(self, limit=50):
        """Запуск получения кастомных полей"""
        print("🚀 Запуск получения кастомных полей")
        print("=" * 80)
        
        custom_fields = self.fetch_all_custom_fields(limit)
        
        if custom_fields:
            print("\n📊 Примеры кастомных полей:")
            for task_id, fields in list(custom_fields.items())[:3]:
                print(f"  Задача {task_id}:")
                for field_name, field_value in fields.items():
                    print(f"    {field_name}: {field_value}")
                print()
        
        print("🎉 Получение кастомных полей завершено!")

def main():
    fetcher = CustomFieldsFetcher()
    fetcher.run_fetch(limit=50)  # Ограничиваем для тестирования

if __name__ == "__main__":
    main()
