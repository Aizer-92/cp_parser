#!/usr/bin/env python3
"""
Скрипт для скачивания обновленной таблицы "Мерч для Sense" из Google Sheets
"""

import requests
import os
from datetime import datetime

def download_merch_sense():
    """Скачивание таблицы "Мерч для Sense" из Google Sheets"""
    
    # URL для скачивания в формате Excel
    sheet_url = "https://docs.google.com/spreadsheets/d/1iB1J0TJevoHzrduqeySqO6gI_xLdhSDV9jxOdKICDY8/export?format=xlsx"
    
    print(f"📥 Скачиваем таблицу 'Мерч для Sense'...")
    print(f"URL: {sheet_url}")
    
    try:
        # Скачиваем файл
        response = requests.get(sheet_url)
        response.raise_for_status()
        
        # Создаем имя файла с timestamp
        timestamp = int(datetime.now().timestamp())
        filename = f"storage/excel_files/Мерч для Sense_{timestamp}.xlsx"
        
        # Сохраняем файл
        os.makedirs("storage/excel_files", exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Файл сохранен: {filename}")
        print(f"📊 Размер файла: {len(response.content)} байт")
        
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return None

def main():
    print("🔄 Скачивание обновленной таблицы 'Мерч для Sense'...")
    
    # Проверяем, есть ли уже файл
    existing_files = []
    for file in os.listdir("storage/excel_files"):
        if file.startswith("Мерч для Sense"):
            existing_files.append(file)
    
    if existing_files:
        print(f"📁 Найдены существующие файлы: {existing_files}")
    
    # Скачиваем новый файл
    new_file = download_merch_sense()
    
    if new_file:
        print(f"\n✅ Новый файл готов для обработки: {new_file}")
        print("Теперь можно запустить парсинг изображений из этого файла")
    else:
        print("\n❌ Не удалось скачать файл")

if __name__ == "__main__":
    main()
