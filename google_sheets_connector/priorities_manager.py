"""
Менеджер для работы с таблицей приоритетов проектов
Специализированный инструмент для анализа и управления проектами
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from connector import GoogleSheetsConnector
    
    class PrioritiesManager:
        """Менеджер таблицы приоритетов проектов"""
        
        def __init__(self, spreadsheet_id: str = None):
            """
            Инициализация менеджера
            
            Args:
                spreadsheet_id: ID таблицы приоритетов
            """
            self.connector = GoogleSheetsConnector()
            self.spreadsheet_id = spreadsheet_id or "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
            self.sheet_name = "Лист1"  # Основной лист с данными
            
            # Определяем колонки
            self.columns = {
                'name': 'A',          # Название
                'status': 'B',        # Статус
                'client_grade': 'C',  # Грейд клиента
                'order_percent': 'D', # % заказа
                'deadline': 'E',      # Сроки
                'complexity': 'F',    # Сложность
                'deal_amount': 'G',   # Сумма сделки
                'calculation': 'H',   # Сумма просчета
                'manager': 'I',       # Постановщик
                'executors': 'J',     # Исполнители
                'create_date': 'K',   # Дата создания
                'process': 'L',       # Процесс
                'priority': 'M'       # Приоритет
            }
        
        def authenticate(self, credentials_file: str = "credentials/quickstart-1591698112539-676a9e339335.json") -> bool:
            """Аутентификация"""
            return self.connector.authenticate_service_account(credentials_file)
        
        def get_all_projects(self) -> pd.DataFrame:
            """
            Получает все проекты из таблицы
            
            Returns:
                pd.DataFrame: Все проекты
            """
            try:
                # Читаем все данные с основного листа
                df = self.connector.read_to_dataframe(
                    self.spreadsheet_id, 
                    f"{self.sheet_name}!A:M", 
                    header_row=True
                )
                
                # Очищаем данные
                df = df.dropna(how='all')  # Удаляем пустые строки
                df = df[df.iloc[:, 0].notna()]  # Удаляем строки без названия
                
                return df
                
            except Exception as e:
                print(f"❌ Ошибка получения проектов: {e}")
                return pd.DataFrame()
        
        def get_projects_by_status(self, status: str) -> pd.DataFrame:
            """
            Получает проекты по статусу
            
            Args:
                status: Статус проекта
                
            Returns:
                pd.DataFrame: Проекты с указанным статусом
            """
            df = self.get_all_projects()
            if df.empty:
                return df
            
            return df[df['Статус'].str.contains(status, case=False, na=False)]
        
        def get_projects_by_executor(self, executor: str) -> pd.DataFrame:
            """
            Получает проекты исполнителя
            
            Args:
                executor: Имя исполнителя
                
            Returns:
                pd.DataFrame: Проекты исполнителя
            """
            df = self.get_all_projects()
            if df.empty:
                return df
            
            return df[df['Исполнители'].str.contains(executor, case=False, na=False)]
        
        def analyze_workload(self) -> Dict[str, Any]:
            """
            Анализирует нагрузку по исполнителям
            
            Returns:
                Dict: Статистика нагрузки
            """
            df = self.get_all_projects()
            if df.empty:
                return {}
            
            # Парсим исполнителей
            executor_projects = {}
            
            for _, row in df.iterrows():
                executors = str(row['Исполнители'])
                if pd.notna(executors) and executors != 'nan':
                    # Разделяем исполнителей по запятым
                    names = [name.strip() for name in executors.split(',')]
                    for name in names:
                        if name and not name.startswith('[') and not name.startswith('#'):
                            if name not in executor_projects:
                                executor_projects[name] = []
                            executor_projects[name].append({
                                'name': row['Название'],
                                'status': row['Статус'],
                                'complexity': row['Сложность'] if pd.notna(row['Сложность']) else 0
                            })
            
            # Подсчитываем статистику
            workload_stats = {}
            for executor, projects in executor_projects.items():
                workload_stats[executor] = {
                    'total_projects': len(projects),
                    'active_projects': len([p for p in projects if p['status'] not in ['КП Согласовано', 'Отложенная']]),
                    'avg_complexity': sum([p['complexity'] for p in projects if isinstance(p['complexity'], (int, float))]) / len(projects) if projects else 0,
                    'projects': projects
                }
            
            return workload_stats
        
        def analyze_financial_metrics(self) -> Dict[str, Any]:
            """
            Анализирует финансовые показатели
            
            Returns:
                Dict: Финансовая статистика
            """
            df = self.get_all_projects()
            if df.empty:
                return {}
            
            # Преобразуем суммы сделок в числа
            def parse_amount(amount):
                if pd.isna(amount):
                    return 0
                
                amount_str = str(amount).replace(' ', '').replace(',', '')
                # Ищем числа в строке
                numbers = re.findall(r'\d+\.?\d*', amount_str)
                if numbers:
                    return float(numbers[0])
                return 0
            
            df['deal_amount_numeric'] = df['Сумма сделки'].apply(parse_amount)
            
            # Группировка по статусам
            status_finance = df.groupby('Статус')['deal_amount_numeric'].agg(['sum', 'count', 'mean']).round(2)
            
            # Общая статистика
            total_amount = df['deal_amount_numeric'].sum()
            avg_deal = df['deal_amount_numeric'].mean()
            
            # Топ проекты по сумме
            top_projects = df.nlargest(5, 'deal_amount_numeric')[['Название', 'Сумма сделки', 'Статус']]
            
            return {
                'total_amount': total_amount,
                'average_deal': avg_deal,
                'projects_count': len(df),
                'status_breakdown': status_finance.to_dict(),
                'top_projects': top_projects.to_dict('records')
            }
        
        def generate_status_report(self) -> str:
            """
            Генерирует отчёт по статусам проектов
            
            Returns:
                str: Отчёт в текстовом формате
            """
            df = self.get_all_projects()
            if df.empty:
                return "❌ Нет данных для отчёта"
            
            report = []
            report.append("📊 ОТЧЁТ ПО СТАТУСАМ ПРОЕКТОВ")
            report.append("=" * 50)
            report.append(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"📈 Всего проектов: {len(df)}")
            report.append("")
            
            # Статистика по статусам
            status_counts = df['Статус'].value_counts()
            report.append("🔍 Распределение по статусам:")
            for status, count in status_counts.items():
                percentage = (count / len(df)) * 100
                report.append(f"   • {status}: {count} ({percentage:.1f}%)")
            
            report.append("")
            
            # Финансовые показатели
            finance_stats = self.analyze_financial_metrics()
            if finance_stats:
                report.append("💰 Финансовые показатели:")
                report.append(f"   • Общая сумма: {finance_stats['total_amount']:,.0f} руб.")
                report.append(f"   • Средняя сделка: {finance_stats['average_deal']:,.0f} руб.")
                report.append("")
            
            # Топ исполнители
            workload = self.analyze_workload()
            if workload:
                report.append("👥 Топ-5 исполнителей по количеству проектов:")
                sorted_executors = sorted(workload.items(), 
                                        key=lambda x: x[1]['active_projects'], 
                                        reverse=True)[:5]
                
                for executor, stats in sorted_executors:
                    report.append(f"   • {executor}: {stats['active_projects']} активных проектов")
            
            return "\n".join(report)
        
        def find_overdue_projects(self, days_threshold: int = 30) -> pd.DataFrame:
            """
            Находит просроченные проекты
            
            Args:
                days_threshold: Количество дней для определения просрочки
                
            Returns:
                pd.DataFrame: Просроченные проекты
            """
            df = self.get_all_projects()
            if df.empty:
                return df
            
            # Фильтруем активные проекты
            active_statuses = ['КП Согласование', 'Поиск и расчет товара', 'Коммерческое предложение']
            active_projects = df[df['Статус'].isin(active_statuses)]
            
            # Здесь можно добавить логику анализа дат создания
            # Пока возвращаем проекты старше threshold дней из всех активных
            
            return active_projects.head(10)  # Заглушка для примера
        
        def create_dashboard(self) -> bool:
            """
            Создаёт дашборд с аналитикой
            
            Returns:
                bool: True если успешно
            """
            try:
                # Получаем данные для дашборда
                df = self.get_all_projects()
                if df.empty:
                    print("❌ Нет данных для создания дашборда")
                    return False
                
                # Создаём лист Dashboard
                try:
                    self.connector.create_sheet(self.spreadsheet_id, "Dashboard")
                except:
                    pass  # Лист уже существует
                
                # Подготавливаем данные для дашборда
                status_counts = df['Статус'].value_counts()
                finance_stats = self.analyze_financial_metrics()
                workload_stats = self.analyze_workload()
                
                dashboard_data = [
                    ["📊 ДАШБОРД ПРОЕКТОВ", f"Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
                    ["", ""],
                    ["📈 ОБЩАЯ СТАТИСТИКА", ""],
                    ["Всего проектов", str(len(df))],
                    ["Общая сумма сделок", f"{finance_stats.get('total_amount', 0):,.0f} руб."],
                    ["Средняя сделка", f"{finance_stats.get('average_deal', 0):,.0f} руб."],
                    ["", ""],
                    ["🔍 СТАТУСЫ", "КОЛИЧЕСТВО"],
                ]
                
                # Добавляем статусы
                for status, count in status_counts.items():
                    dashboard_data.append([status, str(count)])
                
                dashboard_data.extend([
                    ["", ""],
                    ["👥 ТОП ИСПОЛНИТЕЛИ", "АКТИВНЫХ ПРОЕКТОВ"],
                ])
                
                # Добавляем топ исполнителей
                if workload_stats:
                    sorted_executors = sorted(workload_stats.items(), 
                                            key=lambda x: x[1]['active_projects'], 
                                            reverse=True)[:5]
                    
                    for executor, stats in sorted_executors:
                        dashboard_data.append([executor, str(stats['active_projects'])])
                
                # Записываем дашборд
                success = self.connector.write_range(
                    self.spreadsheet_id,
                    "Dashboard!A1",
                    dashboard_data
                )
                
                if success:
                    print("✅ Дашборд создан успешно!")
                    return True
                else:
                    print("❌ Ошибка создания дашборда")
                    return False
                    
            except Exception as e:
                print(f"❌ Ошибка создания дашборда: {e}")
                return False
    
    def main():
        """Главная функция для демонстрации работы с таблицей приоритетов"""
        print("🎯 МЕНЕДЖЕР ТАБЛИЦЫ ПРИОРИТЕТОВ")
        print("=" * 60)
        
        # Создаём менеджер
        manager = PrioritiesManager()
        
        # Проверяем аутентификацию
        if not manager.authenticate():
            print("❌ Ошибка аутентификации")
            print("💡 Убедитесь, что файл credentials/quickstart-1591698112539-676a9e339335.json существует")
            print("💡 И что Service Account имеет доступ к таблице")
            return
        
        print("✅ Подключение установлено")
        
        try:
            # Получаем все проекты
            print("\n📊 Загрузка данных...")
            projects = manager.get_all_projects()
            
            if projects.empty:
                print("❌ Нет доступных данных в таблице")
                return
            
            print(f"✅ Загружено {len(projects)} проектов")
            
            # Генерируем отчёт
            print("\n📋 Генерация отчёта...")
            report = manager.generate_status_report()
            print(report)
            
            # Анализируем нагрузку
            print("\n👥 Анализ нагрузки исполнителей...")
            workload = manager.analyze_workload()
            
            if workload:
                print("📊 Топ-3 загруженных исполнителя:")
                sorted_workload = sorted(workload.items(), 
                                       key=lambda x: x[1]['active_projects'], 
                                       reverse=True)[:3]
                
                for executor, stats in sorted_workload:
                    print(f"   • {executor}: {stats['active_projects']} активных проектов")
            
            # Создаём дашборд
            print("\n📊 Создание дашборда...")
            dashboard_success = manager.create_dashboard()
            
            if dashboard_success:
                print(f"🎉 Анализ завершён!")
                print(f"📊 Откройте таблицу: https://docs.google.com/spreadsheets/d/{manager.spreadsheet_id}")
                print("📋 Дашборд доступен на листе 'Dashboard'")
            
        except Exception as e:
            print(f"❌ Ошибка выполнения: {e}")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Убедитесь, что установлены все зависимости")
except Exception as e:
    print(f"❌ Ошибка: {e}")
