"""
Анализатор приоритетов проектов с финансовыми показателями и участниками
"""

from connector import GoogleSheetsConnector
import pandas as pd
import re
from datetime import datetime
from collections import defaultdict

class PriorityAnalyzer:
    """Класс для анализа приоритетов проектов"""
    
    def __init__(self, spreadsheet_id="1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"):
        self.connector = GoogleSheetsConnector()
        self.spreadsheet_id = spreadsheet_id
        self.df = None
    
    def authenticate(self, credentials_file="credentials/quickstart-1591698112539-676a9e339335.json"):
        """Аутентификация"""
        return self.connector.authenticate_service_account(credentials_file)
    
    def load_data(self):
        """Загружает данные из таблицы"""
        print("📊 Загрузка данных из таблицы приоритетов...")
        
        try:
            # Читаем все данные
            self.df = self.connector.read_to_dataframe(
                self.spreadsheet_id, 
                "Лист1!A1:M600", 
                header_row=True
            )
            
            # Очищаем данные
            self.df = self.df.dropna(subset=['Название'])
            self.df = self.df[self.df['Название'].str.strip() != '']
            
            print(f"✅ Загружено {len(self.df)} проектов")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return False
    
    def parse_amount(self, amount_str):
        """Парсит сумму из строки"""
        if pd.isna(amount_str) or str(amount_str).strip() == '':
            return 0
        
        # Удаляем пробелы и заменяем запятые
        cleaned = str(amount_str).replace(' ', '').replace(',', '')
        
        # Ищем числа в строке
        numbers = re.findall(r'\d+\.?\d*', cleaned)
        if numbers:
            try:
                return float(numbers[0])
            except:
                return 0
        return 0
    
    def parse_executors(self, executors_str):
        """Парсит список исполнителей"""
        if pd.isna(executors_str):
            return []
        
        executors_str = str(executors_str)
        
        # Разделяем по запятым
        names = [name.strip() for name in executors_str.split(',')]
        
        # Очищаем от специальных символов и фильтруем
        clean_names = []
        for name in names:
            # Удаляем квадратные скобки, # и другие символы
            clean_name = re.sub(r'[\[\]#]', '', name).strip()
            
            # Фильтруем пустые и слишком короткие имена
            if clean_name and len(clean_name) > 2 and not clean_name.startswith('###'):
                clean_names.append(clean_name)
        
        return clean_names
    
    def analyze_priorities(self):
        """Анализирует приоритеты проектов"""
        print("\n🎯 Анализ приоритетов...")
        
        if self.df is None:
            print("❌ Данные не загружены")
            return None
        
        # Добавляем парсированные данные
        self.df['parsed_amount'] = self.df['Сумма сделки'].apply(self.parse_amount)
        self.df['parsed_executors'] = self.df['Исполнители'].apply(self.parse_executors)
        
        # Анализ по приоритетам
        priority_analysis = {}
        
        # Группируем по приоритетам
        for priority in self.df['Приоритет'].unique():
            if pd.isna(priority):
                priority = "Не указан"
            
            priority_projects = self.df[self.df['Приоритет'] == priority] if priority != "Не указан" else self.df[self.df['Приоритет'].isna()]
            
            # Финансовые показатели
            total_amount = priority_projects['parsed_amount'].sum()
            avg_amount = priority_projects['parsed_amount'].mean() if len(priority_projects) > 0 else 0
            projects_with_amount = len(priority_projects[priority_projects['parsed_amount'] > 0])
            
            # Собираем всех участников
            all_executors = []
            for executors_list in priority_projects['parsed_executors']:
                all_executors.extend(executors_list)
            
            # Подсчитываем участников
            executor_counts = defaultdict(int)
            for executor in all_executors:
                executor_counts[executor] += 1
            
            # Топ участники
            top_executors = sorted(executor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Статусы проектов в приоритете
            status_counts = priority_projects['Статус'].value_counts()
            
            priority_analysis[str(priority)] = {
                'projects_count': len(priority_projects),
                'total_amount': total_amount,
                'average_amount': avg_amount,
                'projects_with_amount': projects_with_amount,
                'top_executors': top_executors,
                'unique_executors': len(executor_counts),
                'status_breakdown': status_counts.to_dict(),
                'projects': priority_projects[['Название', 'Статус', 'Сумма сделки', 'Исполнители']].head(3).to_dict('records')
            }
        
        return priority_analysis
    
    def create_priority_dashboard(self):
        """Создает дашборд приоритетов"""
        print("\n📊 Создание дашборда приоритетов...")
        
        # Анализируем приоритеты
        analysis = self.analyze_priorities()
        
        if not analysis:
            return False
        
        # Создаем лист для дашборда приоритетов
        try:
            self.connector.create_sheet(self.spreadsheet_id, "🎯 Priority Dashboard")
        except:
            pass  # Лист уже существует
        
        # Подготавливаем данные для дашборда
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        dashboard_data = [
            ["🎯 ДАШБОРД ПРИОРИТЕТОВ ПРОЕКТОВ", f"Обновлено: {current_time}"],
            ["", ""],
            ["📊 АНАЛИЗ ПО ПРИОРИТЕТАМ", ""],
            ["═══════════════════════════════════════════════════════════════════", ""],
        ]
        
        # Сортируем приоритеты (числовые сначала, затем остальные)
        sorted_priorities = []
        other_priorities = []
        
        for priority in analysis.keys():
            try:
                float(priority)
                sorted_priorities.append(priority)
            except:
                other_priorities.append(priority)
        
        sorted_priorities.sort(key=lambda x: float(x))
        all_priorities = sorted_priorities + sorted(other_priorities)
        
        # Добавляем данные по каждому приоритету
        for priority in all_priorities:
            data = analysis[priority]
            
            dashboard_data.extend([
                [f"🎯 ПРИОРИТЕТ: {priority}", ""],
                ["─────────────────────────────────────────────────────────────────", ""],
                ["📈 Общие показатели:", ""],
                ["  • Количество проектов", str(data['projects_count'])],
                ["  • Общая сумма сделок", f"{data['total_amount']:,.0f} руб." if data['total_amount'] > 0 else "Не указано"],
                ["  • Средняя сумма сделки", f"{data['average_amount']:,.0f} руб." if data['average_amount'] > 0 else "Не указано"],
                ["  • Проектов с суммой", str(data['projects_with_amount'])],
                ["  • Уникальных участников", str(data['unique_executors'])],
                ["", ""],
                ["👥 Топ участники:", "Проектов"],
            ])
            
            # Добавляем топ участников
            for executor, count in data['top_executors']:
                dashboard_data.append([f"  • {executor}", str(count)])
            
            if not data['top_executors']:
                dashboard_data.append(["  • Участники не указаны", "-"])
            
            dashboard_data.extend([
                ["", ""],
                ["📊 Статусы проектов:", "Количество"],
            ])
            
            # Добавляем статусы
            for status, count in data['status_breakdown'].items():
                dashboard_data.append([f"  • {status}", str(count)])
            
            dashboard_data.extend([
                ["", ""],
                ["📝 Примеры проектов:", ""],
            ])
            
            # Добавляем примеры проектов
            for i, project in enumerate(data['projects'], 1):
                project_name = project['Название'][:60] + "..." if len(project['Название']) > 60 else project['Название']
                dashboard_data.append([f"  {i}. {project_name}", f"({project['Статус']})"])
            
            dashboard_data.extend([
                ["", ""],
                ["", ""],
            ])
        
        # Добавляем общую сводку
        total_projects = sum(data['projects_count'] for data in analysis.values())
        total_amount = sum(data['total_amount'] for data in analysis.values())
        all_executors = set()
        for data in analysis.values():
            for executor, _ in data['top_executors']:
                all_executors.add(executor)
        
        dashboard_data.extend([
            ["🎊 ОБЩАЯ СВОДКА", ""],
            ["═══════════════════════════════════════════════════════════════════", ""],
            ["📊 Итоговые показатели:", ""],
            ["  • Всего проектов", str(total_projects)],
            ["  • Общая сумма всех проектов", f"{total_amount:,.0f} руб." if total_amount > 0 else "Не указано"],
            ["  • Приоритетов в системе", str(len(analysis))],
            ["  • Всего участников", str(len(all_executors))],
            ["", ""],
            ["💡 Рекомендации:", ""],
            ["  • Сосредоточиться на проектах с высоким приоритетом", ""],
            ["  • Балансировать нагрузку между участниками", ""],
            ["  • Отслеживать проекты без указанного приоритета", ""],
            ["  • Регулярно обновлять финансовые данные", ""],
        ])
        
        # Записываем дашборд
        success = self.connector.write_range(
            self.spreadsheet_id,
            "🎯 Priority Dashboard!A1",
            dashboard_data
        )
        
        if success:
            print("✅ Дашборд приоритетов создан успешно!")
            return True
        else:
            print("❌ Ошибка создания дашборда")
            return False
    
    def create_financial_priority_summary(self):
        """Создает финансовую сводку по приоритетам"""
        print("\n💰 Создание финансовой сводки...")
        
        analysis = self.analyze_priorities()
        if not analysis:
            return False
        
        try:
            self.connector.create_sheet(self.spreadsheet_id, "💰 Financial Priority")
        except:
            pass
        
        # Подготавливаем финансовые данные
        financial_data = [
            ["💰 ФИНАНСОВАЯ СВОДКА ПО ПРИОРИТЕТАМ", f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            ["", ""],
            ["Приоритет", "Проектов", "Общая сумма (руб.)", "Средняя сумма (руб.)", "Топ участник", "Проектов у участника"],
            ["───────────", "─────────", "──────────────────", "────────────────────", "─────────────", "──────────────────"],
        ]
        
        # Сортируем по общей сумме
        sorted_analysis = sorted(analysis.items(), key=lambda x: x[1]['total_amount'], reverse=True)
        
        for priority, data in sorted_analysis:
            top_executor = data['top_executors'][0] if data['top_executors'] else ("Не указан", 0)
            
            financial_data.append([
                str(priority),
                str(data['projects_count']),
                f"{data['total_amount']:,.0f}" if data['total_amount'] > 0 else "0",
                f"{data['average_amount']:,.0f}" if data['average_amount'] > 0 else "0",
                top_executor[0],
                str(top_executor[1])
            ])
        
        # Записываем финансовую сводку
        success = self.connector.write_range(
            self.spreadsheet_id,
            "💰 Financial Priority!A1",
            financial_data
        )
        
        if success:
            print("✅ Финансовая сводка создана!")
        
        return success

def main():
    """Главная функция анализа приоритетов"""
    print("🎯 АНАЛИЗАТОР ПРИОРИТЕТОВ ПРОЕКТОВ")
    print("=" * 60)
    
    # Создаем анализатор
    analyzer = PriorityAnalyzer()
    
    # Аутентификация
    if not analyzer.authenticate():
        print("❌ Ошибка аутентификации")
        return
    
    print("✅ Аутентификация успешна")
    
    # Загружаем данные
    if not analyzer.load_data():
        print("❌ Ошибка загрузки данных")
        return
    
    # Анализируем приоритеты
    analysis = analyzer.analyze_priorities()
    
    if analysis:
        print("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print("-" * 40)
        
        for priority, data in analysis.items():
            print(f"\n🎯 Приоритет {priority}:")
            print(f"   • Проектов: {data['projects_count']}")
            print(f"   • Сумма: {data['total_amount']:,.0f} руб.")
            print(f"   • Участников: {data['unique_executors']}")
            if data['top_executors']:
                print(f"   • Топ участник: {data['top_executors'][0][0]} ({data['top_executors'][0][1]} проектов)")
    
    # Создаем дашборды
    dashboard_success = analyzer.create_priority_dashboard()
    financial_success = analyzer.create_financial_priority_summary()
    
    if dashboard_success and financial_success:
        print(f"\n🎉 АНАЛИЗ ЗАВЕРШЕН!")
        print(f"📊 Откройте таблицу: https://docs.google.com/spreadsheets/d/{analyzer.spreadsheet_id}")
        print("📋 Новые листы:")
        print("   • 🎯 Priority Dashboard - детальный анализ приоритетов")
        print("   • 💰 Financial Priority - финансовая сводка")

if __name__ == "__main__":
    main()
