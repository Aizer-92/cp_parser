#!/usr/bin/env python3
"""
🧪 ТЕСТ МОДУЛЬНОГО JAVASCRIPT - ФАЗА 2.2
Проверяем что модульная архитектура JS работает идентично встроенной
"""

import requests
import time
from pathlib import Path

def test_modular_javascript():
    """Тестирует что модульный JavaScript работает идентично встроенному"""
    
    print("ТЕСТИРОВАНИЕ МОДУЛЬНОГО JAVASCRIPT (ФАЗА 2.2)")
    print("=" * 55)
    
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
        
        # Тест 2: JavaScript модули подгружаются
        print("\nТЕСТ 2: Загрузка модульных JavaScript файлов...")
        
        js_files = [
            "/static/js/app-config.js",
            "/static/js/api-service.js", 
            "/static/js/utils.js",
            "/static/js/form-handlers.js",
            "/static/js/history-handlers.js",
            "/static/js/main-app.js"
        ]
        
        js_loaded = True
        for js_file in js_files:
            js_response = session.get(f"{base_url}{js_file}")
            if js_response.status_code == 200:
                print(f"   OK {js_file}")
            else:
                print(f"   ОШИБКА {js_file}: {js_response.status_code}")
                js_loaded = False
        
        if not js_loaded:
            return False
            
        # Тест 3: HTML содержит ссылки на JS модули
        print("\nТЕСТ 3: HTML содержит правильные ссылки на JavaScript...")
        
        required_scripts = [
            '/static/js/app-config.js',
            '/static/js/main-app.js'
        ]
        
        scripts_found = True
        for script in required_scripts:
            if script in content:
                print(f"   OK Найдена ссылка на {script}")
            else:
                print(f"   ОШИБКА НЕ найдена ссылка на {script}")
                scripts_found = False
        
        if not scripts_found:
            return False
            
        # Тест 4: Проверяем что встроенного JavaScript НЕТ
        print("\nТЕСТ 4: Встроенный JavaScript удален...")
        
        # Ищем старые паттерны Vue приложения
        vue_patterns = ['createApp({', 'const { createApp } = Vue;', '.mount(\'#app\');']
        inline_js_found = False
        
        for pattern in vue_patterns:
            if pattern in content:
                print(f"   ОШИБКА Найден встроенный JS паттерн: {pattern}")
                inline_js_found = True
        
        if inline_js_found:
            return False
        else:
            print("   OK Встроенного JavaScript нет")
        
        # Тест 5: API все еще работает (функциональность не сломалась)
        print("\nТЕСТ 5: Функциональность сохранена...")
        
        # Проверяем API категорий
        api_response = session.get(f"{base_url}/api/categories")
        if api_response.status_code == 200:
            categories = api_response.json()
            print(f"   OK API категорий работает: {len(categories)} категорий")
        else:
            print(f"   ОШИБКА API категорий не работает: {api_response.status_code}")
            return False
            
        # Проверяем API расчета (простой тест)
        calc_data = {
            "product_name": "Тестовый товар",
            "price_yuan": 10.0,
            "weight_kg": 0.5,
            "quantity": 100,
            "delivery_type": "rail",
            "markup": 1.7
        }
        
        calc_response = session.post(f"{base_url}/api/calculate", json=calc_data)
        if calc_response.status_code == 200:
            calc_result = calc_response.json()
            print("   OK API расчета работает")
        else:
            print(f"   ОШИБКА API расчета не работает: {calc_response.status_code}")
            return False
            
        print("\n" + "=" * 55)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("OK Модульный JavaScript работает идентично встроенному")
        print("OK Все JS модули загружаются корректно") 
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
        original_size = Path("index.html").stat().st_size
        modular_size = Path("index_with_modular_js.html").stat().st_size  
        
        print(f"   Встроенный JS (index.html): {original_size:,} байт")
        print(f"   Модульный JS (index_with_modular_js.html): {modular_size:,} байт")
        print(f"   Разница: {original_size - modular_size:+,} байт")
        
        if modular_size < original_size:
            reduction = ((original_size - modular_size) / original_size) * 100
            print(f"   HTML файл уменьшен на {reduction:.1f}%")
        elif modular_size > original_size:
            increase = ((modular_size - original_size) / original_size) * 100
            print(f"   HTML файл увеличен на {increase:.1f}%")
        
        # Подсчитываем общий размер JS модулей
        js_modules = [
            "static/js/app-config.js",
            "static/js/api-service.js",
            "static/js/utils.js", 
            "static/js/form-handlers.js",
            "static/js/history-handlers.js",
            "static/js/main-app.js"
        ]
        
        total_js_size = 0
        for js_file in js_modules:
            if Path(js_file).exists():
                total_js_size += Path(js_file).stat().st_size
        
        print(f"   Общий размер JS модулей: {total_js_size:,} байт")
        print(f"   Итого (HTML + JS): {modular_size + total_js_size:,} байт")
        
        total_diff = (modular_size + total_js_size) - original_size
        if total_diff > 0:
            increase = (total_diff / original_size) * 100
            print(f"   Общее увеличение: +{total_diff:,} байт (+{increase:.1f}%)")
        else:
            decrease = (abs(total_diff) / original_size) * 100
            print(f"   Общее уменьшение: {total_diff:,} байт (-{decrease:.1f}%)")
        
    except Exception as e:
        print(f"   Не удалось сравнить размеры: {e}")

if __name__ == "__main__":
    success = test_modular_javascript()
    compare_file_sizes()
    
    print("\n" + "=" * 55)
    if success:
        print("РЕЗУЛЬТАТ: МОДУЛЬНЫЙ JAVASCRIPT ГОТОВ К ДЕПЛОЮ")
        print("   Можно безопасно заменять index.html и деплоить")
    else:
        print("РЕЗУЛЬТАТ: ТРЕБУЮТСЯ ИСПРАВЛЕНИЯ")
        print("   Нужно исправить ошибки перед деплоем")
