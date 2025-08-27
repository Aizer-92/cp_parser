"""
Быстрый тест подключения и чтения данных
"""

from connector import GoogleSheetsConnector
import pandas as pd

def main():
    print("🚀 Быстрый тест доступа к таблице")
    
    # Создаем коннектор
    sheets = GoogleSheetsConnector()
    
    # Аутентификация
    if not sheets.authenticate_service_account("credentials/service_account.json"):
        print("❌ Ошибка аутентификации")
        return
    
    print("✅ Аутентификация успешна")
    
    # ID таблицы
    spreadsheet_id = "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
    
    try:
        # Получаем информацию о таблице
        info = sheets.get_spreadsheet_info(spreadsheet_id)
        print(f"📊 Таблица: {info['title']}")
        
        # Читаем данные с первого листа
        sheet_name = "Лист1"
        print(f"📖 Чтение данных с листа '{sheet_name}'...")
        
        # Читаем первые 10 строк
        data = sheets.read_range(spreadsheet_id, f"{sheet_name}!A1:M10")
        
        if data:
            print(f"✅ Прочитано {len(data)} строк")
            print("\n📋 Заголовки:")
            if len(data) > 0:
                headers = data[0]
                for i, header in enumerate(headers):
                    print(f"   {chr(65+i)}: {header}")
            
            print("\n📊 Образец данных:")
            if len(data) > 1:
                for i, row in enumerate(data[1:4], 2):  # Показываем строки 2-4
                    print(f"   Строка {i}: {row[0][:50]}...")  # Только название проекта
        
        # Читаем в DataFrame
        print("\n📈 Чтение в DataFrame...")
        df = sheets.read_to_dataframe(spreadsheet_id, f"{sheet_name}!A1:M100", header_row=True)
        
        if not df.empty:
            print(f"✅ DataFrame создан: {df.shape[0]} строк × {df.shape[1]} колонок")
            
            # Показываем статистику по статусам
            if 'Статус' in df.columns:
                print("\n📊 Статистика по статусам:")
                status_counts = df['Статус'].value_counts().head(5)
                for status, count in status_counts.items():
                    print(f"   • {status}: {count}")
        
        print("\n🎉 Тест успешно завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
