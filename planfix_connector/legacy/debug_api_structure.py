import requests
import json

def check_api_structure():
    """Проверяет структуру ответа API для понимания кастомных полей"""
    try:
        # Загружаем конфигурацию
        with open('planfix_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        headers = {
            'Authorization': f'Bearer {config["rest_api"]["auth_token"]}',
            'Content-Type': 'application/json'
        }
        
        print("🔍 Проверяем запрос с явным указанием customFields:")
        
        request_data = {
            'offset': 0,
            'pageSize': 2,
            'filters': [
                {
                    "type": 10,
                    "operator": "equal",
                    "value": [127]  # КП Согласовано
                }
            ],
            'fields': 'id,name,status,customFields'  # Явно запрашиваем customFields
        }
        
        response = requests.post(
            f"{config['rest_api']['base_url']}/task/list",
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('tasks', [])
            print(f"📊 Найдено задач: {len(tasks)}")
            
            for i, task in enumerate(tasks):
                print(f"\n  Задача {i+1} (ID: {task.get('id')}):")
                print(f"    Название: {task.get('name', 'Н/Д')[:50]}...")
                print(f"    Статус: {task.get('status', {}).get('name', 'Н/Д')}")
                
                # Проверяем все поля задачи
                print(f"    📋 Все поля задачи:")
                for key, value in task.items():
                    if value is not None:
                        print(f"      {key}: {type(value).__name__} = {value}")
                
                # Проверяем customFields
                if 'customFields' in task:
                    if task['customFields']:
                        print(f"    ✅ customFields: {len(task['customFields'])} полей")
                        for j, field in enumerate(task['customFields']):
                            print(f"      [{j}] {field}")
                    else:
                        print(f"    ⚠️ customFields: пустой массив")
                else:
                    print(f"    ❌ customFields: поле отсутствует")
                    
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_api_structure()
