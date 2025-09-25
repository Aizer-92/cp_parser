#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЧИСТЫЙ АНАЛИЗ БД - без искажений
- Транспорт как есть из БД (в $)
- Без расчета оборота
- Фокус на БД, CSV только для сравнения
- Гауссовские диапазоны (70% значений)
"""

import sqlite3
import pandas as pd
import numpy as np
import re
from pathlib import Path
from collections import defaultdict, Counter
# Убираем scipy - не используется

class PureDBAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Все категории (копируем из предыдущего анализатора)
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
                        'бутылка kindergarten', 'nursery bottle', 'toddler bottle', 'детский сад бутылка',
                        'маленькая бутылка', 'мини бутылка', 'small bottle', 'bottle small', 'mini bottle',
                        '300ml бутылка', '250ml бутылка', '200ml bottle', 'compact bottle',
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
        
        # Все остальные категории
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
    
    def load_products_pure(self):
        """Загрузка БЕЗ ИСКАЖЕНИЙ - как есть в БД"""
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
            pv.transport_tariff,  -- КАК ЕСТЬ в БД (в $)
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
            'transport_tariff': 'median',  # КАК ЕСТЬ
            'cargo_density': 'median'
        }).reset_index()
        
        return df_unique
    
    def calculate_gaussian_ranges(self, df):
        """Гауссовские диапазоны для 70% значений"""
        ranges = {}
        
        metrics = {
            'price_rub': 'Цена в рублях',
            'price_cny': 'Цена в юанях', 
            'avg_requested_tirage': 'Средний тираж',
            'cargo_density': 'Плотность',
            'transport_tariff': 'Транспорт ($)'
        }
        
        for field, label in metrics.items():
            data = df[field].dropna()
            if len(data) > 0:
                mean = data.mean()
                std = data.std()
                
                # 70% = ±1.04 стандартных отклонения (для нормального распределения)
                # P(-1.04 < Z < 1.04) ≈ 0.70
                z_score = 1.04
                lower = mean - z_score * std
                upper = mean + z_score * std
                
                ranges[field] = {
                    'label': label,
                    'mean': mean,
                    'std': std,
                    'lower_70': max(0, lower),  # не может быть отрицательным
                    'upper_70': upper,
                    'min': data.min(),
                    'max': data.max(),
                    'median': data.median()
                }
        
        return ranges
    
    def pure_categorization(self, df):
        """Чистая категоризация без искажений"""
        print("\n🎯 ЧИСТЫЙ АНАЛИЗ БД:")
        print("=" * 60)
        print("• Транспорт как есть из БД (в $)")
        print("• Без расчета оборота")
        print("• Фокус на структуре БД")
        print("• Гауссовские диапазоны (70% значений)")
        
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
        
        total_categorized = sum(len(products) for products in main_categorized.values())
        total_analyzed = len(df) - excluded_count
        coverage = total_categorized / total_analyzed * 100 if total_analyzed > 0 else 0
        
        print(f"✅ Категоризировано: {total_categorized:,} товаров")
        print(f"🗑️ Исключено служебных: {excluded_count:,} товаров")
        print(f"❓ Без категории: {len(uncategorized):,} товаров")
        print(f"📈 ПОКРЫТИЕ (без служебных): {coverage:.1f}%")
        
        return main_categorized, filtered_sub_categorized, uncategorized, coverage, excluded_count
    
    def calculate_pure_statistics(self, main_categorized, sub_categorized):
        """Статистика БЕЗ оборота"""
        results = []
        
        for main_category, products in main_categorized.items():
            if len(products) == 0:
                continue
                
            df_cat = pd.DataFrame(products)
            
            # Исключаем образцы
            products_only = df_cat[df_cat['moq'] > 1]
            
            if len(products_only) == 0:
                continue
            
            main_stats = {
                'тип': 'main',
                'категория': main_category,
                'родитель': '',
                'товары': len(products_only),
                'медиана_цены_cny': products_only['price_cny'].median() if not products_only['price_cny'].isna().all() else None,
                'медиана_цены_rub': products_only['price_rub'].median() if not products_only['price_rub'].isna().all() else None,
                'средний_тираж': products_only['avg_requested_tirage'].median() if not products_only['avg_requested_tirage'].isna().all() else None,
                'медиана_веса': products_only['item_weight'].median() if not products_only['item_weight'].isna().all() else None,
                'медиана_плотности': products_only['cargo_density'].median() if not products_only['cargo_density'].isna().all() else None,
                'медиана_транспорта_usd': products_only['transport_tariff'].median() if not products_only['transport_tariff'].isna().all() else None,
            }
            results.append(main_stats)
            
            # Подкатегории
            if main_category in sub_categorized:
                for sub_name, sub_products in sub_categorized[main_category].items():
                    df_sub = pd.DataFrame(sub_products)
                    sub_products_only = df_sub[df_sub['moq'] > 1]
                    
                    if len(sub_products_only) == 0:
                        continue
                    
                    sub_stats = {
                        'тип': 'sub',
                        'категория': sub_name,
                        'родитель': main_category,
                        'товары': len(sub_products_only),
                        'медиана_цены_cny': sub_products_only['price_cny'].median() if not sub_products_only['price_cny'].isna().all() else None,
                        'медиана_цены_rub': sub_products_only['price_rub'].median() if not sub_products_only['price_rub'].isna().all() else None,
                        'средний_тираж': sub_products_only['avg_requested_tirage'].median() if not sub_products_only['avg_requested_tirage'].isna().all() else None,
                        'медиана_веса': sub_products_only['item_weight'].median() if not sub_products_only['item_weight'].isna().all() else None,
                        'медиана_плотности': sub_products_only['cargo_density'].median() if not sub_products_only['cargo_density'].isna().all() else None,
                        'медиана_транспорта_usd': sub_products_only['transport_tariff'].median() if not sub_products_only['transport_tariff'].isna().all() else None,
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
    
    def run_pure_analysis(self):
        """Запуск чистого анализа БД"""
        print("🎯 ЧИСТЫЙ АНАЛИЗ БАЗЫ ДАННЫХ")
        print("=" * 60)
        print("Без искажений:")
        print("• Транспорт: как есть в БД (в $)")
        print("• Без расчета оборота")
        print("• Фокус на структуре БД")
        print("• Гауссовские диапазоны (70%)")
        
        # Загружаем данные
        df = self.load_products_pure()
        print(f"📊 Загружено {len(df):,} уникальных товаров")
        
        # Гауссовские диапазоны
        ranges = self.calculate_gaussian_ranges(df)
        print(f"\n📊 ГАУССОВСКИЕ ДИАПАЗОНЫ (70% значений):")
        print("-" * 80)
        for field, info in ranges.items():
            print(f"{info['label']:15} │ "
                  f"Среднее: {info['mean']:8.1f} │ "
                  f"70% диапазон: {info['lower_70']:8.1f} - {info['upper_70']:8.1f} │ "
                  f"Медиана: {info['median']:8.1f}")
        
        # Категоризация
        main_categorized, sub_categorized, uncategorized, coverage, excluded_count = self.pure_categorization(df)
        
        # Статистика
        stats = self.calculate_pure_statistics(main_categorized, sub_categorized)
        
        return stats, coverage, excluded_count, len(df), ranges

def main():
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    analyzer = PureDBAnalyzer(db_path)
    
    try:
        stats, coverage, excluded_count, total_products, ranges = analyzer.run_pure_analysis()
        
        print(f"\n🎯 ВСЕ КАТЕГОРИИ БД (СОРТИРОВКА ПО КОЛИЧЕСТВУ):")
        print("-" * 120)
        print(f"{'№':<3} {'Тип':<4} {'Категория':<35} {'Товары':<7} {'CNY':<8} {'Рубли':<10} {'Тираж':<8} {'Плотн.':<7} {'Транс.$':<8}")
        print("-" * 120)
        
        for i, stat in enumerate(stats, 1):
            type_icon = "📁" if stat['тип'] == 'main' else "📂"
            category_name = stat['категория'] if stat['тип'] == 'main' else f"└─ {stat['категория']}"
            
            price_cny = f"{stat['медиана_цены_cny']:.1f}" if stat['медиана_цены_cny'] else "-"
            price_rub = f"{stat['медиана_цены_rub']:.0f}" if stat['медиана_цены_rub'] else "-"
            tirage = f"{stat['средний_тираж']:.0f}" if stat['средний_тираж'] else "-"
            density = f"{stat['медиана_плотности']:.1f}" if stat['медиана_плотности'] else "-"
            transport = f"{stat['медиана_транспорта_usd']:.1f}" if stat['медиана_транспорта_usd'] else "-"
            
            print(f"{i:<3} {type_icon:<4} {category_name:<35} {stat['товары']:<7} {price_cny:<8} {price_rub:<10} {tirage:<8} {density:<7} {transport:<8}")
        
        print(f"\n🎉 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print(f"  📈 ПОКРЫТИЕ: {coverage:.1f}%")
        print(f"  🗑️ Исключено служебных: {excluded_count:,}")
        print(f"  🏷️ Всего категорий: {len([s for s in stats if s['тип'] == 'main'])}")
        print(f"  📊 Общий объем: {total_products:,} товаров")
        print(f"  🎯 Сортировка по количеству товаров")
        print(f"  💰 Транспорт как есть из БД (в $)")
        print(f"  📏 Без искажений и расчета оборота")
        
        return stats, coverage, ranges
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analyzer.conn.close()

if __name__ == "__main__":
    main()
