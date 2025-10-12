"""
Тест V3 API на Railway Production
Проверяет работу всех endpoints через HTTP
"""

import requests
import json

BASE_URL = "https://price-calculator-production.up.railway.app"

def test_v3_production():
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ V3 API НА PRODUCTION")
    print("=" * 60)
    
    # 1. Тест создания фабрики
    print("\n1️⃣ Создание фабрики...")
    import time
    timestamp = int(time.time())
    factory_data = {
        "name": f"Тестовая фабрика {timestamp}",
        "contact": "https://wechat.com/test_prod",
        "comment": "Тест с Railway",
        "default_sample_time_days": 7,
        "default_production_time_days": 15,
        "default_sample_price_yuan": 10.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v3/factories/", json=factory_data, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        print(f"   Response text: {response.text[:200]}")
        
        if response.status_code in [200, 201]:
            factory = response.json()
            print(f"   Response type: {type(factory)}")
            if isinstance(factory, list):
                print(f"   ⚠️ API вернул список вместо объекта!")
                if len(factory) > 0:
                    factory = factory[0]
                else:
                    print(f"   ❌ Список пустой!")
                    return
            
            print(f"✅ Фабрика создана: ID={factory['id']}, Name='{factory['name']}'")
            factory_id = factory['id']
        else:
            print(f"❌ Ошибка создания фабрики: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception при создании фабрики: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Тест получения списка фабрик
    print("\n2️⃣ Получение списка фабрик...")
    try:
        response = requests.get(f"{BASE_URL}/api/v3/factories")
        if response.status_code == 200:
            factories = response.json()
            print(f"✅ Получено фабрик: {len(factories)}")
            for f in factories[:3]:
                print(f"   - ID={f['id']}: {f['name']}")
        else:
            print(f"❌ Ошибка получения фабрик: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception при получении фабрик: {e}")
    
    # 3. Тест создания позиции
    print("\n3️⃣ Создание позиции...")
    position_data = {
        "name": f"Футболка тестовая {timestamp}",
        "description": "Хлопок 180г/м², тест Railway",
        "category": "футболка",
        "design_files_urls": ["http://example.com/design.jpg"],
        "custom_fields": {"color": "white", "size": "L"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v3/positions/", json=position_data, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            position = response.json()
            print(f"   Response type: {type(position)}")
            if isinstance(position, list):
                print(f"   ⚠️ API вернул список вместо объекта!")
                if len(position) > 0:
                    position = position[0]
                else:
                    print(f"   ❌ Список пустой!")
                    return
            
            print(f"✅ Позиция создана: ID={position['id']}, Name='{position['name']}'")
            position_id = position['id']
        else:
            print(f"❌ Ошибка создания позиции: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception при создании позиции: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Тест создания расчёта
    print("\n4️⃣ Создание расчёта...")
    calculation_data = {
        "position_id": position_id,
        "factory_id": factory_id,
        "quantity": 500,
        "price_yuan": 12.5,
        "calculation_type": "quick",
        "weight_kg": 0.15,
        "factory_comment": "Тест production API"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v3/calculations/", json=calculation_data, allow_redirects=False)
        if response.status_code in [200, 201]:
            calculation = response.json()
            print(f"✅ Расчёт создан: ID={calculation['id']}")
            if 'position' in calculation and calculation['position']:
                print(f"   Position: {calculation['position'].get('name', 'N/A')}")
            if 'factory' in calculation and calculation['factory']:
                print(f"   Factory: {calculation['factory'].get('name', 'N/A')}")
            print(f"   Quantity: {calculation['quantity']} шт")
            calculation_id = calculation['id']
        else:
            print(f"❌ Ошибка создания расчёта: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception при создании расчёта: {e}")
        return
    
    # 5. Тест пересчёта маршрутов
    print("\n5️⃣ Пересчёт маршрутов...")
    try:
        recalc_data = {"category": "футболка"}  # Категория для пересчёта
        response = requests.post(
            f"{BASE_URL}/api/v3/calculations/{calculation_id}/recalculate",
            json=recalc_data,
            allow_redirects=True
        )
        if response.status_code == 200:
            routes = response.json()  # Напрямую список маршрутов
            print(f"✅ Маршруты пересчитаны: {len(routes)} маршрутов")
            for route in routes:
                print(f"   📍 {route['route_name']}:")
                cost_rub = float(route.get('cost_price_rub', 0) or 0)
                sale_rub = float(route.get('sale_price_rub', 0) or 0)
                print(f"      Себестоимость: {cost_rub:.2f} ₽")
                print(f"      Продажная цена: {sale_rub:.2f} ₽")
        else:
            print(f"❌ Ошибка пересчёта: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception при пересчёте: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    
    try:
        factories_count = len(requests.get(f"{BASE_URL}/api/v3/factories").json())
        positions_count = len(requests.get(f"{BASE_URL}/api/v3/positions").json())
        calculations_count = len(requests.get(f"{BASE_URL}/api/v3/calculations").json())
        
        print(f"Фабрик в БД: {factories_count}")
        print(f"Позиций в БД: {positions_count}")
        print(f"Расчётов в БД: {calculations_count}")
    except:
        print("⚠️ Не удалось получить статистику")
    
    print("\n✅ ТЕСТИРОВАНИЕ PRODUCTION API ЗАВЕРШЕНО!")
    print("=" * 60)

if __name__ == "__main__":
    test_v3_production()

