"""
Анализ структуры Google Sheets таблицы на основе предоставленных данных
"""

import pandas as pd
from datetime import datetime

def analyze_table_structure():
    """Анализирует структуру таблицы на основе веб-данных"""
    print("🔍 Анализ структуры Google Sheets таблицы")
    print("=" * 60)
    
    # ID таблицы из URL
    table_id = "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
    sheet_id = "1074629753"  # Из gid в URL
    
    print(f"🆔 ID таблицы: {table_id}")
    print(f"📄 ID листа: {sheet_id}")
    print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{table_id}/edit#gid={sheet_id}")
    
    # Анализ структуры на основе предоставленных данных
    print("\n📊 СТРУКТУРА ТАБЛИЦЫ:")
    print("-" * 40)
    
    # Заголовки колонок (из предоставленных данных)
    headers = [
        "A: Название",
        "B: Статус", 
        "C: Грейд клиента",
        "D: % заказа",
        "E: Сроки",
        "F: Сложность",
        "G: Сумма сделки",
        "H: Сумма просчета", 
        "I: Постановщик",
        "J: Исполнители",
        "K: Дата создания",
        "L: Процесс",
        "M: Приоритет"
    ]
    
    print("📋 Колонки таблицы:")
    for header in headers:
        print(f"   {header}")
    
    print(f"\n📈 Всего колонок: {len(headers)}")
    
    # Анализ типов данных
    print("\n🔍 ТИПЫ ДАННЫХ:")
    print("-" * 40)
    
    data_types = {
        "Название": "Текст (описание проектов/заказов)",
        "Статус": "Категория (КП Согласование, Поиск и расчет товара, и т.д.)",
        "Грейд клиента": "Число (2-5, рейтинг клиента)",
        "% заказа": "Число (процент выполнения)",
        "Сроки": "Число/Дата (временные рамки)",
        "Сложность": "Число (уровень сложности 1-8)",
        "Сумма сделки": "Число (финансовая сумма)",
        "Сумма просчета": "Текст (имена ответственных)",
        "Постановщик": "Текст (имя постановщика)",
        "Исполнители": "Текст (список исполнителей)",
        "Дата создания": "Дата (когда создана запись)",
        "Процесс": "Категория (тип процесса A/B/C/D)",
        "Приоритет": "Число (числовой приоритет)"
    }
    
    for col, data_type in data_types.items():
        print(f"   {col}: {data_type}")
    
    # Анализ статусов
    print("\n📊 СТАТУСЫ ПРОЕКТОВ:")
    print("-" * 40)
    
    statuses = [
        "КП Согласование",
        "Поиск и расчет товара", 
        "Коммерческое предложение",
        "Новая",
        "Клиент принимает решение",
        "КП Согласовано",
        "Отложенная"
    ]
    
    for i, status in enumerate(statuses, 1):
        print(f"   {i}. {status}")
    
    # Анализ данных
    print("\n📈 АНАЛИЗ ДАННЫХ:")
    print("-" * 40)
    
    print("🎯 Основные метрики:")
    print("   • Грейд клиентов: от 2 до 5")
    print("   • Процент заказа: от 1% до 209%")
    print("   • Сложность: от 1 до 8")
    print("   • Суммы сделок: от 12,321 до 36,000,000 руб.")
    
    print("\n🔄 Процессы:")
    processes = ["A", "B", "C", "D"]
    for process in processes:
        print(f"   • Процесс {process}")
    
    print("\n👥 Роли:")
    print("   • Постановщики: Полина Коник, Александра, Ирина Вегера и др.")
    print("   • Исполнители: Георгий Побединский, Светлана Аспидова и др.")
    
    return {
        'table_id': table_id,
        'sheet_id': sheet_id,
        'headers': headers,
        'data_types': data_types,
        'statuses': statuses,
        'total_columns': len(headers)
    }

