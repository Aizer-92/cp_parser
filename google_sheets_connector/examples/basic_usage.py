"""
Базовые примеры использования Google Sheets Connector
"""

import sys
import os
# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connector import GoogleSheetsConnector, save_example_config
from auth import save_example_service_account
import pandas as pd
from datetime import datetime

def setup_credentials():
    """Настройка credentials для первого запуска"""
    print("🔧 Настройка credentials...")
    
    # Создаем пример Service Account файла
    credentials_dir = "credentials"
    os.makedirs(credentials_dir, exist_ok=True)
    
    service_account_example = os.path.join(credentials_dir, "service_account_example.json")
    save_example_service_account(service_account_example)
    
    # Создаем пример конфигурации
    save_example_config()
    
    print("\n📋 Следующие шаги:")
    print("1. Перейдите в Google Cloud Console")
    print("2. Создайте Service Account и скачайте JSON ключ")
    print("3. Замените содержимое service_account_example.json на реальные данные")
    print("4. Переименуйте файл в quickstart-1591698112539-676a9e339335.json")
    print("5. Обновите config.json с ID ваших таблиц")

def basic_reading_example():
    """Пример чтения данных из таблицы"""
    print("\n📖 Пример чтения данных")
    
    # Инициализация коннектора
    sheets = GoogleSheetsConnector()
    
    # Аутентификация (замените на путь к вашему файлу)
    service_account_file = "credentials/quickstart-1591698112539-676a9e339335.json"
    
    if not sheets.authenticate_service_account(service_account_file):
        print("❌ Ошибка аутентификации. Проверьте файл с credentials.")
        return
    
    # ID таблицы для примера (замените на ваш)
    spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    
    try:
        # Получаем информацию о таблице
        info = sheets.get_spreadsheet_info(spreadsheet_id)
        print(f"📊 Таблица: {info['title']}")
        print(f"📋 Листы: {[sheet['title'] for sheet in info['sheets']]}")
        
        # Читаем данные из диапазона
        data = sheets.read_range(spreadsheet_id, "Sheet1!A1:C10")
        print(f"📈 Прочитано {len(data)} строк:")
        for i, row in enumerate(data[:3]):  # Показываем первые 3 строки
            print(f"  Строка {i+1}: {row}")
        
        # Читаем в DataFrame
        df = sheets.read_to_dataframe(spreadsheet_id, "Sheet1!A1:C10")
        print(f"📊 DataFrame shape: {df.shape}")
        print(df.head())
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def basic_writing_example():
    """Пример записи данных в таблицу"""
    print("\n✍️ Пример записи данных")
    
    sheets = GoogleSheetsConnector()
    
    # Аутентификация
    service_account_file = "credentials/service_account.json"
    if not sheets.authenticate_service_account(service_account_file):
        print("❌ Ошибка аутентификации")
        return
    
    # ID таблицы (замените на ваш)
    spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    
    try:
        # Подготавливаем данные для записи
        data = [
            ["Дата", "Событие", "Значение"],
            [datetime.now().strftime("%Y-%m-%d"), "Тест записи", "100"],
            [datetime.now().strftime("%Y-%m-%d"), "Второй тест", "200"]
        ]
        
        # Записываем данные
        success = sheets.write_range(spreadsheet_id, "TestSheet!A1", data)
        if success:
            print("✅ Данные успешно записаны")
        else:
            print("❌ Ошибка записи данных")
        
        # Пример записи DataFrame
        df = pd.DataFrame({
            'Имя': ['Иван', 'Мария', 'Петр'],
            'Возраст': [25, 30, 35],
            'Город': ['Москва', 'СПб', 'Казань']
        })
        
        success = sheets.write_dataframe(spreadsheet_id, "TestSheet!E1", df)
        if success:
            print("✅ DataFrame успешно записан")
        
        # Добавляем строки в конец
        new_rows = [
            [datetime.now().strftime("%H:%M:%S"), "Добавленная строка", "300"]
        ]
        
        success = sheets.append_rows(spreadsheet_id, "TestSheet!A:C", new_rows)
        if success:
            print("✅ Строки добавлены в конец таблицы")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def sheet_management_example():
    """Пример управления листами"""
    print("\n📋 Пример управления листами")
    
    sheets = GoogleSheetsConnector()
    
    # Аутентификация
    service_account_file = "credentials/service_account.json"
    if not sheets.authenticate_service_account(service_account_file):
        print("❌ Ошибка аутентификации")
        return
    
    spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    
    try:
        # Создаем новый лист
        sheet_name = f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        sheet_id = sheets.create_sheet(spreadsheet_id, sheet_name)
        
        if sheet_id:
            print(f"✅ Создан лист '{sheet_name}' с ID {sheet_id}")
            
            # Записываем данные в новый лист
            headers = ["Колонка A", "Колонка B", "Колонка C"]
            test_data = [
                headers,
                ["Значение 1", "Значение 2", "Значение 3"],
                ["Тест 1", "Тест 2", "Тест 3"]
            ]
            
            success = sheets.write_range(spreadsheet_id, f"{sheet_name}!A1", test_data)
            if success:
                print(f"✅ Данные записаны в лист '{sheet_name}'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def config_example():
    """Пример работы с конфигурацией"""
    print("\n⚙️ Пример работы с конфигурацией")
    
    sheets = GoogleSheetsConnector()
    
    # Получаем ID таблицы из конфигурации
    health_id = sheets.get_config_spreadsheet('health_tracking')
    finance_id = sheets.get_config_spreadsheet('finance_tracking')
    
    print(f"🏥 Health tracking table ID: {health_id}")
    print(f"💰 Finance tracking table ID: {finance_id}")
    
    # Обновляем конфигурацию
    new_config = {
        'my_personal_table': '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    }
    
    sheets.save_config(new_config)
    print("✅ Конфигурация обновлена")

def main():
    """Главная функция с примерами"""
    print("🚀 Google Sheets Connector - Примеры использования")
    print("=" * 50)
    
    # Проверяем наличие необходимых файлов
    if not os.path.exists("credentials/quickstart-1591698112539-676a9e339335.json"):
        setup_credentials()
        print("\n⚠️ Настройте credentials и запустите скрипт снова")
        return
    
    try:
        # Запускаем примеры
        basic_reading_example()
        basic_writing_example()
        sheet_management_example()
        config_example()
        
        print("\n🎉 Все примеры выполнены!")
        
    except KeyboardInterrupt:
        print("\n👋 Выполнение прервано пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
