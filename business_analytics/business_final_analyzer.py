#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ФИНАЛЬНЫЙ БИЗНЕС-АНАЛИЗАТОР
Чистый анализ для бизнеса с гауссовскими диапазонами по каждой категории
"""

import sqlite3
import pandas as pd
import numpy as np
import re
from pathlib import Path
from collections import defaultdict

class BusinessFinalAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Все категории
        self.final_categories = {
            'сумка': {
                'keywords': ['сумка', 'сумочка', 'bag', 'пакет', 'мешок', 'шоппер', 'торба', 'авоська'],
                'subcategories': {
                    'сумка_женская': ['женская сумка', 'дамская сумка', 'сумочка женская', 'клатч', 'ladies bag'],
                    'сумка_спорт': ['спортивная сумка', 'фитнес сумка', 'gym bag', 'sports bag', 'сумка спорт'],
                    'сумка_хозяйственная': ['хозяйственная сумка', 'авоська', 'шоппер', 'shopping bag'],
                    'сумка_холодильник': ['сумка холодильник', 'термосумка', 'изотермическая сумка', 'cooler bag'],
                }
            },
            'кружка': {
                'keywords': ['кружка', 'чашка', 'стакан', 'cup', 'mug', 'tumbler'],
                'subcategories': {
                    'кружка_термо': ['термокружка', 'термостакан', 'thermos mug', 'thermal cup', 'термо кружка'],
                    'кружка_керамическая': ['керамическая кружка', 'кружка керамика', 'ceramic mug'],
                    'кружка_металлическая': ['металлическая кружка', 'стальная кружка', 'steel mug'],
                }
            },
            'бутылка': {
                'keywords': ['бутылка', 'бутылочка', 'bottle', 'flask', 'фляга', 'бутылки'],
                'subcategories': {
                    'бутылка_детская': [
                        'детская бутылка', 'бутылочка детская', 'baby bottle', 'kids bottle', 'child bottle',
                        'бутылка для ребенка', 'детская бутылочка', 'бутылочка для малыша', 'бутылка детям',
                        'детский bottle', 'малыш бутылка', 'ребенок бутылка', 'дети бутылка',
                        'school bottle', 'детская питьевая', 'бутылочка для детей', 'бутылка школьная',
                    ],
                    'бутылка_спортивная': ['спортивная бутылка', 'фитнес бутылка', 'sports bottle'],
                }
            },
            'ручка': {
                'keywords': ['ручка', 'pen', 'карандаш', 'pencil', 'ручки'],
                'subcategories': {
                    'ручка_шариковая': ['шариковая ручка', 'ballpoint pen', 'ручка шариковая'],
                }
            },
            'рюкзак': {
                'keywords': ['рюкзак', 'backpack', 'рюкзачок', 'ранец', 'портфель школьный', 'ранец школьный'],
                'subcategories': {
                    'рюкзак_школьный': ['школьный рюкзак', 'ранец школьный', 'school backpack', 'студенческий рюкзак'],
                    'рюкзак_детский': ['детский рюкзак', 'рюкзачок детский', 'kids backpack'],
                }
            },
            'лампа': {
                'keywords': ['лампа', 'lamp', 'светильник', 'подсветка', 'ночник'],
                'subcategories': {
                    'лампа_ночная': ['ночная лампа', 'ночник', 'night light', 'светильник ночной'],
                    'лампа_настольная': ['настольная лампа', 'desk lamp'],
                }
            },
        }
        
        # Расширенные категории
        self.extended_categories = {
            'игрушка': ['игрушка', 'toy', 'плюшевая', 'игрушки', 'мягкая игрушка'],
            'набор': ['набор', 'set', 'комплект', 'наборы', 'сет'],
            'кабель': ['кабель', 'провод', 'cable', 'шнур', 'кабели', 'usb кабель'],
            'брелок': ['брелок', 'keychain', 'брелоки', 'брелочек'],
            'подставка': ['подставка', 'stand', 'держатель', 'подставки'],
            'чехол': ['чехол', 'case', 'футляр', 'обложка', 'чехлы'],
            'очки': ['очки', 'glasses', 'sunglasses', 'солнцезащитные очки'],
            'ластик': ['ластик', 'стерка', 'eraser', 'ластики'],
            'блокнот': ['блокнот', 'notebook', 'записная книжка', 'тетрадь'],
            'аккумулятор': ['аккумулятор', 'battery', 'повербанк', 'powerbank', 'power bank', 'пауэр'],
            'зарядное': ['зарядное', 'зарядка', 'charger', 'charging', 'зарядник'],
            'наушники': ['наушники', 'earphones', 'headphones', 'наушник', 'гарнитура'],
            'микрофон': ['микрофон', 'microphone', 'микрофоны', 'mic'],
            'мышь': ['мышь', 'мышка', 'mouse', 'компьютерная мышь'],
            'клавиатура': ['клавиатура', 'keyboard'],
            'флешка': ['флешка', 'флэш', 'usb', 'flash drive', 'пзу'],
            'колонка': ['колонка', 'speaker', 'динамик', 'акустика'],
            'вебкамера': ['вебкамера', 'webcam', 'камера', 'веб камера'],
            'принтер': ['принтер', 'printer', 'мини принтер'],
            'проектор': ['проектор', 'projector', 'мини проектор'],
            'футболка': ['футболка', 't-shirt', 'tshirt', 'майка', 'поло'],
            'толстовка': ['толстовка', 'свитшот', 'худи', 'hoodie'],
            'кепка': ['кепка', 'бейсболка', 'cap', 'hat', 'шапка'],
            'зонт': ['зонт', 'umbrella', 'зонтик'],
            'перчатки': ['перчатки', 'gloves', 'варежки'],
            'шарф': ['шарф', 'scarf', 'платок'],
            'носки': ['носки', 'socks', 'гольфы'],
            'дождевик': ['дождевик', 'raincoat', 'плащ'],
            'термос': ['термос', 'thermos', 'термокружка'],
            'тарелка': ['тарелка', 'plate', 'dish', 'тарелки'],
            'ложка': ['ложка', 'spoon', 'ложки'],
            'вилка': ['вилка', 'fork', 'вилки'],
            'нож': ['нож', 'knife', 'лезвие', 'ножи'],
            'чайник': ['чайник', 'teapot', 'kettle'],
            'контейнер': ['контейнер', 'container', 'ланч бокс', 'ланчбокс'],
            'открывашка': ['открывашка', 'открывалка', 'bottle opener'],
            'фонарь': ['фонарь', 'flashlight', 'фонарик', 'torch'],
            'свеча': ['свеча', 'candle', 'свечка'],
            'гирлянда': ['гирлянда', 'lights', 'освещение'],
            'таблетница': ['таблетница', 'pill box'],
            'градусник': ['градусник', 'термометр', 'thermometer'],
            'тонометр': ['тонометр', 'давление'],
            'маска_медицинская': ['медицинская маска', 'защитная маска', 'маска'],
            'антисептик': ['антисептик', 'sanitizer', 'дезинфектор'],
            'грелка': ['грелка', 'warmer', 'электрогрелка'],
            'антистресс': ['антистресс', 'сквиш', 'squish', 'стресс', 'попит'],
            'головоломка': ['кубик-рубик', 'кубик рубик', 'rubik', 'головоломка', 'спиннер'],
            'настольная_игра': ['настольная игра', 'board game', 'карты', 'домино'],
            'пазл': ['пазл', 'puzzle', 'мозаика'],
            'конструктор': ['конструктор', 'lego', 'лего'],
            'зеркало': ['зеркало', 'зеркальце', 'mirror'],
            'расческа': ['расческа', 'гребень', 'comb', 'brush'],
            'косметичка': ['косметичка', 'beauty bag', 'makeup bag', 'несессер'],
            'браслет': ['браслет', 'bracelet', 'фенечка'],
            'часы': ['часы', 'watch', 'clock', 'умные часы'],
            'стикеры': ['стикер', 'наклейка', 'sticker'],
            'штамп': ['штамп', 'печать', 'stamp'],
            'маркер': ['маркер', 'marker', 'фломастер'],
            'органайзер': ['органайзер', 'organizer'],
            'папка': ['папка', 'folder', 'файл'],
            'калькулятор': ['калькулятор', 'calculator'],
            'линейка': ['линейка', 'ruler', 'треугольник'],
            'степлер': ['степлер', 'stapler', 'скобы'],
            'дырокол': ['дырокол', 'hole punch'],
            'скрепки': ['скрепка', 'зажим', 'клип'],
            'пенал': ['пенал', 'pencil case'],
            'лента': ['лента', 'tape', 'скотч'],
            'бейдж': ['бейдж', 'badge', 'значок'],
            'плед': ['плед', 'blanket', 'покрывало'],
            'подушка': ['подушка', 'pillow', 'думка'],
            'полотенце': ['полотенце', 'towel'],
            'коврик': ['коврик', 'mat', 'pad'],
            'массажер': ['массажер', 'massager'],
            'эспандер': ['эспандер', 'expander', 'тренажер'],
            'гантель': ['гантель', 'dumbbell'],
            'скакалка': ['скакалка', 'jump rope'],
            'шейкер': ['шейкер', 'shaker'],
            'вентилятор': ['вентилятор', 'fan'],
            'увлажнитель': ['увлажнитель', 'humidifier', 'диффузор'],
            'селфи_палка': ['селфи палка', 'selfie stick'],
            'умные_часы': ['умные часы', 'smart watch'],
            'станция': ['станция', 'dock station'],
            'отвертка': ['отвертка', 'screwdriver'],
            'молоток': ['молоток', 'hammer'],
            'плоскогубцы': ['плоскогубцы', 'pliers'],
            'мультитул': ['мультитул', 'multitool'],
            'карабин': ['карабин', 'carabiner'],
            'шарик': ['шарик', 'balloon', 'воздушный шар'],
            'открытка': ['открытка', 'card'],
            'упаковка': ['упаковка', 'подарочная упаковка'],
            'снежный_шар': ['снежный шар', 'snow globe'],
            'календарь': ['календарь', 'calendar'],
            'ваза': ['ваза', 'vase'],
            'рамка': ['рамка', 'frame', 'фоторамка'],
            'статуэтка': ['статуэтка', 'figurine'],
            'шкатулка': ['шкатулка', 'jewelry box'],
            'подсвечник': ['подсвечник', 'candleholder'],
            'доска': ['доска', 'board', 'whiteboard'],
            'коффер': ['коффер', 'suitcase', 'чемодан'],
            'ремувка': ['ремувка', 'luggage tag'],
            'освежитель_воздуха': ['освежитель воздуха', 'ароматизатор'],
            'держатель_авто': ['держатель в машину', 'автодержатель'],
            'детские_товары': ['детский', 'детская', 'детское', 'ребенок', 'малыш', 'дети', 'kids', 'baby'],
            'соска': ['соска', 'пустышка', 'pacifier'],
            'слюнявчик': ['слюнявчик', 'нагрудник', 'bib'],
            'погремушка': ['погремушка', 'rattle'],
            'игрушка_животное': ['игрушка для собак', 'игрушка для кошек'],
            'миска_животное': ['миска для животных', 'pet bowl'],
            'ошейник': ['ошейник', 'collar', 'поводок'],
            'лейка': ['лейка', 'watering can'],
            'горшок': ['горшок', 'pot', 'кашпо'],
            'картхолдер': ['картхолдер', 'card holder'],
            'портмоне': ['портмоне', 'wallet', 'кошелек'],
            'чайная_пара': ['чайная пара', 'tea set'],
            'коробка': ['коробка', 'box'],
            'магнит': ['магнит', 'magnet'],
            'держатель': ['держатель', 'holder'],
            'метка': ['метка', 'tag', 'этикетка'],
            'резинка': ['резинка', 'elastic'],
            'веревка': ['веревка', 'rope', 'шнурок'],
            'мешочек': ['мешочек', 'pouch'],
            'карточка': ['карточка', 'card'],
            'служебные_исключить': ['образец', 'sample', 'лого', 'авиа', 'карго']
        }
    
    def load_products(self):
        """Загрузка товаров из БД"""
        query = """
        SELECT 
            p.id,
            p.original_title,
            p.title,
            pv.price_cny,
            pv.price_rub, 
            pv.price_usd,
            pv.moq,
            pv.quantity_in_box,
            pv.item_weight,
            pv.transport_tariff,
            pv.cargo_density
        FROM products p
        JOIN product_variants pv ON p.id = pv.product_id
        WHERE (p.original_title IS NOT NULL AND p.original_title != '') 
           OR (p.title IS NOT NULL AND p.title != '')
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Взвешенные названия: original_title×2 + title×3
        df['final_title'] = ''
        
        for idx, row in df.iterrows():
            parts = []
            
            if pd.notna(row['original_title']) and row['original_title'].strip():
                original = row['original_title'].strip().lower()
                original = re.sub(r'[^\w\s\-]', ' ', original)
                original = re.sub(r'\s+', ' ', original).strip()
                parts.extend([original] * 2)
            
            if pd.notna(row['title']) and row['title'].strip():
                title = row['title'].strip().lower()
                title = re.sub(r'[^\w\s\-]', ' ', title)
                title = re.sub(r'\s+', ' ', title).strip()
                parts.extend([title] * 3)
            
            df.at[idx, 'final_title'] = ' '.join(parts)
        
        # Средний запрашиваемый тираж
        df['avg_requested_tirage'] = df.apply(lambda row: 
            max(
                row['moq'] * 1.5 if pd.notna(row['moq']) else 0,
                row['quantity_in_box'] * 5 if pd.notna(row['quantity_in_box']) else 0
            ) if pd.notna(row['moq']) or pd.notna(row['quantity_in_box']) else None, axis=1)
        
        # Уникальные товары
        df_unique = df.groupby('original_title').agg({
            'final_title': 'first',
            'title': 'first',
            'price_cny': 'median',
            'price_rub': 'median',
            'price_usd': 'median',
            'moq': 'median',
            'avg_requested_tirage': 'median',
            'item_weight': 'median',
            'transport_tariff': 'median',
            'cargo_density': 'median'
        }).reset_index()
        
        return df_unique
    
    def categorize_products(self, df):
        """Категоризация товаров"""
        main_categorized = defaultdict(list)
        sub_categorized = defaultdict(lambda: defaultdict(list))
        excluded_count = 0
        uncategorized = []
        
        for _, row in df.iterrows():
            title = row['final_title']
            product_categorized = False
            
            # Исключения
            for exclude_word in self.extended_categories['служебные_исключить']:
                if exclude_word.lower() in title:
                    excluded_count += 1
                    product_categorized = True
                    break
            
            if product_categorized:
                continue
            
            # Иерархические категории
            for main_category, config in self.final_categories.items():
                # Подкатегории
                for sub_name, sub_keywords in config['subcategories'].items():
                    for keyword in sub_keywords:
                        if keyword.lower() in title:
                            sub_categorized[main_category][sub_name].append(row)
                            main_categorized[main_category].append(row)
                            product_categorized = True
                            break
                    if product_categorized:
                        break
                
                # Основные ключевые слова
                if not product_categorized:
                    for keyword in config['keywords']:
                        if keyword.lower() in title:
                            main_categorized[main_category].append(row)
                            product_categorized = True
                            break
                
                if product_categorized:
                    break
            
            # Расширенные категории
            if not product_categorized:
                for category, keywords in self.extended_categories.items():
                    if category == 'служебные_исключить':
                        continue
                    for keyword in keywords:
                        if keyword.lower() in title:
                            main_categorized[category].append(row)
                            product_categorized = True
                            break
                    if product_categorized:
                        break
            
            if not product_categorized:
                uncategorized.append(row)
        
        # Фильтруем подкатегории ≥20
        filtered_sub_categorized = defaultdict(lambda: defaultdict(list))
        for main_cat, subcats in sub_categorized.items():
            for sub_name, sub_products in subcats.items():
                if len(sub_products) >= 20:
                    filtered_sub_categorized[main_cat][sub_name] = sub_products
        
        return main_categorized, filtered_sub_categorized, uncategorized, excluded_count
    
    def calculate_category_gaussian_ranges(self, products_list):
        """Реальные 70% товаров для конкретной категории"""
        if len(products_list) == 0:
            return {}
        
        df_cat = pd.DataFrame(products_list)
        products_only = df_cat[df_cat['moq'] > 1]
        
        if len(products_only) < 3:  # Минимум 3 товара для статистики
            return {}
        
        ranges = {}
        metrics = {
            'price_rub': 'Цена (₽)',
            'price_cny': 'Цена (¥)', 
            'avg_requested_tirage': 'Тираж',
            'cargo_density': 'Плотность',
            'transport_tariff': 'Транспорт ($)'
        }
        
        for field, label in metrics.items():
            # КРИТИЧНО: исключаем нулевые, пустые и нереальные значения
            data = products_only[field].copy()
            
            # Убираем NaN
            data = data.dropna()
            
            # Убираем нули и отрицательные
            data = data[data > 0]
            
            # Специальные фильтры для конкретных метрик
            if field == 'cargo_density':
                # Плотность не может быть меньше 10 кг/м³ (даже пенопласт ~20 кг/м³)
                data = data[data >= 10.0]
            elif field == 'transport_tariff':
                # Транспорт не может быть меньше $0.1/кг
                data = data[data >= 0.1]
            elif field == 'price_rub':
                # Цена не может быть меньше 1 рубля
                data = data[data >= 1]
            elif field == 'price_cny':
                # Цена не может быть меньше 0.1 юаня
                data = data[data >= 0.1]
            elif field == 'avg_requested_tirage':
                # Тираж не может быть меньше 10 штук
                data = data[data >= 10]
            
            if len(data) >= 3:
                # РЕАЛЬНЫЕ 70% товаров: 15-й и 85-й процентили
                percentile_15 = data.quantile(0.15)  # 15% снизу
                percentile_85 = data.quantile(0.85)  # 85% сверху
                # Между ними ровно 70% товаров!
                
                mean = data.mean()
                std = data.std()
                
                ranges[field] = {
                    'label': label,
                    'mean': mean,
                    'std': std,
                    'lower_70': percentile_15,  # Реальный 15-й процентиль
                    'upper_70': percentile_85,  # Реальный 85-й процентиль
                    'min': data.min(),
                    'max': data.max(),
                    'median': data.median(),
                    'count': len(data),
                    'real_70_percent': True,  # Маркер что это реальные 70%
                    'original_count': len(products_only[field]),  # Для статистики
                    'filtered_out': len(products_only[field]) - len(data)  # Сколько исключили
                }
        
        return ranges
    
    def calculate_statistics_with_gaussian(self, main_categorized, sub_categorized):
        """Статистика с гауссовскими диапазонами для каждой категории"""
        results = []
        
        for main_category, products in main_categorized.items():
            if len(products) == 0:
                continue
                
            df_cat = pd.DataFrame(products)
            products_only = df_cat[df_cat['moq'] > 1]
            
            if len(products_only) == 0:
                continue
            
            # Реальные 70% товаров для категории
            gaussian_ranges = self.calculate_category_gaussian_ranges(products)
            
            # Медианы только для валидных данных (>0, не NaN)
            def safe_median(series, min_val=0):
                clean_data = series.dropna()
                clean_data = clean_data[clean_data > min_val]
                return clean_data.median() if len(clean_data) > 0 else None
            
            main_stats = {
                'тип': 'main',
                'категория': main_category,
                'родитель': '',
                'товары': len(products_only),
                'медиана_цены_cny': safe_median(products_only['price_cny'], 0.1),
                'медиана_цены_rub': safe_median(products_only['price_rub'], 1),
                'средний_тираж': safe_median(products_only['avg_requested_tirage'], 10),
                'медиана_веса': safe_median(products_only['item_weight'], 0.001),
                'медиана_плотности': safe_median(products_only['cargo_density'], 10.0),
                'медиана_транспорта_usd': safe_median(products_only['transport_tariff'], 0.1),
                'gaussian_ranges': gaussian_ranges
            }
            results.append(main_stats)
            
            # Подкатегории
            if main_category in sub_categorized:
                for sub_name, sub_products in sub_categorized[main_category].items():
                    df_sub = pd.DataFrame(sub_products)
                    sub_products_only = df_sub[df_sub['moq'] > 1]
                    
                    if len(sub_products_only) == 0:
                        continue
                    
                    sub_gaussian_ranges = self.calculate_category_gaussian_ranges(sub_products)
                    
                    sub_stats = {
                        'тип': 'sub',
                        'категория': sub_name,
                        'родитель': main_category,
                        'товары': len(sub_products_only),
                        'медиана_цены_cny': safe_median(sub_products_only['price_cny'], 0.1),
                        'медиана_цены_rub': safe_median(sub_products_only['price_rub'], 1),
                        'средний_тираж': safe_median(sub_products_only['avg_requested_tirage'], 10),
                        'медиана_веса': safe_median(sub_products_only['item_weight'], 0.001),
                        'медиана_плотности': safe_median(sub_products_only['cargo_density'], 10.0),
                        'медиана_транспорта_usd': safe_median(sub_products_only['transport_tariff'], 0.1),
                        'gaussian_ranges': sub_gaussian_ranges
                    }
                    results.append(sub_stats)
        
        # Сортировка по количеству товаров
        main_results = [r for r in results if r['тип'] == 'main']
        main_results.sort(key=lambda x: x['товары'], reverse=True)
        
        sorted_results = []
        for main_result in main_results:
            sorted_results.append(main_result)
            sub_results = [r for r in results if r['тип'] == 'sub' and r['родитель'] == main_result['категория']]
            sub_results.sort(key=lambda x: x['товары'], reverse=True)
            sorted_results.extend(sub_results)
        
        return sorted_results
    
    def run_business_analysis(self):
        """Запуск финального бизнес-анализа"""
        print("🎯 ФИНАЛЬНЫЙ БИЗНЕС-АНАЛИЗ")
        print("=" * 60)
        print("РЕАЛЬНЫЕ 70% товаров для каждой категории")
        print("Исключены нулевые и нереальные значения")
        print("Чистый бизнес-отчет без технических деталей")
        
        # Загружаем данные
        df = self.load_products()
        print(f"📊 Загружено {len(df):,} уникальных товаров")
        
        # Категоризация
        main_categorized, sub_categorized, uncategorized, excluded_count = self.categorize_products(df)
        
        total_categorized = sum(len(products) for products in main_categorized.values())
        total_analyzed = len(df) - excluded_count
        coverage = total_categorized / total_analyzed * 100 if total_analyzed > 0 else 0
        
        print(f"✅ Категоризировано: {total_categorized:,} товаров")
        print(f"📈 ПОКРЫТИЕ: {coverage:.1f}%")
        
        # Статистика с гауссовскими диапазонами
        stats = self.calculate_statistics_with_gaussian(main_categorized, sub_categorized)
        
        return stats, coverage, excluded_count, len(df)

