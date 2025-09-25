#!/usr/bin/env python3
"""
Тестовый парсер для 1688.com
"""
import requests
import time
import random
import json
from urllib.parse import urlparse
import re

class Test1688Parser:
    """Тестовый парсер для 1688.com"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def parse_product(self, item_id):
        """Парсит товар по ID"""
        try:
            print(f"🔍 Парсинг товара {item_id}...")
            
            # Формируем URL
            url = f'https://detail.1688.com/offer/{item_id}.html'
            
            # Заголовки
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Задержка
            time.sleep(random.uniform(1, 2))
            
            # Запрос
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Успешно получен ответ для {item_id}")
                
                # Анализируем ответ
                content = response.text
                
                # Ищем данные в HTML
                result = self.extract_data_from_html(content, item_id)
                
                return result
            else:
                print(f"❌ HTTP {response.status_code} для {item_id}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка парсинга {item_id}: {e}")
            return None
    
    def extract_data_from_html(self, html_content, item_id):
        """Извлекает данные из HTML"""
        try:
            # Базовая структура
            result = {
                'id': f'abb-{item_id}',
                'item_id': item_id,
                'url': f'https://detail.1688.com/offer/{item_id}.html',
                'title': '',
                'status': 'success',
                'raw_data': {
                    'Item': {
                        'ItemId': item_id,
                        'Title': '',
                        'Description': '',
                        'MainPictureUrl': '',
                        'Pictures': [],
                        'Attributes': [],
                        'PhysicalParameters': {},
                        'ActualWeightInfo': {},
                        'BrandName': '',
                        'VendorName': '',
                        'Price': {}
                    }
                }
            }
            
            # Ищем заголовок
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                result['title'] = title
                result['raw_data']['Item']['Title'] = title
            
            # Ищем описание
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html_content, re.IGNORECASE)
            if desc_match:
                description = desc_match.group(1).strip()
                result['raw_data']['Item']['Description'] = description
            
            # Ищем изображения
            img_matches = re.findall(r'<img[^>]*src="([^"]*)"', html_content)
            if img_matches:
                # Фильтруем изображения 1688.com
                valid_images = [img for img in img_matches if 'alicdn.com' in img or '1688.com' in img]
                if valid_images:
                    result['raw_data']['Item']['MainPictureUrl'] = valid_images[0]
                    result['raw_data']['Item']['Pictures'] = [{'Url': img} for img in valid_images[1:5]]  # Первые 5
            
            # Ищем цену
            price_match = re.search(r'price["\']?\s*:\s*["\']?([0-9.]+)', html_content, re.IGNORECASE)
            if price_match:
                price = price_match.group(1)
                result['raw_data']['Item']['Price'] = {'ConvertedPrice': price}
            
            # Ищем бренд
            brand_match = re.search(r'brand["\']?\s*:\s*["\']?([^"\']+)', html_content, re.IGNORECASE)
            if brand_match:
                brand = brand_match.group(1).strip()
                result['raw_data']['Item']['BrandName'] = brand
            
            print(f"   📋 Извлечено: заголовок, {len(result['raw_data']['Item']['Pictures'])} изображений")
            return result
            
        except Exception as e:
            print(f"   ❌ Ошибка извлечения данных: {e}")
            return None

def test_parser():
    """Тестирует парсер"""
    print("🧪 ТЕСТИРОВАНИЕ ПАРСЕРА 1688.COM")
    print("=" * 60)
    
    parser = Test1688Parser()
    
    # Тестовые ID (реальные товары с 1688.com)
    test_ids = [
        '701929814435',  # Игрушка из рабочего chunk
        '733742816146',  # Еще один из рабочего chunk
        '123456789'      # Несуществующий для теста ошибок
    ]
    
    results = []
    
    for item_id in test_ids:
        result = parser.parse_product(item_id)
        if result:
            results.append(result)
            print(f"✅ Товар {item_id} успешно спарсен")
        else:
            print(f"❌ Товар {item_id} не удалось спарсить")
        
        print("-" * 40)
    
    print(f"📊 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:")
    print(f"   Успешно: {len(results)}")
    print(f"   Неудачно: {len(test_ids) - len(results)}")
    
    if results:
        print(f"\n📋 ПРИМЕР РЕЗУЛЬТАТА:")
        example = results[0]
        print(f"   ID: {example['id']}")
        print(f"   Title: {example['title'][:50]}...")
        print(f"   Images: {len(example['raw_data']['Item']['Pictures'])}")
        print(f"   Description length: {len(example['raw_data']['Item']['Description'])}")

if __name__ == "__main__":
    test_parser()
