#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОБЪЕДИНЕНИЕ ДАННЫХ С ПОПУЛЯРНЫМИ КАТЕГОРИЯМИ
Дополнение таблицы диапазонов информацией из CSV файла
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from business_final_analyzer import BusinessFinalAnalyzer
import re

def normalize_category_name(name):
    """Нормализация названия категории для сопоставления"""
    if pd.isna(name) or name == '':
        return ''
    
    name = str(name).lower().strip()
    
    # Убираем лишние символы
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    
    # Замены для лучшего сопоставления
    replacements = {
        'картхолдер': 'картхолдер',
        'кардхолдер': 'картхолдер', 
        'рюкзак': 'рюкзак',
        'сумка': 'сумка',
        'шоппер': 'сумка',
        'органайзер': 'органайзер',
        'косметичка': 'косметичка',
        'пенал': 'пенал',
        'термосумка': 'термосумка',
        'авоська': 'авоська',
        'стикер': 'наклейка',
        'наклейка': 'наклейка',
        'ежедневник': 'ежедневник',
        'блокнот': 'блокнот',
        'носки': 'носки',
        'шарф': 'шарф',
        'платок': 'шарф',
        'кепка': 'кепка',
        'бейсболка': 'кепка',
        'футболка': 'футболка',
        'худи': 'худи',
        'толстовка': 'худи',
        'шапка': 'шапка',
        'плед': 'плед',
        'полотенце': 'полотенце',
        'ланчбокс': 'ланчбокс',
        'бутылка': 'бутылка',
        'стакан': 'бутылка',
        'термос': 'термос',
        'термокружка': 'термос',
        'термостакан': 'термос',
        'посуда': 'посуда',
        'тарелка': 'посуда',
        'кружка': 'кружка',
        'блендер': 'блендер',
        'грелка': 'грелка',
        'мышь': 'мышь',
        'массажер': 'массажер',
        'колонка': 'колонка',
        'наушник': 'наушник',
        'пауэрбанк': 'пауэрбанк',
        'повербанк': 'пауэрбанк',
        'докстанция': 'докстанция',
        'увлажнитель': 'увлажнитель',
        'лампа': 'лампа',
        'светильник': 'лампа',
        'ночник': 'лампа',
        'фонарик': 'фонарик',
        'значок': 'значок',
        'брелок': 'брелок',
        'магнит': 'магнит',
        'флешка': 'флешка',
        'кабель': 'кабель',
        'провод': 'кабель',
        'шнурок': 'шнурок',
        'ланьярд': 'ланьярд',
        'часы': 'часы',
        'подушка': 'подушка',
        'маска': 'маска',
        'елочная игрушка': 'елочная игрушка',
        'снежный шар': 'снежный шар',
        'конструктор': 'конструктор',
        'мягкая игрушка': 'игрушка',
        'пазл': 'пазл',
        'головоломка': 'головоломка',
        'кубик рубика': 'головоломка',
        'шашки': 'шашки',
        'шахматы': 'шашки',
        'круг': 'круг',
        'резинка': 'резинка',
        'скакалка': 'скакалка',
        'зонт': 'зонт',
        'коробка': 'коробка',
        'автовизитка': 'автовизитка',
        'проектор': 'проектор',
        'фотоаппарат': 'фотоаппарат',
        'ручка': 'ручка',
        'тетрис': 'тетрис',
        'карандаш': 'карандаш',
        'попсокет': 'попсокет',
        'обложка': 'обложка',
        'чемодан': 'чемодан',
        'статуэтка': 'статуэтка',
        'награда': 'статуэтка',
        'панама': 'панама',
        'держатель': 'держатель',
        'гирлянда': 'гирлянда',
        'шлем': 'шлем'
    }
    
    for old, new in replacements.items():
        if old in name:
            name = name.replace(old, new)
            break
    
    return name.strip()