def main():
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    analyzer = BusinessFinalAnalyzer(db_path)
    
    try:
        stats, coverage, excluded_count, total_products = analyzer.run_business_analysis()
        
        print(f"\n🎯 КАТЕГОРИИ С РЕАЛЬНЫМИ 70% ДИАПАЗОНАМИ:")
        print("-" * 120)
        
        for i, stat in enumerate(stats[:10], 1):
            type_icon = "📁" if stat['тип'] == 'main' else "📂"
            category_name = stat['категория'] if stat['тип'] == 'main' else f"└─ {stat['категория']}"
            
            print(f"{i:<3} {type_icon} {category_name:<30} {stat['товары']:<7} товаров")
            
            # Показываем реальные диапазоны для категории
            if stat['gaussian_ranges']:
                for field, ranges in stat['gaussian_ranges'].items():
                    if field == 'price_rub':
                        print(f"    💰 Цены: {ranges['lower_70']:.0f}-{ranges['upper_70']:.0f}₽ (медиана {ranges['median']:.0f}₽, валидных: {ranges['count']})")
                    elif field == 'avg_requested_tirage':
                        print(f"    📦 Тиражи: {ranges['lower_70']:.0f}-{ranges['upper_70']:.0f} шт (медиана {ranges['median']:.0f}, валидных: {ranges['count']})")
                    elif field == 'cargo_density':
                        print(f"    🏗️ Плотность: {ranges['lower_70']:.1f}-{ranges['upper_70']:.1f} кг/м³ (медиана {ranges['median']:.1f}, валидных: {ranges['count']})")
            print()
        
        print(f"🎉 ИТОГ: {len([s for s in stats if s['тип'] == 'main'])} категорий с реальными 70% диапазонами товаров")
        
        return stats, coverage
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analyzer.conn.close()

if __name__ == "__main__":
    main()
