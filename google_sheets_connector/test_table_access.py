"""
Тестирование доступа к конкретной Google Sheets таблице
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from connector import GoogleSheetsConnector
    import pandas as pd
    from datetime import datetime
    
    def test_table_access():
        """Тестирование доступа к таблице"""
        print("🔍 Тестирование доступа к Google Sheets таблице")
        print("=" * 60)
        
        # Создаем коннектор
        sheets = GoogleSheetsConnector()
        
        # ID таблицы из функции main
        spreadsheet_id = extract_table_id_from_url("https://docs.google.com/spreadsheets/d/1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE/edit?gid=1074629753#gid=1074629753")
        
        # Проверяем наличие credentials
        credentials_file = "credentials/service_account.json"
        if not os.path.exists(credentials_file):
            print("❌ Файл credentials/service_account.json не найден")
            print("💡 Сначала настройте аутентификацию:")
            print("   1. Создайте Service Account в Google Cloud Console")
            print("   2. Скачайте JSON ключ")
            print("   3. Сохраните его как credentials/service_account.json")
            return False
        
        # Аутентификация
        print("🔐 Выполняется аутентификация...")
        if not sheets.authenticate_service_account(credentials_file):
            print("❌ Ошибка аутентификации")
            print("💡 Проверьте правильность Service Account файла")
            return False
        
        print("✅ Аутентификация успешна")
        
        try:
            # Получаем информацию о таблице
            print(f"\n📊 Получение информации о таблице...")
            info = sheets.get_spreadsheet_info(spreadsheet_id)
            
            print(f"📋 Название таблицы: {info['title']}")
            print(f"🔗 URL: {info['url']}")
            print(f"📄 Количество листов: {len(info['sheets'])}")
            
            print("\n📑 Листы в таблице:")
            for i, sheet in enumerate(info['sheets'], 1):
                print(f"   {i}. {sheet['title']} ({sheet['rows']} строк × {sheet['columns']} колонок)")
            
            # Попробуем прочитать данные с первого листа
            first_sheet = info['sheets'][0]['title']
            print(f"\n📖 Чтение данных с листа '{first_sheet}'...")
            
            # Читаем заголовки (первая строка)
            headers = sheets.read_range(spreadsheet_id, f"{first_sheet}!1:1")
            if headers and len(headers) > 0:
                print(f"📊 Заголовки ({len(headers[0])} колонок):")
                for i, header in enumerate(headers[0][:10]):  # Показываем первые 10 колонок
                    if header.strip():
                        print(f"   {chr(65+i)}: {header}")
                
                if len(headers[0]) > 10:
                    print(f"   ... и еще {len(headers[0]) - 10} колонок")
            
            # Читаем несколько строк данных
            sample_data = sheets.read_range(spreadsheet_id, f"{first_sheet}!A1:F5")
            if sample_data and len(sample_data) > 1:
                print(f"\n📋 Образец данных (первые 5 строк):")
                
                # Создаем DataFrame для красивого отображения
                df = pd.DataFrame(sample_data[1:], columns=sample_data[0][:6])
                print(df.to_string(index=False, max_cols=6, max_colwidth=30))
            
            # Подсчитываем количество записей
            all_data = sheets.read_range(spreadsheet_id, f"{first_sheet}!A:A")
            if all_data:
                record_count = len([row for row in all_data if row and row[0].strip()]) - 1  # Минус заголовок
                print(f"\n📈 Общее количество записей: {record_count}")
            
            print(f"\n✅ Доступ к таблице успешно проверен!")
            print(f"📊 Таблица содержит данные о: {info['title']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка доступа к таблице: {e}")
            
            # Анализируем тип ошибки
            if "403" in str(e):
                print("💡 Ошибка доступа (403):")
                print("   - Service Account не имеет доступа к таблице")
                print("   - Предоставьте доступ email'у из Service Account JSON файла")
                print("   - Email находится в поле 'client_email'")
            elif "404" in str(e):
                print("💡 Таблица не найдена (404):")
                print("   - Проверьте правильность ID таблицы")
                print("   - Убедитесь, что таблица существует и доступна")
            else:
                print(f"💡 Неизвестная ошибка: {e}")
            
            return False
    
    def extract_table_id_from_url(url):
        """Извлекает ID таблицы из URL"""
        try:
            # Ищем ID между '/d/' и '/edit' или следующим '/'
            start = url.find('/d/') + 3
            end = url.find('/', start)
            if end == -1:
                end = url.find('#', start)
            if end == -1:
                end = len(url)
            
            table_id = url[start:end]
            if table_id.endswith('/edit'):
                table_id = table_id[:-5]
            
            return table_id
        except:
            return None
    
    def main():
        """Главная функция"""
        print("🚀 Тестирование доступа к Google Sheets")
        print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # URL таблицы из вашего запроса
        table_url = "https://docs.google.com/spreadsheets/d/1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE/edit?gid=1074629753#gid=1074629753"
        
        print(f"🔗 URL таблицы: {table_url}")
        
        # Извлекаем ID
        table_id = extract_table_id_from_url(table_url)
        print(f"🆔 ID таблицы: {table_id}")
        
        if not table_id:
            print("❌ Не удалось извлечь ID таблицы из URL")
            return
        
        # Тестируем доступ
        success = test_table_access()
        
        if success:
            print("\n🎉 Тест завершен успешно!")
            print("\n💡 Возможные действия:")
            print("   - Читать данные из таблицы")
            print("   - Записывать новые данные")
            print("   - Создавать отчеты")
            print("   - Автоматизировать обработку данных")
        else:
            print("\n❌ Тест не прошел")
            print("\n🔧 Следующие шаги:")
            print("   1. Настройте Service Account в Google Cloud Console")
            print("   2. Предоставьте доступ к таблице")
            print("   3. Повторите тест")
        
        print(f"\n📊 Для работы с этой таблицей добавьте в config.json:")
        print(f'   "priorities_table": "{table_id}"')

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Установите зависимости: py -m pip install google-api-python-client google-auth pandas")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")
