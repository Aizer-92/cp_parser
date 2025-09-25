#!/usr/bin/env python3
"""
Финальный тест исправленной морфологии полнотекстового поиска
"""

import requests
import time

def test_final_morphology():
    """Финальный тест морфологии через API"""
    
    base_url = "http://localhost:8003"
    
    # Ждем запуска сервера
    print("⏳ Ожидание запуска сервера...")
    time.sleep(3)
    
    # Тестовые пары слов (разные формы одного слова)
    test_pairs = [
        ("таблетница", "таблетницы"),
        ("телефон", "телефона"),
        ("платье", "платья"),
        ("часы", "часов")
    ]
    
    print("🔍 Финальный тест исправленной морфологии...")
    
    for word1, word2 in test_pairs:
        try:
            print(f"\n📝 Тестирование: '{word1}' vs '{word2}'")
            
            # Тест первого слова
            response1 = requests.get(f"{base_url}/api/products", params={
                "search": word1,
                "limit": 5
            }, timeout=10)
            
            # Тест второго слова
            response2 = requests.get(f"{base_url}/api/products", params={
                "search": word2,
                "limit": 5
            }, timeout=10)
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                count1 = data1['total_count']
                count2 = data2['total_count']
                
                print(f"  '{word1}': {count1} товаров")
                print(f"  '{word2}': {count2} товаров")
                
                if count1 == count2:
                    print(f"  ✅ Морфология работает правильно!")
                else:
                    print(f"  ❌ Проблема с морфологией! Разница: {abs(count1 - count2)}")
                
                # Показываем топ результаты
                if data1['products']:
                    print(f"  📦 Топ результаты для '{word1}':")
                    for i, product in enumerate(data1['products'][:3], 1):
                        print(f"    {i}. {product['title'][:50]}...")
                
            else:
                print(f"  ❌ Ошибка API: {response1.status_code} / {response2.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Ошибка запроса: {e}")
        except Exception as e:
            print(f"  ❌ Общая ошибка: {e}")
    
    # Тест веб-интерфейса
    print(f"\n🌐 Тестирование веб-интерфейса...")
    try:
        response = requests.get(f"{base_url}/?search=таблетница", timeout=10)
        if response.status_code == 200:
            print("✅ Веб-интерфейс доступен")
            if "таблетница" in response.text.lower():
                print("✅ Поиск работает в веб-интерфейсе")
            else:
                print("❌ Поиск не работает в веб-интерфейсе")
        else:
            print(f"❌ Веб-интерфейс недоступен: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка веб-интерфейса: {e}")

if __name__ == "__main__":
    test_final_morphology()
