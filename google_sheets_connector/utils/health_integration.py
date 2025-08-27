"""
Утилиты для интеграции Google Sheets с данными здоровья
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connector import GoogleSheetsConnector

class HealthSheetsSync:
    """Класс для синхронизации данных здоровья с Google Sheets"""
    
    def __init__(self, connector: Optional[GoogleSheetsConnector] = None):
        """
        Инициализация синхронизации здоровья
        
        Args:
            connector: Готовый коннектор или None для создания нового
        """
        self.connector = connector or GoogleSheetsConnector()
        self.health_data_path = "../../Docs/Health/"
        
    def authenticate(self, service_account_file: str = "credentials/service_account.json") -> bool:
        """
        Аутентификация в Google Sheets
        
        Args:
            service_account_file: Путь к файлу Service Account
            
        Returns:
            bool: True если успешно
        """
        return self.connector.authenticate_service_account(service_account_file)
    
    def parse_medical_analysis(self, file_path: str) -> Dict[str, Any]:
        """
        Парсинг медицинского анализа из markdown файла
        
        Args:
            file_path: Путь к файлу анализа
            
        Returns:
            Dict с данными анализа
        """
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Извлекаем дату из имени файла
            filename = os.path.basename(file_path)
            date_str = filename.replace('analysis_report_', '').replace('.md', '')
            
            analysis_data = {
                'date': date_str,
                'file': filename,
                'metrics': {}
            }
            
            # Простой парсер для извлечения числовых показателей
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                # Определяем секции
                if line.startswith('##') and not line.startswith('###'):
                    current_section = line.replace('##', '').strip()
                    continue
                
                # Ищем строки с показателями (содержат цифры и единицы измерения)
                if ':' in line and any(char.isdigit() for char in line):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        metric_name = parts[0].strip()
                        value_text = parts[1].strip()
                        
                        # Извлекаем числовое значение
                        import re
                        numbers = re.findall(r'\d+\.?\d*', value_text)
                        if numbers:
                            try:
                                value = float(numbers[0])
                                analysis_data['metrics'][metric_name] = {
                                    'value': value,
                                    'text': value_text,
                                    'section': current_section
                                }
                            except ValueError:
                                pass
            
            return analysis_data
            
        except Exception as e:
            print(f"Ошибка парсинга файла {file_path}: {e}")
            return {}
    
    def collect_all_health_data(self) -> List[Dict[str, Any]]:
        """
        Собирает все данные здоровья из файлов анализов
        
        Returns:
            List[Dict]: Список всех анализов
        """
        health_files = []
        health_dir = os.path.join(os.path.dirname(__file__), self.health_data_path)
        
        if not os.path.exists(health_dir):
            print(f"Директория здоровья не найдена: {health_dir}")
            return []
        
        # Ищем все файлы анализов
        for filename in os.listdir(health_dir):
            if filename.startswith('analysis_report_') and filename.endswith('.md'):
                file_path = os.path.join(health_dir, filename)
                analysis_data = self.parse_medical_analysis(file_path)
                if analysis_data:
                    health_files.append(analysis_data)
        
        # Сортируем по дате
        health_files.sort(key=lambda x: x['date'])
        return health_files
    
    def create_health_summary_sheet(self, spreadsheet_id: str, sheet_name: str = "Health Summary") -> bool:
        """
        Создает сводный лист со всеми показателями здоровья
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            # Собираем все данные
            all_data = self.collect_all_health_data()
            if not all_data:
                print("Нет данных для синхронизации")
                return False
            
            # Создаем лист если не существует
            try:
                self.connector.create_sheet(spreadsheet_id, sheet_name)
            except:
                pass  # Лист уже существует
            
            # Собираем уникальные метрики
            all_metrics = set()
            for analysis in all_data:
                all_metrics.update(analysis['metrics'].keys())
            
            all_metrics = sorted(list(all_metrics))
            
            # Создаем заголовки
            headers = ['Дата', 'Файл'] + all_metrics
            
            # Подготавливаем данные для таблицы
            table_data = [headers]
            
            for analysis in all_data:
                row = [analysis['date'], analysis['file']]
                
                for metric in all_metrics:
                    if metric in analysis['metrics']:
                        value = analysis['metrics'][metric]['value']
                        row.append(str(value))
                    else:
                        row.append('')
                
                table_data.append(row)
            
            # Записываем в таблицу
            success = self.connector.write_range(
                spreadsheet_id, 
                f"{sheet_name}!A1", 
                table_data
            )
            
            if success:
                print(f"✅ Создан сводный лист '{sheet_name}' с {len(all_data)} записями")
                return True
            else:
                print("❌ Ошибка записи сводных данных")
                return False
                
        except Exception as e:
            print(f"Ошибка создания сводного листа: {e}")
            return False
    
    def create_metrics_trend_sheet(self, spreadsheet_id: str, sheet_name: str = "Health Trends") -> bool:
        """
        Создает лист с трендами основных показателей
        
        Args:
            spreadsheet_id: ID таблицы
            sheet_name: Название листа
            
        Returns:
            bool: True если успешно
        """
        try:
            # Собираем данные
            all_data = self.collect_all_health_data()
            if not all_data:
                return False
            
            # Создаем лист
            try:
                self.connector.create_sheet(spreadsheet_id, sheet_name)
            except:
                pass
            
            # Основные показатели для отслеживания
            key_metrics = [
                'Гемоглобин', 'Эритроциты', 'Лейкоциты', 'Тромбоциты',
                'Глюкоза', 'Холестерин', 'Креатинин', 'АЛТ', 'АСТ'
            ]
            
            # Подготавливаем данные
            trend_data = []
            headers = ['Дата'] + key_metrics + ['Общее количество показателей']
            trend_data.append(headers)
            
            for analysis in all_data:
                row = [analysis['date']]
                
                for metric in key_metrics:
                    # Ищем метрику в данных (поиск по подстроке)
                    found_value = ''
                    for data_metric, data in analysis['metrics'].items():
                        if metric.lower() in data_metric.lower():
                            found_value = str(data['value'])
                            break
                    row.append(found_value)
                
                # Общее количество показателей
                row.append(str(len(analysis['metrics'])))
                trend_data.append(row)
            
            # Записываем данные
            success = self.connector.write_range(
                spreadsheet_id,
                f"{sheet_name}!A1",
                trend_data
            )
            
            if success:
                print(f"✅ Создан лист трендов '{sheet_name}'")
                return True
            else:
                print("❌ Ошибка записи трендов")
                return False
                
        except Exception as e:
            print(f"Ошибка создания листа трендов: {e}")
            return False
    
    def sync_health_data(self, spreadsheet_id: Optional[str] = None) -> bool:
        """
        Полная синхронизация данных здоровья
        
        Args:
            spreadsheet_id: ID таблицы или None для использования из config
            
        Returns:
            bool: True если успешно
        """
        if not self.connector.is_connected():
            print("❌ Не подключен к Google Sheets")
            return False
        
        # Получаем ID таблицы
        if spreadsheet_id is None:
            spreadsheet_id = self.connector.get_config_spreadsheet('health_tracking')
        
        if not spreadsheet_id:
            print("❌ ID таблицы для здоровья не настроен")
            return False
        
        try:
            print(f"🔄 Синхронизация данных здоровья в таблицу {spreadsheet_id}")
            
            # Создаем листы с данными
            summary_success = self.create_health_summary_sheet(spreadsheet_id)
            trends_success = self.create_metrics_trend_sheet(spreadsheet_id)
            
            if summary_success and trends_success:
                print("✅ Синхронизация данных здоровья завершена успешно")
                return True
            else:
                print("⚠️ Синхронизация завершена с ошибками")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка синхронизации: {e}")
            return False
    
    def add_new_analysis(self, analysis_file: str, spreadsheet_id: Optional[str] = None) -> bool:
        """
        Добавляет новый анализ в таблицу
        
        Args:
            analysis_file: Путь к файлу анализа
            spreadsheet_id: ID таблицы
            
        Returns:
            bool: True если успешно
        """
        if not self.connector.is_connected():
            print("❌ Не подключен к Google Sheets")
            return False
        
        if spreadsheet_id is None:
            spreadsheet_id = self.connector.get_config_spreadsheet('health_tracking')
        
        if not spreadsheet_id:
            print("❌ ID таблицы не настроен")
            return False
        
        try:
            # Парсим новый анализ
            analysis_data = self.parse_medical_analysis(analysis_file)
            if not analysis_data:
                print("❌ Ошибка парсинга файла анализа")
                return False
            
            # Добавляем в лист Health Summary
            sheet_name = "Health Summary"
            
            # Читаем существующие заголовки
            try:
                headers_data = self.connector.read_range(spreadsheet_id, f"{sheet_name}!1:1")
                if headers_data and len(headers_data) > 0:
                    headers = headers_data[0]
                else:
                    # Если заголовков нет, пересоздаем лист
                    return self.sync_health_data(spreadsheet_id)
            except:
                # Лист не существует, создаем заново
                return self.sync_health_data(spreadsheet_id)
            
            # Подготавливаем новую строку
            new_row = [analysis_data['date'], analysis_data['file']]
            
            for i in range(2, len(headers)):  # Пропускаем Дата и Файл
                metric_name = headers[i]
                if metric_name in analysis_data['metrics']:
                    new_row.append(str(analysis_data['metrics'][metric_name]['value']))
                else:
                    new_row.append('')
            
            # Добавляем строку в конец таблицы
            success = self.connector.append_rows(
                spreadsheet_id,
                f"{sheet_name}!A:Z",
                [new_row]
            )
            
            if success:
                print(f"✅ Анализ от {analysis_data['date']} добавлен в таблицу")
                return True
            else:
                print("❌ Ошибка добавления анализа")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка добавления анализа: {e}")
            return False

def main():
    """Пример использования интеграции здоровья"""
    print("🏥 Google Sheets - Интеграция данных здоровья")
    print("=" * 50)
    
    # Создаем синхронизатор
    health_sync = HealthSheetsSync()
    
    # Аутентификация
    if not health_sync.authenticate():
        print("❌ Ошибка аутентификации")
        return
    
    # Получаем ID таблицы из конфигурации
    spreadsheet_id = health_sync.connector.get_config_spreadsheet('health_tracking')
    
    if not spreadsheet_id:
        print("❌ ID таблицы для здоровья не настроен в config.json")
        print("Добавьте 'health_tracking': 'your_spreadsheet_id' в config.json")
        return
    
    try:
        # Полная синхронизация
        print("🔄 Запуск полной синхронизации...")
        success = health_sync.sync_health_data(spreadsheet_id)
        
        if success:
            print("\n🎉 Синхронизация завершена!")
            print(f"📊 Откройте таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        else:
            print("\n❌ Синхронизация не удалась")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
