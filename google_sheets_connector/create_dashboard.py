"""
Создание дашборда для таблицы приоритетов
"""

from connector import GoogleSheetsConnector
import pandas as pd
from datetime import datetime
import re

def create_comprehensive_dashboard():
    """Создает полный дашборд для таблицы приоритетов"""
    print("📊 СОЗДАНИЕ ДАШБОРДА ТАБЛИЦЫ ПРИОРИТЕТОВ")
    print("=" * 60)
    
    # Подключение
    sheets = GoogleSheetsConnector()
    if not sheets.authenticate_service_account("credentials/quickstart-1591698112539-676a9e339335.json"):
        print("❌ Ошибка аутентификации")
        return
    
    spreadsheet_id = "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
    
    try:
        # Читаем все данные
        print("📖 Загрузка данных...")
        df = sheets.read_to_dataframe(spreadsheet_id, "Лист1!A1:M600", header_row=True)
        
        # Очищаем данные
        df = df.dropna(subset=['Название'])  # Удаляем строки без названия
        df = df[df['Название'].str.strip() != '']  # Удаляем пустые названия
        
        print(f"✅ Загружено {len(df)} проектов")
        
        # Анализируем данные
        print("\n📊 Создание аналитики...")
        
        # 1. Статистика по статусам
        status_stats = df['Статус'].value_counts()
        
        # 2. Анализ исполнителей
        executor_analysis = analyze_executors(df)
        
        # 3. Финансовая аналитика
        financial_stats = analyze_finances(df)
        
        # 4. Анализ грейдов клиентов
        grade_stats = df['Грейд клиента'].value_counts().sort_index()
        
        # Создаем дашборд
        print("🎨 Создание дашборда...")
        
        # Создаем новый лист для дашборда
        try:
            sheets.create_sheet(spreadsheet_id, "📊 Dashboard")
        except:
            pass  # Лист уже существует
        
        # Подготавливаем данные для дашборда
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        dashboard_data = [
            ["📊 ДАШБОРД ТАБЛИЦЫ ПРИОРИТЕТОВ", f"Обновлено: {current_time}"],
            ["", ""],
            ["🎯 ОБЩАЯ СТАТИСТИКА", ""],
            ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""],
            ["Всего активных проектов", str(len(df))],
            ["Общая сумма сделок", f"{financial_stats['total']:,.0f} руб." if financial_stats['total'] > 0 else "Не указано"],
            ["Средняя сумма сделки", f"{financial_stats['average']:,.0f} руб." if financial_stats['average'] > 0 else "Не указано"],
            ["Уникальных исполнителей", str(len(executor_analysis))],
            ["", ""],
            ["📈 СТАТУСЫ ПРОЕКТОВ", "КОЛИЧЕСТВО"],
            ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "━━━━━━━━━━━"],
        ]
        
        # Добавляем статусы
        for status, count in status_stats.head(10).items():
            percentage = (count / len(df)) * 100
            dashboard_data.append([status, f"{count} ({percentage:.1f}%)"])
        
        dashboard_data.extend([
            ["", ""],
            ["👥 ТОП ИСПОЛНИТЕЛИ", "АКТИВНЫХ ПРОЕКТОВ"],
            ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "━━━━━━━━━━━━━━━━━━"],
        ])
        
        # Добавляем топ исполнителей
        sorted_executors = sorted(executor_analysis.items(), key=lambda x: x[1], reverse=True)[:10]
        for executor, count in sorted_executors:
            dashboard_data.append([executor, str(count)])
        
        dashboard_data.extend([
            ["", ""],
            ["⭐ ГРЕЙДЫ КЛИЕНТОВ", "КОЛИЧЕСТВО"],
            ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "━━━━━━━━━━━"],
        ])
        
        # Добавляем грейды
        for grade, count in grade_stats.items():
            if pd.notna(grade):
                dashboard_data.append([f"Грейд {grade}", str(count)])
        
        dashboard_data.extend([
            ["", ""],
            ["💰 ФИНАНСОВЫЕ ПОКАЗАТЕЛИ", ""],
            ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""],
            ["Проектов с указанной суммой", str(financial_stats['projects_with_amount'])],
            ["Максимальная сделка", f"{financial_stats['max']:,.0f} руб." if financial_stats['max'] > 0 else "Не указано"],
            ["Минимальная сделка", f"{financial_stats['min']:,.0f} руб." if financial_stats['min'] > 0 else "Не указано"],
            ["", ""],
            ["🚀 РЕКОМЕНДАЦИИ", ""],
            ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""],
            ["1. Проекты в статусе 'Клиент принимает решение'", f"{status_stats.get('Клиент принимает решение', 0)} требуют внимания"],
            ["2. Загруженность исполнителей", f"У {sorted_executors[0][0]} больше всего проектов: {sorted_executors[0][1]}" if sorted_executors else ""],
            ["3. Финансовый фокус", "Сосредоточиться на крупных сделках"],
            ["4. Процессы", "Оптимизировать workflow для быстрого закрытия"],
        ])
        
        # Записываем дашборд
        success = sheets.write_range(spreadsheet_id, "📊 Dashboard!A1", dashboard_data)
        
        if success:
            print("✅ Дашборд создан успешно!")
            
            # Создаем детальную аналитику
            create_detailed_analytics(sheets, spreadsheet_id, df, status_stats, executor_analysis)
            
            print(f"\n🎉 ДАШБОРД ГОТОВ!")
            print(f"📊 Откройте таблицу: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            print("📋 Листы:")
            print("   • 📊 Dashboard - основная сводка")
            print("   • 📈 Analytics - детальная аналитика")
            
        else:
            print("❌ Ошибка создания дашборда")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def analyze_executors(df):
    """Анализирует нагрузку исполнителей"""
    executor_counts = {}
    
    for _, row in df.iterrows():
        executors = str(row['Исполнители'])
        if pd.notna(executors) and executors != 'nan':
            # Разделяем исполнителей по запятым
            names = [name.strip() for name in executors.split(',')]
            for name in names:
                # Очищаем от специальных символов
                clean_name = re.sub(r'[\[\]#]', '', name).strip()
                if clean_name and len(clean_name) > 2:
                    executor_counts[clean_name] = executor_counts.get(clean_name, 0) + 1
    
    return executor_counts

def analyze_finances(df):
    """Анализирует финансовые показатели"""
    amounts = []
    
    for _, row in df.iterrows():
        amount_str = str(row['Сумма сделки'])
        if pd.notna(amount_str) and amount_str != 'nan':
            # Извлекаем числа из строки
            numbers = re.findall(r'\d+\.?\d*', amount_str.replace(' ', '').replace(',', ''))
            if numbers:
                try:
                    amount = float(numbers[0])
                    if amount > 0:
                        amounts.append(amount)
                except:
                    pass
    
    if amounts:
        return {
            'total': sum(amounts),
            'average': sum(amounts) / len(amounts),
            'max': max(amounts),
            'min': min(amounts),
            'projects_with_amount': len(amounts)
        }
    else:
        return {
            'total': 0,
            'average': 0,
            'max': 0,
            'min': 0,
            'projects_with_amount': 0
        }

def create_detailed_analytics(sheets, spreadsheet_id, df, status_stats, executor_analysis):
    """Создает детальную аналитику"""
    print("📈 Создание детальной аналитики...")
    
    # Создаем лист аналитики
    try:
        sheets.create_sheet(spreadsheet_id, "📈 Analytics")
    except:
        pass
    
    # Подготавливаем данные аналитики
    analytics_data = [
        ["📈 ДЕТАЛЬНАЯ АНАЛИТИКА", f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
        ["", ""],
        ["🔍 ПОЛНАЯ СТАТИСТИКА ПО СТАТУСАМ", "", ""],
        ["Статус", "Количество", "Процент"],
        ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "━━━━━━━━━━━", "━━━━━━━━━"],
    ]
    
    for status, count in status_stats.items():
        percentage = (count / len(df)) * 100
        analytics_data.append([status, str(count), f"{percentage:.1f}%"])
    
    analytics_data.extend([
        ["", "", ""],
        ["👥 ПОЛНАЯ СТАТИСТИКА ПО ИСПОЛНИТЕЛЯМ", "", ""],
        ["Исполнитель", "Проектов", "Нагрузка %"],
        ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "━━━━━━━━━━━", "━━━━━━━━━"],
    ])
    
    total_assignments = sum(executor_analysis.values())
    for executor, count in sorted(executor_analysis.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_assignments) * 100 if total_assignments > 0 else 0
        analytics_data.append([executor, str(count), f"{percentage:.1f}%"])
    
    # Записываем аналитику
    sheets.write_range(spreadsheet_id, "📈 Analytics!A1", analytics_data)
    print("✅ Детальная аналитика создана")

def main():
    create_comprehensive_dashboard()

if __name__ == "__main__":
    main()