def load_popular_categories():
    """Загрузка популярных категорий из CSV"""
    csv_file = 'Расчеты Хай Вэй NEW - Популярные категории товаров.csv'
    
    # Читаем CSV с правильными параметрами
    df_popular = pd.read_csv(csv_file, encoding='utf-8', skiprows=6)
    
    # Очищаем данные
    popular_data = []
    
    for i, row in df_popular.iterrows():
        if len(row) < 8:  # Минимум столбцов
            continue
            
        category = row.iloc[1] if pd.notna(row.iloc[1]) else ''
        material = row.iloc[2] if pd.notna(row.iloc[2]) else ''
        density = row.iloc[6] if pd.notna(row.iloc[6]) else ''
        rail_rate = row.iloc[8] if len(row) > 8 and pd.notna(row.iloc[8]) else ''
        air_rate = row.iloc[9] if len(row) > 9 and pd.notna(row.iloc[9]) else ''
        rail_density_rate = row.iloc[10] if len(row) > 10 and pd.notna(row.iloc[10]) else ''
        air_density_rate = row.iloc[11] if len(row) > 11 and pd.notna(row.iloc[11]) else ''
        certificates = row.iloc[12] if len(row) > 12 and pd.notna(row.iloc[12]) else ''
        
        if str(category).strip() != '':
            popular_data.append({
                'category_original': str(category).strip(),
                'category_normalized': normalize_category_name(category),
                'material': str(material).strip(),
                'density_recommended': density,
                'rail_rate_base': rail_rate,
                'air_rate_base': air_rate,
                'rail_rate_density': rail_density_rate,
                'air_rate_density': air_density_rate,
                'certificates': str(certificates).strip()
            })
    
    return pd.DataFrame(popular_data)