def suggest_automations():
    """Предлагает автоматизации для таблицы"""
    print("\n🤖 ПРЕДЛАГАЕМЫЕ АВТОМАТИЗАЦИИ:")
    print("=" * 60)
    
    automations = [
        {
            'name': 'Мониторинг просроченных сделок',
            'description': 'Автоматическая проверка сроков и уведомления о просроченных проектах',
            'frequency': 'Ежедневно'
        },
        {
            'name': 'Отчёт по статусам',
            'description': 'Еженедельный отчёт о количестве проектов в каждом статусе',
            'frequency': 'Еженедельно'
        },
        {
            'name': 'Анализ нагрузки исполнителей',
            'description': 'Подсчёт активных проектов для каждого исполнителя',
            'frequency': 'По запросу'
        },
        {
            'name': 'Финансовая аналитика',
            'description': 'Расчёт общих сумм сделок по статусам и исполнителям',
            'frequency': 'Ежемесячно'
        },
        {
            'name': 'Контроль качества данных',
            'description': 'Проверка заполненности обязательных полей',
            'frequency': 'При изменении'
        }
    ]
    
    for i, automation in enumerate(automations, 1):
        print(f"{i}. 🎯 {automation['name']}")
        print(f"   📝 {automation['description']}")
        print(f"   ⏰ Частота: {automation['frequency']}")
        print()

def create_integration_example():
    """Создаёт пример интеграции с таблицей"""
    print("\n💻 ПРИМЕР КОДА ДЛЯ ИНТЕГРАЦИИ:")
    print("=" * 60)
    
    code_example = '''
# Пример работы с таблицей приоритетов
from connector import GoogleSheetsConnector

def work_with_priorities_table():
    """Работа с таблицей приоритетов"""
    
    # Подключение
    sheets = GoogleSheetsConnector()
    sheets.authenticate_service_account('credentials/quickstart-1591698112539-676a9e339335.json')
    
    table_id = "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
    
    # Чтение всех данных
    all_data = sheets.read_to_dataframe(table_id, "Лист1!A:M", header_row=True)
    
    # Анализ статусов
    status_counts = all_data['Статус'].value_counts()
    print("Распределение по статусам:")
    print(status_counts)
    
    # Поиск просроченных проектов
    today = datetime.now()
    # (Логика для проверки сроков)
    
    # Расчёт финансовых показателей
    total_deals = all_data['Сумма сделки'].sum()
    print(f"Общая сумма сделок: {total_deals:,.0f} руб.")
    
    # Анализ нагрузки исполнителей
    # (Парсинг колонки "Исполнители")
    
    return all_data

# Автоматическое обновление статистики
def update_dashboard():
    """Обновляет дашборд с аналитикой"""
    
    data = work_with_priorities_table()
    
    # Создание сводного листа
    summary = {
        'Всего проектов': len(data),
        'В работе': len(data[data['Статус'] != 'КП Согласовано']),
        'Завершено': len(data[data['Статус'] == 'КП Согласовано']),
        'Общая сумма': data['Сумма сделки'].sum()
    }
    
    # Запись сводки в отдельный лист
    sheets.write_range(table_id, "Dashboard!A1", 
                      [list(summary.keys()), list(summary.values())])
'''
    
    print(code_example)

def main():
    """Главная функция анализа"""
    print("🚀 АНАЛИЗ GOOGLE SHEETS ТАБЛИЦЫ")
    print(f"⏰ Время анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Анализируем структуру
    table_info = analyze_table_structure()
    
    # Предлагаем автоматизации
    suggest_automations()
    
    # Показываем пример кода
    create_integration_example()
    
    print("\n✅ ЗАКЛЮЧЕНИЕ:")
    print("=" * 60)
    print("📊 Таблица содержит данные о проектах/сделках с полной информацией:")
    print("   • Названия и статусы проектов")
    print("   • Финансовые показатели") 
    print("   • Ответственные лица")
    print("   • Временные рамки")
    print("   • Метрики качества")
    
    print("\n🔐 ДЛЯ ПОДКЛЮЧЕНИЯ К ТАБЛИЦЕ:")
    print("1. Настройте Service Account в Google Cloud Console")
    print("2. Предоставьте доступ email'у Service Account к таблице")
    print("3. Используйте созданный коннектор для автоматизации")
    
    print(f"\n📋 Добавьте в config.json:")
    print(f'   "priorities_table": "{table_info["table_id"]}"')
    
    print(f"\n🔗 Прямая ссылка: https://docs.google.com/spreadsheets/d/{table_info['table_id']}")

if __name__ == "__main__":
    main()
