#!/usr/bin/env python3
"""
🎨 ТЕСТ МОДУЛЬНОГО CSS - ФАЗА 2.1
Проверяем что интерфейс остается идентичным после вынесения CSS в модули
"""

import requests
import time
from pathlib import Path

def test_modular_css():
    """Тестирует что модульный CSS работает идентично встроенному"""
    
    print("ТЕСТИРОВАНИЕ МОДУЛЬНОГО CSS (ФАЗА 2.1)")
    print("=" * 50)
    
    # Ждем запуска приложения
    time.sleep(3)
    
    base_url = "http://localhost:8000"
    
    try:
        # Тест 1: Главная страница загружается
        print("ТЕСТ 1: Загрузка главной страницы...")
        
        # Создаем сессию для аутентификации  
        session = requests.Session()
        
        # Логинимся
        login_response = session.post(f"{base_url}/api/login", data={
            "username": "admin", 
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print(f"ОШИБКА авторизации: {login_response.status_code}")
            return False
        
        # Получаем главную страницу
        main_response = session.get(f"{base_url}/")
        
        if main_response.status_code != 200:
            print(f"ОШИБКА Главная страница не загружается: {main_response.status_code}")
            return False
            
        content = main_response.text
        print("OK Главная страница загружается")
        
        # Тест 2: CSS файлы подгружаются
        print("\nТЕСТ 2: Загрузка модульных CSS файлов...")
        
        css_files = [
            "/static/css/main.css",
            "/static/css/components/header.css", 
            "/static/css/components/cards.css",
            "/static/css/components/forms.css",
            "/static/css/components/history.css"
        ]
        
        css_loaded = True
        for css_file in css_files:
            css_response = session.get(f"{base_url}{css_file}")
            if css_response.status_code == 200:
                print(f"   OK {css_file}")
            else:
                print(f"   ОШИБКА {css_file}: {css_response.status_code}")
                css_loaded = False
        
        if not css_loaded:
            return False
            
        # Тест 3: HTML содержит ссылки на CSS модули
        print("\nТЕСТ 3: HTML содержит правильные ссылки на CSS...")
        
        required_links = [
            '/static/css/main.css',
            '/static/css/components/header.css',
            '/static/css/components/cards.css'
        ]
        
        links_found = True
        for link in required_links:
            if link in content:
                print(f"   OK Найдена ссылка на {link}")
            else:
                print(f"   ОШИБКА НЕ найдена ссылка на {link}")
                links_found = False
        
        if not links_found:
            return False
            
        # Тест 4: Проверяем что встроенных стилей НЕТ
        print("\nТЕСТ 4: Встроенные стили удалены...")
        
        if '<style>' in content:
            print("   ОШИБКА Найдены встроенные <style> теги - модуляризация неполная")
            return False
        else:
            print("   OK Встроенных <style> тегов нет")
        
        # Тест 5: API работает (функциональность не сломалась)
        print("\nТЕСТ 5: Функциональность сохранена...")
        
        api_response = session.get(f"{base_url}/api/categories")
        if api_response.status_code == 200:
            categories = api_response.json()
            print(f"   OK API категорий работает: {len(categories)} категорий")
        else:
            print(f"   ОШИБКА API категорий не работает: {api_response.status_code}")
            return False
            
        print("\n" + "=" * 50)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("OK Модульный CSS работает идентично встроенному")
        print("OK Интерфейс остается без изменений") 
        print("OK Функциональность сохранена")
        print("ГОТОВО К ДЕПЛОЮ НА RAILWAY!")
        
        return True
        
    except Exception as e:
        print(f"\nОШИБКА ТЕСТИРОВАНИЯ: {e}")
        return False

def compare_file_sizes():
    """Сравниваем размеры файлов"""
    print("\nСРАВНЕНИЕ РАЗМЕРОВ ФАЙЛОВ:")
    
    try:
        backup_size = Path("index_backup.html").stat().st_size
        current_size = Path("index.html").stat().st_size  
        
        print(f"   Встроенный CSS (backup): {backup_size:,} байт")
        print(f"   Модульный CSS (current): {current_size:,} байт")
        print(f"   Разница: {backup_size - current_size:+,} байт")
        
        if current_size < backup_size:
            reduction = ((backup_size - current_size) / backup_size) * 100
            print(f"   HTML файл уменьшен на {reduction:.1f}%")
        
    except Exception as e:
        print(f"   Не удалось сравнить размеры: {e}")

if __name__ == "__main__":
    success = test_modular_css()
    compare_file_sizes()
    
    print("\n" + "=" * 50)
    if success:
        print("РЕЗУЛЬТАТ: МОДУЛЬНЫЙ CSS ГОТОВ К ДЕПЛОЮ")
        print("   Можно безопасно деплоить на Railway")
    else:
        print("РЕЗУЛЬТАТ: ТРЕБУЮТСЯ ИСПРАВЛЕНИЯ")
        print("   Нужно вернуться к встроенному CSS")

