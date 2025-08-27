"""
Интерактивное руководство по настройке Google Sheets Connector
"""

import os
import json
import webbrowser
from datetime import datetime

def print_header(title):
    """Красивый заголовок"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Форматирование шага"""
    print(f"\n📋 Шаг {step_num}: {title}")
    print("-" * 40)

def setup_directories():
    """Создание необходимых директорий"""
    directories = ["credentials", "examples", "utils", "temp", "output"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Создана директория: {directory}")
        else:
            print(f"📁 Директория уже существует: {directory}")

def create_google_cloud_project_guide():
    """Руководство по созданию проекта в Google Cloud"""
    print_step(1, "Создание проекта в Google Cloud Console")
    
    print("""
1️⃣ Перейдите в Google Cloud Console:
   https://console.cloud.google.com/

2️⃣ Создайте новый проект:
   - Нажмите на выпадающий список проектов вверху
   - Выберите "New Project"
   - Введите название проекта (например: "my-sheets-connector")
   - Нажмите "Create"

3️⃣ Включите Google Sheets API:
   - Перейдите в "APIs & Services" > "Library"
   - Найдите "Google Sheets API"
   - Нажмите "Enable"

4️⃣ Включите Google Drive API (опционально):
   - Найдите "Google Drive API"
   - Нажмите "Enable"
    """)
    
    open_browser = input("\n🌐 Открыть Google Cloud Console в браузере? (y/n): ").lower()
    if open_browser == 'y':
        webbrowser.open("https://console.cloud.google.com/")

def create_service_account_guide():
    """Руководство по созданию Service Account"""
    print_step(2, "Создание Service Account")
    
    print("""
1️⃣ В Google Cloud Console перейдите в:
   "IAM & Admin" > "Service Accounts"

2️⃣ Создайте Service Account:
   - Нажмите "Create Service Account"
   - Введите имя (например: "sheets-connector-bot")
   - Введите описание
   - Нажмите "Create and Continue"

3️⃣ Назначьте роли (опционально):
   - Можете пропустить этот шаг для простого доступа к таблицам
   - Нажмите "Continue"

4️⃣ Создайте ключ:
   - В списке Service Accounts нажмите на созданный аккаунт
   - Перейдите на вкладку "Keys"
   - Нажмите "Add Key" > "Create new key"
   - Выберите "JSON"
   - Нажмите "Create"

5️⃣ Сохраните ключ:
   - Файл JSON автоматически скачается
   - Переместите его в папку credentials/
   - Переименуйте в quickstart-1591698112539-676a9e339335.json
    """)

def create_test_spreadsheet_guide():
    """Руководство по созданию тестовой таблицы"""
    print_step(3, "Создание тестовой Google Sheets таблицы")
    
    print("""
1️⃣ Создайте новую таблицу:
   - Перейдите на https://sheets.google.com
   - Нажмите "Создать" > "Пустой файл"
   - Назовите таблицу (например: "Test Connector Table")

2️⃣ Добавьте тестовые данные:
   В ячейки A1:C3 введите:
   | Имя    | Возраст | Город   |
   | Иван   | 25      | Москва  |
   | Мария  | 30      | СПб     |

3️⃣ Скопируйте ID таблицы:
   - ID находится в URL между '/d/' и '/edit'
   - Например: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

4️⃣ Предоставьте доступ Service Account:
   - Нажмите "Настройки доступа"
   - Добавьте email вашего Service Account
   - Дайте права "Редактор"
   - Service Account email можно найти в JSON файле (поле client_email)
    """)
    
    open_browser = input("\n🌐 Открыть Google Sheets в браузере? (y/n): ").lower()
    if open_browser == 'y':
        webbrowser.open("https://sheets.google.com")

def create_config_file():
    """Создание файла конфигурации"""
    print_step(4, "Создание файла конфигурации")
    
    config = {
        "health_tracking": "",
        "finance_tracking": "",
        "learning_progress": "",
        "project_management": "",
        "test_table": ""
    }
    
    print("Введите ID таблиц для различных целей (Enter для пропуска):")
    
    for key in config.keys():
        display_name = key.replace('_', ' ').title()
        value = input(f"📊 {display_name}: ").strip()
        if value:
            config[key] = value
    
    # Сохраняем конфигурацию
    config_path = "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Конфигурация сохранена в {config_path}")
    return config

