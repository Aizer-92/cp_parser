#!/usr/bin/env python3
"""
Тест API КП
"""

import requests
import json

BASE_URL = "http://localhost:5000"

print("🧪 ТЕСТ API КП")
print("=" * 80)

# Создаем сессию для сохранения cookies
session = requests.Session()

# 1. Проверяем пустое КП
print("\n1️⃣  Получение пустого КП...")
resp = session.get(f"{BASE_URL}/api/kp")
print(f"   Статус: {resp.status_code}")
print(f"   Ответ: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

# 2. Добавляем товар в КП
print("\n2️⃣  Добавление товара в КП...")
print("   (product_id=1, price_offer_id=1)")
resp = session.post(f"{BASE_URL}/api/kp/add", json={
    'product_id': 1,
    'price_offer_id': 1
})
print(f"   Статус: {resp.status_code}")
print(f"   Ответ: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

# 3. Добавляем еще один товар
print("\n3️⃣  Добавление второго товара...")
print("   (product_id=2, price_offer_id=5)")
resp = session.post(f"{BASE_URL}/api/kp/add", json={
    'product_id': 2,
    'price_offer_id': 5
})
print(f"   Статус: {resp.status_code}")
print(f"   Ответ: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

# 4. Получаем КП
print("\n4️⃣  Получение КП с товарами...")
resp = session.get(f"{BASE_URL}/api/kp")
print(f"   Статус: {resp.status_code}")
data = resp.json()
if data['success']:
    print(f"   Всего товаров: {data['total_items']}")
    for item in data['kp_items']:
        print(f"\n   📦 {item['product']['name']}")
        print(f"      Тираж: {item['price_offer']['quantity']} шт")
        print(f"      Маршрут: {item['price_offer']['route']}")
        print(f"      Цена: ${item['price_offer']['price_usd']}")

# 5. Проверка что товары в КП
print("\n5️⃣  Проверка price_offer_id в КП...")
resp = session.post(f"{BASE_URL}/api/kp/check", json={
    'price_offer_ids': [1, 5, 99]
})
print(f"   Статус: {resp.status_code}")
print(f"   Ответ: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

# 6. Очистка КП
print("\n6️⃣  Очистка КП...")
resp = session.delete(f"{BASE_URL}/api/kp/clear")
print(f"   Статус: {resp.status_code}")
print(f"   Ответ: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")

# 7. Проверка что КП пустое
print("\n7️⃣  Проверка что КП очищено...")
resp = session.get(f"{BASE_URL}/api/kp")
print(f"   Статус: {resp.status_code}")
data = resp.json()
print(f"   Всего товаров: {data['total_items']}")

print("\n" + "=" * 80)
print("✅ ТЕСТ ЗАВЕРШЕН!")
print("\nЧтобы запустить тест:")
print("1. Запусти сервер: cd web_interface && python3 app.py")
print("2. В другом терминале: python3 test_kp_api.py")

