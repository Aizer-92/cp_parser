#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УМНЫЙ ПОИСК ТОВАРОВ ДЛЯ КАТЕГОРИЙ ИЗ CSV
Улучшенный алгоритм поиска и заполнения данных
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from business_final_analyzer import BusinessFinalAnalyzer
import re

class SmartCategoryMatcher:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Расширенный словарь синонимов и ключевых слов
        self.keyword_mapping = {
            'картхолдер': ['card', 'holder', 'карт', 'визитка', 'кредитка', 'пластик'],
            'кардхолдер': ['card', 'holder', 'карт', 'визитка', 'кредитка', 'пластик'],
            'рюкзак': ['backpack', 'bag', 'сумка', 'спорт', 'школ', 'туризм'],
            'поясная': ['belt', 'waist', 'пояс', 'бан', 'сумка'],
            'шоппер': ['shopping', 'bag', 'сумка', 'покуп', 'торг'],
            'органайзер': ['organizer', 'органайз', 'порядок', 'хранение'],
            'косметичка': ['cosmetic', 'косметик', 'макияж', 'beauty'],
            'пенал': ['pencil', 'case', 'канцелярия', 'школ'],
            'термосумка': ['thermal', 'термо', 'холод', 'изотерм'],
            'авоська': ['mesh', 'сетка', 'сумка', 'продукт'],
            'чехол': ['case', 'cover', 'защит', 'phone', 'телефон'],
            'стикер': ['sticker', 'наклейка', 'этикетка', 'label'],
            'наклейка': ['sticker', 'этикетка', 'label', 'vinyl'],
            'ежедневник': ['diary', 'planner', 'планинг', 'notebook'],
            'блокнот': ['notebook', 'notepad', 'записная', 'тетрадь'],
            'носки': ['socks', 'sock', 'чулочно', 'хлопок'],
            'шарф': ['scarf', 'платок', 'neck', 'шея'],
            'платок': ['scarf', 'handkerchief', 'шарф', 'шея'],
            'кепка': ['cap', 'hat', 'бейсболка', 'головной'],
            'бейсболка': ['cap', 'hat', 'кепка', 'baseball'],
            'футболка': ['t-shirt', 'tshirt', 'shirt', 'майка'],
            'худи': ['hoodie', 'sweatshirt', 'толстовка', 'капюшон'],
            'толстовка': ['hoodie', 'sweatshirt', 'худи', 'кофта'],
            'шапка': ['hat', 'beanie', 'cap', 'головной'],
            'плед': ['blanket', 'покрывало', 'одеяло'],
            'полотенце': ['towel', 'банное', 'махровое'],
            'ланчбокс': ['lunch', 'box', 'контейнер', 'еда'],
            'таблетница': ['pill', 'box', 'таблетки', 'лекарство'],
            'термос': ['thermos', 'thermal', 'термо'],
            'термокружка': ['thermal', 'mug', 'термо', 'кружка'],
            'термостакан': ['thermal', 'cup', 'термо', 'стакан'],
            'блендер': ['blender', 'миксер', 'измельчитель'],
            'грелка': ['warmer', 'heat', 'нагреватель'],
            'массажер': ['massage', 'массаж', 'релакс'],
            'наушники': ['headphone', 'earphone', 'наушник'],
            'пауэрбанк': ['power', 'bank', 'аккумулятор', 'зарядка'],
            'повербанк': ['power', 'bank', 'аккумулятор', 'зарядка'],
            'докстанция': ['dock', 'station', 'подставка', 'зарядка'],
            'увлажнитель': ['humidifier', 'увлажн', 'воздух'],
            'проектор': ['projector', 'проекция', 'экран'],
            'светильник': ['light', 'lamp', 'освещение'],
            'ночник': ['night', 'light', 'детский', 'спальня'],
            'значок': ['badge', 'pin', 'знак', 'эмблема'],
            'магнит': ['magnet', 'магнитный', 'холодильник'],
            'ремувка': ['remover', 'средство', 'cleaning'],
            'флешка': ['usb', 'flash', 'drive', 'накопитель'],
            'шнурок': ['cord', 'string', 'lace', 'веревка'],
            'ланьярд': ['lanyard', 'лента', 'шнур'],
            'подушка': ['pillow', 'cushion', 'подголовник'],
            'маска': ['mask', 'сна', 'глаз', 'sleep'],
            'елочная': ['christmas', 'новый', 'год', 'праздник'],
            'игрушка': ['toy', 'детская', 'игра'],
            'снежный': ['snow', 'globe', 'шар'],
            'конструктор': ['constructor', 'lego', 'building'],
            'мягкая': ['soft', 'плюшевая', 'teddy'],
            'пазл': ['puzzle', 'головоломка'],
            'головоломка': ['puzzle', 'brain', 'логика'],
            'шашки': ['checkers', 'игра', 'настольная'],
            'шахматы': ['chess', 'игра', 'настольная'],
            'круг': ['ring', 'надувной', 'плавание'],
            'резинка': ['rubber', 'elastic', 'фитнес'],
            'скакалка': ['rope', 'jump', 'прыжки'],
            'зонт': ['umbrella', 'дождь', 'защита'],
            'коробка': ['box', 'упаковка', 'картон'],
            'автовизитка': ['business', 'card', 'визитка'],
            'фотоаппарат': ['camera', 'photo', 'фото'],
            'тетрис': ['tetris', 'игра', 'головоломка'],
            'карандаш': ['pencil', 'канцелярия', 'рисование'],
            'попсокет': ['popsocket', 'grip', 'держатель'],
            'обложка': ['cover', 'passport', 'документ'],
            'чемодан': ['suitcase', 'luggage', 'багаж'],
            'статуэтка': ['figurine', 'статуя', 'награда'],
            'награда': ['award', 'prize', 'статуэтка'],
            'панама': ['panama', 'hat', 'головной'],
            'держатель': ['holder', 'stand', 'подставка'],
            'гирлянда': ['garland', 'lights', 'освещение'],
            'шлем': ['helmet', 'защитный', 'голова']
        }
    
    def get_search_keywords(self, category_name):
        """Получение ключевых слов для поиска"""
        category_lower = category_name.lower().strip()
        
        # Разбиваем название на части
        parts = re.split(r'[,\-\s]+', category_lower)
        
        keywords = []
        for part in parts:
            part = part.strip()
            if len(part) < 3:  # Игнорируем короткие слова
                continue
                
            keywords.append(part)
            
            # Добавляем синонимы
            if part in self.keyword_mapping:
                keywords.extend(self.keyword_mapping[part])
        
        # Убираем дубликаты и короткие слова
        keywords = list(set([k for k in keywords if len(k) >= 3]))
        return keywords
    
    def search_products_for_category(self, category_name, limit=100):
        """Умный поиск товаров для категории"""
        keywords = self.get_search_keywords(category_name)
        
        if not keywords:
            return pd.DataFrame()
        
        # Строим запрос с разными стратегиями поиска
        search_conditions = []
        
        # 1. Поиск по основным словам
        for keyword in keywords[:5]:  # Берем первые 5 ключевых слов
            search_conditions.append(f"(p.title LIKE '%{keyword}%' OR p.original_title LIKE '%{keyword}%')")
        
        # 2. Поиск по комбинациям слов (для составных категорий)
        if len(keywords) >= 2:
            for i in range(len(keywords)-1):
                search_conditions.append(
                    f"(p.title LIKE '%{keywords[i]}%' AND p.title LIKE '%{keywords[i+1]}%')"
                )
        
        where_clause = ' OR '.join(search_conditions)
        
        query = f"""
        SELECT 
            p.id,
            p.original_title,
            p.title,
            pv.price_cny,
            pv.price_rub, 
            pv.price_usd,
            pv.moq,
            pv.item_weight,
            pv.transport_tariff,
            pv.cargo_density,
            pv.quantity_in_box
        FROM products p
        JOIN product_variants pv ON p.id = pv.product_id
        WHERE ({where_clause})
            AND pv.moq > 1
            AND p.title NOT LIKE '%sample%'
            AND p.title NOT LIKE '%образец%'
            AND p.title NOT LIKE '%logo%'
            AND p.title NOT LIKE '%логотип%'
        ORDER BY pv.price_rub DESC
        LIMIT {limit}
        """
        
        try:
            df_found = pd.read_sql_query(query, self.conn)
            
            # Фильтруем результаты по релевантности
            if len(df_found) > 0:
                # Добавляем счетчик релевантности
                df_found['relevance_score'] = 0
                
                for keyword in keywords:
                    mask_title = df_found['title'].str.contains(keyword, case=False, na=False)
                    mask_original = df_found['original_title'].str.contains(keyword, case=False, na=False)
                    df_found.loc[mask_title | mask_original, 'relevance_score'] += 1
                
                # Сортируем по релевантности и берем лучшие результаты
                df_found = df_found.sort_values('relevance_score', ascending=False)
                df_found = df_found.head(50)  # Ограничиваем 50 лучшими результатами
                
            return df_found
            
        except Exception as e:
            print(f"❌ Ошибка поиска для '{category_name}': {e}")
            return pd.DataFrame()
    
    def calculate_ranges_for_products(self, products_df):
        """Расчет диапазонов для найденных товаров"""
        if len(products_df) < 3:
            return {}
        
        # Фильтруем продукты (исключаем образцы)
        products_only = products_df[products_df['moq'] > 1].copy()
        
        if len(products_only) < 3:
            return {}
        
        # Добавляем расчетные поля
        products_only.loc[:, 'avg_requested_tirage'] = products_only['moq'] * 2
        
        ranges = {}
        metrics = {
            'price_rub': 'Цена (₽)',
            'price_cny': 'Цена (¥)', 
            'avg_requested_tirage': 'Тираж',
            'cargo_density': 'Плотность',
            'transport_tariff': 'Транспорт ($)'
        }
        
        for field, label in metrics.items():
            data = products_only[field].copy()
            
            # Убираем NaN
            data = data.dropna()
            
            # Убираем нули и отрицательные
            data = data[data > 0]
            
            # Специальные фильтры
            if field == 'cargo_density':
                data = data[data >= 10.0]
            elif field == 'transport_tariff':
                data = data[data >= 0.1]
            elif field == 'price_rub':
                data = data[data >= 1]
            elif field == 'price_cny':
                data = data[data >= 0.1]
            elif field == 'avg_requested_tirage':
                data = data[data >= 10]
            
            if len(data) >= 3:
                percentile_15 = data.quantile(0.15)
                percentile_85 = data.quantile(0.85)
                
                ranges[field] = {
                    'label': label,
                    'mean': data.mean(),
                    'std': data.std(),
                    'lower_70': percentile_15,
                    'upper_70': percentile_85,
                    'min': data.min(),
                    'max': data.max(),
                    'median': data.median(),
                    'count': len(data)
                }
        
        return ranges
    
    def enhance_csv_categories(self):
        """Поиск и заполнение товаров для категорий из CSV"""
        
        print("🔍 УМНЫЙ ПОИСК ТОВАРОВ ДЛЯ КАТЕГОРИЙ ИЗ CSV")
        print("=" * 60)
        
        # Читаем категории только из CSV
        csv_only = pd.read_excel('COMPREHENSIVE_DATA_ANALYSIS.xlsx', sheet_name='🟠_Только_CSV')
        print(f"📊 Найдено {len(csv_only)} категорий только из CSV")
        
        enhanced_categories = []
        successful_matches = 0
        
        for i, row in csv_only.iterrows():
            category_name = row['Категория']
            print(f"\n🔍 Поиск товаров для '{category_name}'...")
            
            # Ищем товары
            products_df = self.search_products_for_category(category_name)
            
            if len(products_df) >= 5:  # Минимум 5 товаров
                print(f"  ✅ Найдено {len(products_df)} товаров")
                
                # Рассчитываем диапазоны
                ranges = self.calculate_ranges_for_products(products_df)
                
                # Создаем обновленную запись
                enhanced_row = row.copy()
                enhanced_row['Товаров'] = len(products_df)
                enhanced_row['Полнота_данных'] = "🟢 ПОЛНЫЕ ДАННЫЕ"
                enhanced_row['Есть_диапазоны_БД'] = True
                enhanced_row['Количество_диапазонов'] = len(ranges)
                
                # Добавляем медианы
                enhanced_row['Медиана_цены_руб'] = products_df['price_rub'].median() if not products_df['price_rub'].isna().all() else None
                enhanced_row['Медиана_цены_юань'] = products_df['price_cny'].median() if not products_df['price_cny'].isna().all() else None
                enhanced_row['Медиана_тиража'] = products_df['moq'].median() if not products_df['moq'].isna().all() else None
                enhanced_row['Медиана_плотности'] = products_df['cargo_density'].median() if not products_df['cargo_density'].isna().all() else None
                enhanced_row['Медиана_транспорта'] = products_df['transport_tariff'].median() if not products_df['transport_tariff'].isna().all() else None
                
                # Добавляем диапазоны
                for field, data in ranges.items():
                    if field == 'price_rub':
                        enhanced_row['Цена_руб_мин'] = data['lower_70']
                        enhanced_row['Цена_руб_макс'] = data['upper_70']
                        enhanced_row['Цена_руб_медиана'] = data['median']
                        enhanced_row['Цена_руб_среднее'] = data['mean']
                        enhanced_row['Цена_руб_стд'] = data['std']
                        enhanced_row['Цена_руб_количество'] = data['count']
                    elif field == 'price_cny':
                        enhanced_row['Цена_юань_мин'] = data['lower_70']
                        enhanced_row['Цена_юань_макс'] = data['upper_70']
                        enhanced_row['Цена_юань_медиана'] = data['median']
                        enhanced_row['Цена_юань_среднее'] = data['mean']
                        enhanced_row['Цена_юань_стд'] = data['std']
                        enhanced_row['Цена_юань_количество'] = data['count']
                    elif field == 'avg_requested_tirage':
                        enhanced_row['Тираж_мин'] = data['lower_70']
                        enhanced_row['Тираж_макс'] = data['upper_70']
                        enhanced_row['Тираж_медиана'] = data['median']
                        enhanced_row['Тираж_среднее'] = data['mean']
                        enhanced_row['Тираж_стд'] = data['std']
                        enhanced_row['Тираж_количество'] = data['count']
                    elif field == 'cargo_density':
                        enhanced_row['Плотность_мин'] = data['lower_70']
                        enhanced_row['Плотность_макс'] = data['upper_70']
                        enhanced_row['Плотность_медиана'] = data['median']
                        enhanced_row['Плотность_среднее'] = data['mean']
                        enhanced_row['Плотность_стд'] = data['std']
                        enhanced_row['Плотность_количество'] = data['count']
                    elif field == 'transport_tariff':
                        enhanced_row['Транспорт_мин'] = data['lower_70']
                        enhanced_row['Транспорт_макс'] = data['upper_70']
                        enhanced_row['Транспорт_медиана'] = data['median']
                        enhanced_row['Транспорт_среднее'] = data['mean']
                        enhanced_row['Транспорт_стд'] = data['std']
                        enhanced_row['Транспорт_количество'] = data['count']
                
                enhanced_categories.append(enhanced_row)
                successful_matches += 1
                
            else:
                print(f"  ❌ Найдено только {len(products_df)} товаров (минимум 5)")
        
        print(f"\n🎉 РЕЗУЛЬТАТ: {successful_matches} из {len(csv_only)} категорий успешно дополнено")
        
        if successful_matches > 0:
            # Создаем DataFrame с дополненными категориями
            df_enhanced = pd.DataFrame(enhanced_categories)
            
            # Сохраняем результат
            output_file = Path(__file__).parent / "ENHANCED_CSV_CATEGORIES.xlsx"
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df_enhanced.to_excel(writer, sheet_name='Дополненные_категории', index=False)
                
                # Статистика успешности
                success_stats = pd.DataFrame([{
                    'Всего_категорий_CSV': len(csv_only),
                    'Успешно_дополнено': successful_matches,
                    'Процент_успеха': (successful_matches / len(csv_only)) * 100,
                    'Товаров_добавлено': df_enhanced['Товаров'].sum(),
                    'Средне_товаров': df_enhanced['Товаров'].mean()
                }])
                success_stats.to_excel(writer, sheet_name='Статистика_дополнения', index=False)
            
            print(f"✅ Дополненные категории сохранены: {output_file}")
            return df_enhanced
        
        return pd.DataFrame()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    
    matcher = SmartCategoryMatcher(db_path)
    enhanced_df = matcher.enhance_csv_categories()
    
    return enhanced_df

if __name__ == "__main__":
    main()