def find_missing_categories_in_db(popular_categories, db_path):
    """Поиск товаров в БД для категорий, которых нет в наших результатах"""
    conn = sqlite3.connect(db_path)
    
    missing_data = []
    
    for _, row in popular_categories.iterrows():
        category_norm = row['category_normalized']
        category_orig = row['category_original']
        
        if category_norm == '':
            continue
            
        # Ищем товары по ключевым словам
        keywords = category_norm.split()
        if len(keywords) == 0:
            continue
            
        # Строим запрос для поиска
        where_conditions = []
        for keyword in keywords:
            where_conditions.append(f"(p.title LIKE '%{keyword}%' OR p.original_title LIKE '%{keyword}%')")
        
        where_clause = ' OR '.join(where_conditions)
        
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
            pv.cargo_density
        FROM products p
        JOIN product_variants pv ON p.id = pv.product_id
        WHERE {where_clause}
            AND pv.moq > 1
        LIMIT 50
        """
        
        try:
            df_found = pd.read_sql_query(query, conn)
            if len(df_found) > 0:
                missing_data.append({
                    'category_original': category_orig,
                    'category_normalized': category_norm,
                    'found_products': len(df_found),
                    'products_data': df_found
                })
        except Exception as e:
            print(f"Ошибка поиска для {category_orig}: {e}")
    
    conn.close()
    return missing_data

def create_enhanced_ranges_table():
    """Создание расширенной таблицы с данными из популярных категорий"""
    
    print("🎯 СОЗДАНИЕ РАСШИРЕННОЙ ТАБЛИЦЫ С ПОПУЛЯРНЫМИ КАТЕГОРИЯМИ")
    print("=" * 70)
    
    # Загружаем популярные категории
    print("📊 Загрузка популярных категорий из CSV...")
    popular_df = load_popular_categories()
    print(f"✅ Загружено {len(popular_df)} популярных категорий")
    
    # Загружаем наши данные
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    analyzer = BusinessFinalAnalyzer(db_path)
    
    print("📊 Загрузка данных из БД...")
    stats, coverage, excluded_count, total_products = analyzer.run_business_analysis()
    
    # Создаем основную таблицу диапазонов
    ranges_data = []
    
    for stat in stats:
        if not stat.get('gaussian_ranges'):
            continue
            
        row = {
            'Тип': stat['тип'],
            'Категория': stat['категория'],
            'Родитель': stat['родитель'],
            'Товаров': stat['товары'],
            'Медиана_цены_руб': stat.get('медиана_цены_rub'),
            'Медиана_цены_юань': stat.get('медиана_цены_cny'),
            'Медиана_тиража': stat.get('средний_тираж'),
            'Медиана_плотности': stat.get('медиана_плотности'),
            'Медиана_транспорта': stat.get('медиана_транспорта_usd'),
        }
        
        # Добавляем диапазоны для каждой метрики
        for field, ranges in stat['gaussian_ranges'].items():
            if field == 'price_rub':
                row.update({
                    'Цена_руб_мин': ranges['lower_70'],
                    'Цена_руб_макс': ranges['upper_70'],
                    'Цена_руб_медиана': ranges['median'],
                    'Цена_руб_среднее': ranges['mean'],
                    'Цена_руб_стд': ranges['std'],
                    'Цена_руб_количество': ranges['count']
                })
            elif field == 'price_cny':
                row.update({
                    'Цена_юань_мин': ranges['lower_70'],
                    'Цена_юань_макс': ranges['upper_70'],
                    'Цена_юань_медиана': ranges['median'],
                    'Цена_юань_среднее': ranges['mean'],
                    'Цена_юань_стд': ranges['std'],
                    'Цена_юань_количество': ranges['count']
                })
            elif field == 'avg_requested_tirage':
                row.update({
                    'Тираж_мин': ranges['lower_70'],
                    'Тираж_макс': ranges['upper_70'],
                    'Тираж_медиана': ranges['median'],
                    'Тираж_среднее': ranges['mean'],
                    'Тираж_стд': ranges['std'],
                    'Тираж_количество': ranges['count']
                })
            elif field == 'cargo_density':
                row.update({
                    'Плотность_мин': ranges['lower_70'],
                    'Плотность_макс': ranges['upper_70'],
                    'Плотность_медиана': ranges['median'],
                    'Плотность_среднее': ranges['mean'],
                    'Плотность_стд': ranges['std'],
                    'Плотность_количество': ranges['count']
                })
            elif field == 'transport_tariff':
                row.update({
                    'Транспорт_мин': ranges['lower_70'],
                    'Транспорт_макс': ranges['upper_70'],
                    'Транспорт_медиана': ranges['median'],
                    'Транспорт_среднее': ranges['mean'],
                    'Транспорт_стд': ranges['std'],
                    'Транспорт_количество': ranges['count']
                })
        
        ranges_data.append(row)
    
    # Создаем DataFrame
    df_ranges = pd.DataFrame(ranges_data)
    
    # Добавляем данные из популярных категорий
    print("🔗 Сопоставление с популярными категориями...")
    
    # Нормализуем названия наших категорий
    df_ranges['category_normalized'] = df_ranges['Категория'].apply(normalize_category_name)
    
    # Объединяем с популярными категориями
    merged_df = df_ranges.merge(
        popular_df, 
        left_on='category_normalized', 
        right_on='category_normalized', 
        how='left'
    )
    
    # Переименовываем столбцы для ясности
    merged_df = merged_df.rename(columns={
        'category_original': 'Популярная_категория',
        'material': 'Материал_рекомендуемый',
        'density_recommended': 'Плотность_рекомендуемая',
        'rail_rate_base': 'Ставка_жд_базовая',
        'air_rate_base': 'Ставка_авиа_базовая',
        'rail_rate_density': 'Ставка_жд_по_плотности',
        'air_rate_density': 'Ставка_авиа_по_плотности',
        'certificates': 'Сертификаты_требуемые'
    })
    
    # Удаляем служебный столбец
    merged_df = merged_df.drop('category_normalized', axis=1)
    
    # Сортируем по количеству товаров
    merged_df = merged_df.sort_values('Товаров', ascending=False)
    
    # Ищем недостающие категории в БД
    print("🔍 Поиск недостающих категорий в БД...")
    missing_categories = find_missing_categories_in_db(popular_df, db_path)
    
    # Добавляем найденные категории
    for missing in missing_categories:
        if missing['found_products'] >= 5:  # Минимум 5 товаров
            print(f"  ✅ Найдено {missing['found_products']} товаров для '{missing['category_original']}'")
            
            # Создаем строку для недостающей категории
            products_data = missing['products_data']
            
            new_row = {
                'Тип': 'popular',
                'Категория': missing['category_original'],
                'Родитель': '',
                'Товаров': len(products_data),
                'Медиана_цены_руб': products_data['price_rub'].median() if not products_data['price_rub'].isna().all() else None,
                'Медиана_цены_юань': products_data['price_cny'].median() if not products_data['price_cny'].isna().all() else None,
                'Медиана_тиража': products_data['moq'].median() if not products_data['moq'].isna().all() else None,
                'Медиана_плотности': products_data['cargo_density'].median() if not products_data['cargo_density'].isna().all() else None,
                'Медиана_транспорта': products_data['transport_tariff'].median() if not products_data['transport_tariff'].isna().all() else None,
                'Популярная_категория': missing['category_original'],
                'Материал_рекомендуемый': '',
                'Плотность_рекомендуемая': '',
                'Ставка_жд_базовая': '',
                'Ставка_авиа_базовая': '',
                'Ставка_жд_по_плотности': '',
                'Ставка_авиа_по_плотности': '',
                'Сертификаты_требуемые': ''
            }
            
            # Добавляем в таблицу
            merged_df = pd.concat([merged_df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Сохраняем результат
    output_file = Path(__file__).parent / "ENHANCED_CATEGORIES_RANGES.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Основная таблица
        merged_df.to_excel(writer, sheet_name='Расширенные_диапазоны', index=False)
        
        # ТОП-20
        df_top20 = merged_df.head(20)
        df_top20.to_excel(writer, sheet_name='ТОП_20_расширенные', index=False)
        
        # Только с популярными данными
        df_with_popular = merged_df[merged_df['Популярная_категория'].notna()]
        df_with_popular.to_excel(writer, sheet_name='С_популярными_данными', index=False)
        
        # Только популярные категории
        df_popular_only = merged_df[merged_df['Тип'] == 'popular']
        df_popular_only.to_excel(writer, sheet_name='Популярные_категории', index=False)
    
    print(f"✅ Расширенная таблица создана: {output_file}")
    print(f"📊 Листы:")
    print(f"  1. 'Расширенные_диапазоны' - {len(merged_df)} категорий с полными данными")
    print(f"  2. 'ТОП_20_расширенные' - лидеры с популярными данными")
    print(f"  3. 'С_популярными_данными' - категории с данными из CSV")
    print(f"  4. 'Популярные_категории' - только найденные в БД популярные категории")
    print()
    print(f"🎯 ДОПОЛНИТЕЛЬНЫЕ СТОЛБЦЫ:")
    print(f"  • Материал_рекомендуемый - рекомендуемые материалы")
    print(f"  • Плотность_рекомендуемая - рекомендуемая плотность")
    print(f"  • Ставка_жд_базовая - базовая ставка ЖД")
    print(f"  • Ставка_авиа_базовая - базовая ставка авиа")
    print(f"  • Ставка_жд_по_плотности - ставка ЖД по плотности")
    print(f"  • Ставка_авиа_по_плотности - ставка авиа по плотности")
    print(f"  • Сертификаты_требуемые - требуемые сертификаты")
    
    analyzer.conn.close()
    return output_file

if __name__ == "__main__":
    create_enhanced_ranges_table()
