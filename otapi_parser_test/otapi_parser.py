#!/usr/bin/env python3
"""
Правильный парсер для 1688.com через OTAPI API
"""
import requests
import time
import random
import json
import logging
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OTAPIParser:
    """Парсер для 1688.com через OTAPI API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://otapi.net/service-json/BatchGetItemFullInfo"
        self.instance_key = "5bde2d7b-250e-4a48-ad4c-ec18d4e40bed"
        self.language = "ru"
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def parse_product(self, item_id):
        """Парсит товар по ID через OTAPI API"""
        try:
            print(f"🔍 Парсинг товара {item_id} через OTAPI API...")
            
            # Убираем префикс abb- если есть
            if str(item_id).startswith('abb-'):
                item_id = str(item_id)[4:]
            
            # Параметры запроса
            params = {
                'instanceKey': self.instance_key,
                'language': self.language,
                'signature': '',
                'timestamp': '',
                'sessionId': '',
                'itemParameters': '',
                'itemId': f'abb-{item_id}',
                'blockList': 'Description'  # Исключаем описание для экономии трафика
            }
            
            # Заголовки
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'http://otapi.net/',
            }
            
            # Задержка между запросами
            time.sleep(random.uniform(0.5, 1.0))
            
            # Выполняем запрос
            response = self.session.get(self.base_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Успешно получен ответ для {item_id}")
                
                try:
                    # Парсим JSON ответ
                    data = response.json()
                    
                    # Проверяем успешность запроса
                    if data.get('ErrorCode') == 'Ok':
                        result = self.process_otapi_response(data, item_id)
                        return result
                    else:
                        print(f"❌ API ошибка для {item_id}: {data.get('ErrorCode')}")
                        return None
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON для {item_id}: {e}")
                    return None
            else:
                print(f"❌ HTTP {response.status_code} для {item_id}")
                return None
                
        except Exception as e:
            logging.error(f"Ошибка парсинга товара {item_id}: {e}")
            return None
    
    def process_otapi_response(self, data, item_id):
        """Обрабатывает ответ от OTAPI API"""
        try:
            result = data.get('Result', {})
            item = result.get('Item', {})
            
            if not item:
                print(f"❌ Нет данных Item для {item_id}")
                return None
            
            # Формируем результат в том же формате что и оригинальные chunks
            parsed_item = {
                'id': f'abb-{item_id}',
                'item_id': item_id,
                'url': f'https://detail.1688.com/offer/{item_id}.html',
                'title': item.get('Title', ''),
                'status': 'success',
                'raw_data': {
                    'Item': item
                }
            }
            
            # Анализируем что получили
            print(f"   📋 Извлечено:")
            print(f"      Заголовок: {len(item.get('Title', ''))} символов")
            print(f"      Описание: {len(item.get('Description', ''))} символов")
            print(f"      Изображения: {len(item.get('Pictures', []))}")
            print(f"      Характеристики: {len(item.get('Attributes', []))}")
            print(f"      Физические параметры: {len(item.get('PhysicalParameters', {}))}")
            print(f"      Информация о весе: {len(item.get('ActualWeightInfo', {}))}")
            print(f"      Бренд: {item.get('BrandName', 'НЕТ')}")
            print(f"      Поставщик: {item.get('VendorName', 'НЕТ')}")
            
            return parsed_item
            
        except Exception as e:
            logging.error(f"Ошибка обработки ответа для {item_id}: {e}")
            return None
    
    def parse_batch(self, item_ids, batch_size=100):
        """Парсит батч товаров"""
        print(f"🚀 ПАРСИНГ БАТЧА: {len(item_ids)} товаров")
        print("=" * 60)
        
        results = []
        errors = 0
        
        for i, item_id in enumerate(item_ids):
            try:
                result = self.parse_product(item_id)
                if result:
                    results.append(result)
                    print(f"✅ [{i+1}/{len(item_ids)}] Товар {item_id} успешно спарсен")
                else:
                    errors += 1
                    print(f"❌ [{i+1}/{len(item_ids)}] Товар {item_id} не удалось спарсить")
                
                # Разделитель между товарами
                if i < len(item_ids) - 1:
                    print("-" * 40)
                    
            except Exception as e:
                errors += 1
                logging.error(f"Ошибка обработки товара {item_id}: {e}")
        
        print(f"\n📊 РЕЗУЛЬТАТ ПАРСИНГА БАТЧА:")
        print(f"   Успешно: {len(results)}")
        print(f"   Ошибок: {errors}")
        print(f"   Процент успеха: {len(results)/len(item_ids)*100:.1f}%")
        
        return results

def test_otapi_parser():
    """Тестирует OTAPI парсер"""
    print("🧪 ТЕСТИРОВАНИЕ OTAPI ПАРСЕРА")
    print("=" * 60)
    
    parser = OTAPIParser()
    
    # Тестовые ID (реальные товары с 1688.com)
    test_ids = [
        '631212367701',  # Металлическая открывашка из API примера
        '701929814435',  # Игрушка из рабочего chunk
        '733742816146'   # Еще один из рабочего chunk
    ]
    
    results = parser.parse_batch(test_ids)
    
    if results:
        print(f"\n📋 ПРИМЕР РЕЗУЛЬТАТА:")
        example = results[0]
        print(f"   ID: {example['id']}")
        print(f"   Title: {example['title'][:50]}...")
        
        # Проверяем структуру raw_data
        raw_data = example.get('raw_data', {})
        item = raw_data.get('Item', {})
        
        print(f"   Raw data keys: {list(item.keys())}")
        print(f"   Attributes count: {len(item.get('Attributes', []))}")
        print(f"   Pictures count: {len(item.get('Pictures', []))}")

if __name__ == "__main__":
    test_otapi_parser()
