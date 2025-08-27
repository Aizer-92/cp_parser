#!/usr/bin/env python3
"""
Тестирование API полей Planfix
"""

import json
import requests

def test_api_fields():
    """Тестирование доступных полей в API"""
    
    # Загружаем конфигурацию
    try:
        with open('planfix_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return
    
    headers = {
        'Authorization': f'Bearer {config["rest_api"]["auth_token"]}',
        'Content-Type': 'application/json'
    }
    
    # Тестируем получение одной задачи
    try:
        url = f"{config['rest_api']['base_url']}/task/96041"
        print(f"🔍 Тестируем URL: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Получен ответ от API")
            
            if 'task' in data:
                task = data['task']
                print("\n📋 Доступные поля задачи:")
                for key, value in task.items():
                    print(f"  {key}: {type(value).__name__}")
                    if isinstance(value, (dict, list)) and len(str(value)) < 200:
                        print(f"    Значение: {value}")
                    elif isinstance(value, str) and len(value) < 100:
                        print(f"    Значение: {value}")
                    else:
                        print(f"    Значение: {str(value)[:50]}...")
            else:
                print("❌ Поле 'task' не найдено в ответе")
                print("📄 Полный ответ:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    test_api_fields()
