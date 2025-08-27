import requests
import json
import xml.etree.ElementTree as ET

def check_xml_api():
    """Проверяет XML API для доступа к кастомным полям"""
    try:
        # Загружаем конфигурацию
        with open('planfix_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("🔍 Проверяем XML API:")
        print(f"  Base URL: {config['xml_api']['base_url']}")
        print(f"  API Key: {config['xml_api']['api_key'][:10]}...")
        
        # Создаем XML запрос для получения задач
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<request method="task.getList">
    <api_key>{config['xml_api']['api_key']}</api_key>
    <token>{config['xml_api']['token']}</token>
    <pageSize>2</pageSize>
    <filters>
        <filter>
            <type>10</type>
            <operator>equal</operator>
            <value>127</value>
        </filter>
    </filters>
</request>"""
        
        print(f"\n📤 Отправляем XML запрос:")
        print(xml_request)
        
        # Отправляем запрос
        response = requests.post(
            config['xml_api']['base_url'],
            data=xml_request.encode('utf-8'),
            headers={'Content-Type': 'application/xml'},
            timeout=30
        )
        
        print(f"\n📥 Ответ XML API:")
        print(f"  Статус: {response.status_code}")
        print(f"  Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                # Парсим XML ответ
                root = ET.fromstring(response.text)
                print(f"  ✅ XML успешно распарсен")
                print(f"  Корневой элемент: {root.tag}")
                
                # Ищем задачи
                tasks = root.findall('.//task')
                print(f"  📊 Найдено задач: {len(tasks)}")
                
                if tasks:
                    task = tasks[0]
                    print(f"\n  🔍 Первая задача:")
                    print(f"    ID: {task.find('id').text if task.find('id') is not None else 'Н/Д'}")
                    print(f"    Название: {task.find('name').text if task.find('name') is not None else 'Н/Д'}")
                    
                    # Ищем кастомные поля
                    custom_fields = task.findall('.//customField')
                    if custom_fields:
                        print(f"    ✅ Кастомные поля: {len(custom_fields)}")
                        for cf in custom_fields[:3]:  # Показываем первые 3
                            name = cf.find('name').text if cf.find('name') is not None else 'Без названия'
                            value = cf.find('value').text if cf.find('value') is not None else 'Н/Д'
                            print(f"      {name}: {value}")
                    else:
                        print(f"    ❌ Кастомные поля не найдены")
                        
            except ET.ParseError as e:
                print(f"  ❌ Ошибка парсинга XML: {e}")
                print(f"  Ответ: {response.text[:500]}...")
        else:
            print(f"  ❌ Ошибка API: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_xml_api()