def verify_setup():
    """Проверка настройки"""
    print_step(5, "Проверка настройки")
    
    checks = [
        ("credentials/quickstart-1591698112539-676a9e339335.json", "Service Account ключ"),
        ("config.json", "Файл конфигурации"),
        ("requirements.txt", "Файл зависимостей")
    ]
    
    all_good = True
    
    for file_path, description in checks:
        if os.path.exists(file_path):
            print(f"✅ {description}: найден")
        else:
            print(f"❌ {description}: не найден ({file_path})")
            all_good = False
    
    return all_good

def test_connection():
    """Тестирование подключения"""
    print_step(6, "Тестирование подключения")
    
    try:
        # Попытка импорта и базовой проверки
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from connector import GoogleSheetsConnector
        
        sheets = GoogleSheetsConnector()
        
            if os.path.exists("credentials/quickstart-1591698112539-676a9e339335.json"):
        success = sheets.authenticate_service_account("credentials/quickstart-1591698112539-676a9e339335.json")
            if success:
                print("✅ Аутентификация успешна!")
                
                # Пробуем получить информацию о тестовой таблице
                if sheets.config.get('test_table'):
                    try:
                        info = sheets.get_spreadsheet_info(sheets.config['test_table'])
                        print(f"✅ Подключение к таблице '{info['title']}' успешно!")
                        return True
                    except Exception as e:
                        print(f"❌ Ошибка подключения к таблице: {e}")
                        return False
                else:
                    print("⚠️ ID тестовой таблицы не настроен")
                    return False
            else:
                print("❌ Ошибка аутентификации")
                return False
        else:
            print("❌ Файл quickstart-1591698112539-676a9e339335.json не найден")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def final_instructions():
    """Финальные инструкции"""
    print_header("🎉 Настройка завершена!")
    
    print("""
Теперь вы можете использовать Google Sheets Connector:

📚 Примеры использования:
   py examples/basic_usage.py

🔧 Основные команды:
   - Чтение данных: sheets.read_range(spreadsheet_id, "Sheet1!A1:C10")
   - Запись данных: sheets.write_range(spreadsheet_id, "Sheet1!A1", data)
   - Работа с DataFrame: sheets.read_to_dataframe() / write_dataframe()

📋 Файлы:
   - connector.py - основной класс
   - auth.py - модуль аутентификации
   - examples/ - примеры использования
   - utils/ - утилиты для интеграции

🔗 Полезные ссылки:
   - Google Sheets API: https://developers.google.com/sheets/api
   - Google Cloud Console: https://console.cloud.google.com
   - Документация: README.md

💡 Советы:
   - Храните credentials/ в .gitignore
   - Создавайте отдельные Service Accounts для разных проектов
   - Используйте config.json для управления ID таблиц
    """)

def main():
    """Главная функция настройки"""
    print_header("Google Sheets Connector - Мастер настройки")
    
    print("""
Этот мастер поможет вам настроить Google Sheets Connector.
Процесс включает:
1. Создание проекта в Google Cloud
2. Настройка Service Account
3. Создание тестовой таблицы
4. Настройка конфигурации
5. Проверка подключения

Убедитесь, что у вас есть аккаунт Google и доступ к интернету.
    """)
    
    if input("\n🚀 Начать настройку? (y/n): ").lower() != 'y':
        print("👋 Настройка отменена")
        return
    
    try:
        # Создаем директории
        setup_directories()
        
        # Руководства по настройке
        create_google_cloud_project_guide()
        input("\n⏸️ Нажмите Enter после выполнения шага 1...")
        
        create_service_account_guide()
        input("\n⏸️ Нажмите Enter после выполнения шага 2...")
        
        create_test_spreadsheet_guide()
        input("\n⏸️ Нажмите Enter после выполнения шага 3...")
        
        # Создаем конфигурацию
        create_config_file()
        
        # Проверяем настройку
        if verify_setup():
            print("\n✅ Все файлы на месте!")
            
            # Тестируем подключение
            if test_connection():
                final_instructions()
            else:
                print("\n❌ Тест подключения не прошел. Проверьте настройки.")
        else:
            print("\n❌ Некоторые файлы отсутствуют. Завершите настройку.")
        
    except KeyboardInterrupt:
        print("\n👋 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка во время настройки: {e}")

if __name__ == "__main__":
    main()
