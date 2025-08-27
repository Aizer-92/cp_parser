"""
Проверка Service Account credentials и доступа к таблице
"""

import json
import os
from datetime import datetime

def check_service_account():
    """Проверяет Service Account файл"""
    print("🔍 Проверка Service Account credentials")
    print("=" * 50)
    
    credentials_file = "credentials/quickstart-1591698112539-676a9e339335.json"
    
    if not os.path.exists(credentials_file):
        print("❌ Файл quickstart-1591698112539-676a9e339335.json не найден")
        return False
    
    try:
        with open(credentials_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ Файл credentials найден и загружен")
        print(f"📧 Client Email: {data.get('client_email', 'N/A')}")
        print(f"🆔 Project ID: {data.get('project_id', 'N/A')}")
        print(f"🔧 Type: {data.get('type', 'N/A')}")
        
        # Проверяем обязательные поля
        required_fields = ['type', 'project_id', 'private_key', 'client_email', 'client_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Отсутствуют поля: {', '.join(missing_fields)}")
            return False
        
        print("✅ Все необходимые поля присутствуют")
        return True, data.get('client_email')
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_table_access():
    """Тестирует доступ к таблице приоритетов"""
    print("\n🚀 Тестирование доступа к таблице")
    print("=" * 50)
    
    try:
        from connector import GoogleSheetsConnector
        
        # Создаем коннектор
        sheets = GoogleSheetsConnector()
        
        # Аутентификация
        print("🔐 Выполняется аутентификация...")
        success = sheets.authenticate_service_account("credentials/quickstart-1591698112539-676a9e339335.json")
        
        if not success:
            print("❌ Ошибка аутентификации")
            return False
        
        print("✅ Аутентификация успешна")
        
        # ID таблицы из config
        spreadsheet_id = sheets.get_config_spreadsheet('priorities_table')
        
        if not spreadsheet_id:
            print("❌ ID таблицы не найден в config.json")
            return False
        
        print(f"🆔 ID таблицы: {spreadsheet_id}")
        
        # Проверяем доступ к таблице
        print("📊 Получение информации о таблице...")
        info = sheets.get_spreadsheet_info(spreadsheet_id)
        
        print(f"✅ Подключение успешно!")
        print(f"📋 Название: {info['title']}")
        print(f"📄 Листы: {len(info['sheets'])}")
        
        # Показываем листы
        print("\n📑 Доступные листы:")
        for i, sheet in enumerate(info['sheets'], 1):
            print(f"   {i}. {sheet['title']} ({sheet['rows']} строк × {sheet['columns']} колонок)")
        
        # Пробуем прочитать данные
        first_sheet = info['sheets'][0]['title']
        print(f"\n📖 Тестовое чтение данных с листа '{first_sheet}'...")
        
        # Читаем первые несколько строк
        sample_data = sheets.read_range(spreadsheet_id, f"{first_sheet}!A1:E3")
        
        if sample_data:
            print("✅ Данные успешно прочитаны:")
            for i, row in enumerate(sample_data):
                row_display = [cell[:30] + "..." if len(str(cell)) > 30 else str(cell) for cell in row[:5]]
                print(f"   Строка {i+1}: {row_display}")
        
        # Подсчитываем общее количество записей
        all_data = sheets.read_range(spreadsheet_id, f"{first_sheet}!A:A")
        if all_data:
            record_count = len([row for row in all_data if row and str(row[0]).strip()]) - 1
            print(f"\n📈 Общее количество записей: {record_count}")
        
        print(f"\n🎉 Полный доступ к таблице подтвержден!")
        print(f"🔗 URL: {info['url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка доступа к таблице: {e}")
        
        # Анализируем ошибку
        error_str = str(e)
        if "403" in error_str or "Forbidden" in error_str:
            print("\n💡 Ошибка доступа (403 Forbidden):")
            print("   ❌ Service Account не имеет доступа к таблице")
            print("   🔧 Решение:")
            print("      1. Откройте таблицу в браузере")
            print("      2. Нажмите 'Настройки доступа' (Share)")
            print("      3. Добавьте email Service Account")
            print("      4. Дайте права 'Редактор'")
            
        elif "404" in error_str or "Not Found" in error_str:
            print("\n💡 Таблица не найдена (404):")
            print("   ❌ Неверный ID таблицы или таблица удалена")
            print("   🔧 Проверьте ID таблицы в config.json")
            
        elif "401" in error_str or "Unauthorized" in error_str:
            print("\n💡 Ошибка авторизации (401):")
            print("   ❌ Проблема с Service Account")
            print("   🔧 Проверьте корректность JSON файла")
            
        else:
            print(f"\n💡 Другая ошибка: {error_str}")
        
        return False

def main():
    """Главная функция проверки"""
    print("🔍 ПРОВЕРКА ДОСТУПА К GOOGLE SHEETS")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Проверяем Service Account
    credentials_check = check_service_account()
    
    if not credentials_check:
        print("\n❌ Проблемы с credentials файлом")
        return
    
    if isinstance(credentials_check, tuple):
        success, client_email = credentials_check
        if success:
            print(f"\n📧 Service Account Email: {client_email}")
            print("🔧 Убедитесь, что этот email добавлен в настройки доступа к таблице!")
    
    # Тестируем доступ к таблице
    table_access = test_table_access()
    
    if table_access:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Service Account настроен корректно")
        print("✅ Доступ к таблице подтвержден")
        print("✅ Данные успешно читаются")
        print("\n🚀 Теперь можете использовать:")
        print("   py priorities_manager.py")
    else:
        print("\n❌ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("🔧 Следуйте инструкциям выше для решения проблем")

if __name__ == "__main__":
    main()
