#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Веб-интерфейс для просмотра результатов парсинга коммерческих предложений
Готов для деплоя в интернет
"""

# КРИТИЧЕСКИ ВАЖНО: Импортируем psycopg2 САМЫМ ПЕРВЫМ!
# Как в promo_calculator - это решает проблему с типами
import psycopg2
import psycopg2.extensions

# Регистрируем типы СРАЗУ после импорта psycopg2
TEXT_OID = psycopg2.extensions.new_type((25,), "TEXT", psycopg2.STRING)
psycopg2.extensions.register_type(TEXT_OID)

VARCHAR_OID = psycopg2.extensions.new_type((1043,), "VARCHAR", psycopg2.STRING)
psycopg2.extensions.register_type(VARCHAR_OID)

BPCHAR_OID = psycopg2.extensions.new_type((1042,), "BPCHAR", psycopg2.STRING)
psycopg2.extensions.register_type(BPCHAR_OID)

print("✅ [APP] psycopg2 типы зарегистрированы ДО всех импортов (как в promo_calculator)")

import os
from pathlib import Path
import sys

# ===== ВЕКТОРНЫЙ ПОИСК: pgvector (отдельная БД) =====
PGVECTOR_ENABLED = False
PGVECTOR_ENGINE = None
OPENAI_CLIENT = None

try:
    from openai import OpenAI
    from dotenv import load_dotenv
    from sqlalchemy import create_engine
    
    load_dotenv()
    
    # 1. Подключение к pgvector БД
    vector_db_url = os.getenv('VECTOR_DATABASE_URL')
    if vector_db_url:
        PGVECTOR_ENGINE = create_engine(vector_db_url, pool_pre_ping=True)
        # Проверка подключения
        with PGVECTOR_ENGINE.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print("✅ [APP] pgvector БД подключена")
        print(f"   URL: {vector_db_url[:50]}...")
    
    # 2. OpenAI API для генерации embeddings
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and PGVECTOR_ENGINE:
        OPENAI_CLIENT = OpenAI(api_key=api_key)
        PGVECTOR_ENABLED = True
        print("✅ [APP] Векторный поиск через pgvector ВКЛЮЧЕН")
        print("   📝 Поиск делает PostgreSQL (СУПЕР БЫСТРО!)")
    elif not PGVECTOR_ENGINE:
        print("ℹ️  [APP] VECTOR_DATABASE_URL не настроен")
    elif not api_key:
        print("ℹ️  [APP] OPENAI_API_KEY не настроен")
        
except Exception as e:
    print(f"⚠️  [APP] pgvector недоступен: {e}")
    PGVECTOR_ENABLED = False

if not PGVECTOR_ENABLED:
    print("ℹ️  [APP] Используется обычный текстовый поиск (ILIKE)")

# ===== IMAGE SEARCH: CLIP модель =====
# ВРЕМЕННО ОТКЛЮЧЕНО: Блокирует запуск приложения на Railway
IMAGE_SEARCH_ENABLED = False
CLIP_MODEL = None
print("ℹ️  [APP] Поиск по изображениям ОТКЛЮЧЕН (загрузка CLIP модели пропущена)")

# Раскомментируй для включения (требует ~1GB RAM):
# try:
#     if PGVECTOR_ENGINE and OPENAI_CLIENT:  # Image search требует pgvector БД
#         print("🔄 [APP] Загружаю CLIP модель (это может занять 10-30 секунд)...")
#         import time
#         start_time = time.time()
#         
#         from sentence_transformers import SentenceTransformer
#         CLIP_MODEL = SentenceTransformer('clip-ViT-B-32')
#         
#         load_time = time.time() - start_time
#         IMAGE_SEARCH_ENABLED = True
#         print(f"✅ [APP] CLIP модель загружена за {load_time:.1f}с - поиск по изображениям ВКЛЮЧЕН")
#     elif not PGVECTOR_ENGINE:
#         print("ℹ️  [APP] CLIP модель НЕ загружается: отсутствует pgvector БД")
#     elif not OPENAI_CLIENT:
#         print("ℹ️  [APP] CLIP модель НЕ загружается: отсутствует OpenAI API")
# except Exception as e:
#     import traceback
#     print(f"⚠️  [APP] CLIP модель недоступна: {e}")
#     print(f"   Traceback: {traceback.format_exc()}")
#     print("ℹ️  [APP] Поиск по изображениям ОТКЛЮЧЕН")

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for
from flask import session as flask_session
import uuid

# ВРЕМЕННО ОТКЛЮЧЕНО: Импорты для image search (но нужны для endpoint)
try:
    from werkzeug.utils import secure_filename
    from PIL import Image
    import io
    import tempfile
except ImportError:
    # Если не установлены - endpoint вернет 503
    pass

# Патчим SQLAlchemy dialect ДО импорта моделей
try:
    from sqlalchemy.dialects.postgresql import base as pg_base
    from sqlalchemy import String, Text
    
    # Заменяем все TEXT типы на String в ischema_names
    pg_base.ischema_names['text'] = String
    pg_base.ischema_names['varchar'] = String
    pg_base.ischema_names['bpchar'] = String
    
    print("✅ [APP] SQLAlchemy dialect пропатчен - все TEXT типы заменены на String")
except Exception as e:
    print(f"❌ [APP] Ошибка патча dialect: {e}")

from database.postgresql_manager import db_manager
from database.models import Project, Product, PriceOffer, ProductImage
from sqlalchemy import or_, func
import math

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')  # Для сессий

# Добавляем функцию в контекст шаблонов
@app.context_processor
def inject_image_url():
    return dict(get_image_url=get_image_url)

# Импортируем конфигурацию
from config import (
    CLOUD_STORAGE_ENABLED, S3_BASE_URL, CLOUD_IMAGES_PREFIX,
    PRODUCTS_PER_PAGE, PROJECTS_PER_PAGE, IMAGES_DIR,
    get_image_url
)
from auth import AUTH_USERNAME, AUTH_PASSWORD, SECRET_KEY, create_session_token, check_session, login_required

# image_proxy не нужен - изображения публично доступны в S3

from datetime import datetime

# ===== УТИЛИТЫ =====

def parse_price(price_str):
    """Парсит цену из текстового формата '20 700,00 ₽' в float"""
    if not price_str:
        return None
    try:
        # Убираем символ рубля и неразрывные пробелы
        cleaned = str(price_str).replace('₽', '').replace('\xa0', '').replace(' ', '').strip()
        # Заменяем запятую на точку
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return None

# ===== ВЕКТОРНЫЙ ПОИСК (с graceful fallback) =====

def generate_search_embedding(query: str):
    """
    Генерирует embedding для поискового запроса
    Возвращает None если векторный поиск недоступен
    """
    if not VECTOR_SEARCH_AVAILABLE or not OPENAI_CLIENT:
        return None
    
    try:
        # Таймаут 10 секунд для OpenAI API
        import httpx
        client_with_timeout = OpenAI(
            api_key=OPENAI_CLIENT.api_key,
            timeout=httpx.Timeout(10.0, connect=5.0)
        )
        response = client_with_timeout.embeddings.create(
            input=query[:8000],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"⚠️  [VECTOR] Ошибка генерации embedding: {e}")
        return None

def cosine_similarity(vec1, vec2):
    """Вычисляет косинусное сходство между двумя векторами"""
    import math
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    return dot_product / (magnitude1 * magnitude2)

def vector_search_pgvector(search_query, limit=200):
    """
    Выполняет векторный поиск через pgvector БД (СУПЕР БЫСТРО!)
    PostgreSQL делает поиск используя индекс ivfflat
    
    Возвращает: list of product_id или None (fallback)
    """
    if not PGVECTOR_ENABLED or not PGVECTOR_ENGINE or not OPENAI_CLIENT:
        return None
    
    try:
        import httpx
        from sqlalchemy import text
        import time
        
        start_time = time.time()
        
        # 1. Генерируем embedding для запроса
        response = OPENAI_CLIENT.embeddings.create(
            model="text-embedding-3-small",
            input=search_query.strip(),
            timeout=httpx.Timeout(10.0)
        )
        query_embedding = response.data[0].embedding
        
        embedding_time = time.time() - start_time
        
        # 2. ВЕКТОРНЫЙ ПОИСК в pgvector БД
        #    PostgreSQL делает поиск (не Python!)
        search_start = time.time()
        
        # Преобразуем list в строку для pgvector
        # pgvector ожидает строку вида '[0.1, 0.2, ...]'
        query_vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        with PGVECTOR_ENGINE.connect() as conn:
            # Используем format SQL так как SQLAlchemy text() конфликтует с ::vector cast
            sql_query = f"""
                SELECT 
                    product_id,
                    1 - (name_embedding <=> '{query_vector_str}'::vector) as similarity
                FROM product_embeddings
                WHERE 1 - (name_embedding <=> '{query_vector_str}'::vector) >= 0.55
                ORDER BY name_embedding <=> '{query_vector_str}'::vector
                LIMIT {limit}
            """
            results = conn.execute(text(sql_query)).fetchall()
        
        search_time = time.time() - search_start
        total_time = time.time() - start_time
        
        product_ids = [r[0] for r in results]
        
        print(f"🔍 [PGVECTOR] Найдено {len(product_ids)} товаров")
        print(f"   ⏱️  Embedding: {embedding_time:.2f}с | Поиск: {search_time:.2f}с | Всего: {total_time:.2f}с")
        
        return product_ids if product_ids else None
        
    except Exception as e:
        print(f"❌ [PGVECTOR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def vector_search_products(session, query_embedding, limit=100):
    """
    СТАРАЯ ФУНКЦИЯ: Векторный поиск через TEXT embeddings (медленно!)
    Оставлена для обратной совместимости
    Возвращает список ID товаров, отсортированных по релевантности
    Если что-то не работает - возвращает None (fallback на обычный поиск)
    """
    if not query_embedding:
        return None
    
    try:
        from sqlalchemy import text
        import json
        
        # Проверяем что колонка существует (сначала TEXT версия, потом pgvector)
        check_text = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            AND column_name = 'name_embedding_text'
        """)).fetchone()
        
        check_vector = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            AND column_name = 'name_embedding'
        """)).fetchone()
        
        if not check_text and not check_vector:
            print("⚠️  [VECTOR] Embeddings колонки не существуют, используем обычный поиск")
            return None
        
        # Если есть TEXT колонка - используем её (простая версия)
        if check_text:
            print("🔍 [VECTOR] Используем TEXT embeddings (оптимизированная версия)")
            
            import time
            start_time = time.time()
            
            # ОПТИМИЗАЦИЯ: Загружаем только 200 товаров вместо 1000
            # Берем последние добавленные товары (они обычно актуальнее)
            result = session.execute(text("""
                SELECT id, name, name_embedding_text
                FROM products
                WHERE name_embedding_text IS NOT NULL
                ORDER BY id DESC
                LIMIT 200
            """)).fetchall()
            
            fetch_time = time.time() - start_time
            print(f"   Загружено {len(result)} товаров за {fetch_time:.2f}с")
            
            # Вычисляем similarity в Python
            similarities = []
            calc_start = time.time()
            
            for product_id, product_name, embedding_json in result:
                try:
                    # ОПТИМИЗАЦИЯ: Таймаут на весь поиск (5 секунд max)
                    if time.time() - start_time > 5.0:
                        print("⚠️  [VECTOR] Timeout 5с, прерываем поиск")
                        break
                    
                    product_embedding = json.loads(embedding_json)
                    similarity = cosine_similarity(query_embedding, product_embedding)
                    
                    # ОПТИМИЗАЦИЯ: Снизили порог до 0.25 для лучшего recall
                    if similarity > 0.25:
                        similarities.append((product_id, product_name, similarity))
                except:
                    continue
            
            calc_time = time.time() - calc_start
            print(f"   Вычислено similarity для {len(similarities)} товаров за {calc_time:.2f}с")
            
            # Сортируем по similarity
            similarities.sort(key=lambda x: x[2], reverse=True)
            
            # Берем top results
            product_ids = [pid for pid, _, _ in similarities[:limit]]
            
            total_time = time.time() - start_time
            
            if product_ids:
                print(f"✅ [VECTOR] Найдено {len(product_ids)} релевантных товаров за {total_time:.2f}с")
            else:
                print("⚠️  [VECTOR] Векторный поиск не нашел релевантных товаров")
            
            return product_ids if product_ids else None
        
        # Если есть pgvector колонка - используем её (быстрая версия)
        elif check_vector:
            print("🔍 [VECTOR] Используем pgvector (быстрая версия)")
            
            result = session.execute(text("""
                SELECT id, name, 
                       1 - (name_embedding <=> :query_embedding::vector) as similarity
                FROM products
                WHERE name_embedding IS NOT NULL
                ORDER BY name_embedding <=> :query_embedding::vector
                LIMIT :limit
            """), {
                'query_embedding': str(query_embedding),
                'limit': limit
            }).fetchall()
            
            product_ids = [row[0] for row in result if row[2] > 0.3]
            
            if product_ids:
                print(f"✅ [VECTOR] Найдено {len(product_ids)} релевантных товаров (pgvector)")
            else:
                print("⚠️  [VECTOR] Векторный поиск не нашел релевантных товаров")
            
            return product_ids if product_ids else None
        
    except Exception as e:
        print(f"⚠️  [VECTOR] Ошибка векторного поиска: {e}")
        print("   Используем обычный текстовый поиск")
        return None

# ===== АВТОРИЗАЦИЯ =====

@app.route('/login')
def login_page():
    """Страница входа"""
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    """API endpoint для авторизации"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Проверка credentials
        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            # Создаем новую сессию
            session_token = create_session_token()
            session['session_token'] = session_token
            session['username'] = username
            
            return jsonify({"success": True, "message": "Успешная авторизация"})
        else:
            return jsonify({"success": False, "message": "Неверный логин или пароль"}), 401
    
    except Exception as e:
        return jsonify({"success": False, "message": "Ошибка сервера"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """API endpoint для выхода"""
    session.clear()
    return jsonify({"success": True, "message": "Вы вышли из системы"})

# ===== ОСНОВНЫЕ РОУТЫ =====

@app.route('/')
@login_required
def index():
    """Главная страница с общей статистикой"""
    try:
        print("🔍 [DEBUG] Начинаем запрос к БД...")
        
        with db_manager.get_session() as session:
            print("🔍 [DEBUG] Сессия создана успешно")
            
            # ТЕСТОВЫЙ ЗАПРОС: Пробуем простой COUNT
            try:
                print("🔍 [DEBUG] Пробуем COUNT(*)...")
                projects_count = session.query(Project).count()
                print(f"✅ [DEBUG] COUNT успешен: {projects_count}")
            except Exception as e:
                print(f"❌ [DEBUG] Ошибка в COUNT: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Получаем статистику
            products_count = session.query(Product).count()
            offers_count = session.query(PriceOffer).count()
            images_count = session.query(ProductImage).count()
            completed_projects = session.query(Project).filter(Project.parsing_status == 'complete').count()
            
            # Получаем последние обработанные проекты (только с товарами)
            print("🔍 [DEBUG] Пробуем получить последние проекты через RAW SQL...")
            
            # Используем RAW SQL чтобы обойти проблему с типами
            from sqlalchemy import text
            raw_sql = text("""
                SELECT id, project_name, file_name, google_sheets_url, 
                       manager_name, total_products_found, total_images_found,
                       updated_at, created_at
                FROM projects 
                WHERE parsing_status = 'complete' AND total_products_found > 0
                ORDER BY updated_at DESC 
                LIMIT 6
            """)
            
            result = session.execute(raw_sql)
            rows = result.fetchall()
            
            # Преобразуем в объекты Project вручную
            recent_projects = []
            for row in rows:
                project = Project()
                project.id = row[0]
                project.project_name = row[1]
                project.file_name = row[2]
                project.google_sheets_url = row[3]
                project.manager_name = row[4]
                project.total_products_found = row[5]
                project.total_images_found = row[6]
                # Преобразуем строки в datetime объекты
                project.updated_at = datetime.fromisoformat(str(row[7])) if row[7] else None
                project.created_at = datetime.fromisoformat(str(row[8])) if row[8] else None
                recent_projects.append(project)
            
            print(f"✅ [DEBUG] Получено проектов через RAW SQL: {len(recent_projects)}")
            
            stats = {
                'projects': projects_count,
                'products': products_count,
                'offers': offers_count,
                'images': images_count,
                'completed_projects': completed_projects
            }
            
            print("🔍 [DEBUG] Рендерим шаблон...")
            return render_template('index_new.html', stats=stats, recent_projects=recent_projects)
    except Exception as e:
        print(f"❌ [ERROR] Критическая ошибка в index(): {e}")
        import traceback
        traceback.print_exc()
        return f"Ошибка: {e}", 500

@app.route('/products')
@login_required
def products_list():
    """Список товаров с пагинацией, поиском и фильтрами"""
    from sqlalchemy import text
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    max_quantity = request.args.get('max_quantity', type=int)  # Фильтр по тиражу (до)
    max_price = request.args.get('max_price', type=float)  # Фильтр по макс. цене RUB
    max_delivery_days = request.args.get('max_delivery_days', type=int)  # Фильтр по сроку доставки (до)
    region_uae = request.args.get('region_uae')  # Фильтр по ОАЭ (checkbox)
    sort_by = request.args.get('sort_by', '', type=str)  # Сортировка
    image_search_id = request.args.get('image_search', '', type=str)  # ID поиска по изображению
    
    with db_manager.get_session() as session:
        # Строим динамический WHERE для фильтров
        where_conditions = []
        params = {}
        
        # ===== ПОИСК ПО ИЗОБРАЖЕНИЮ =====
        image_product_ids = None
        if image_search_id:
            # Получаем product_ids из сессии
            session_key = f'image_search_{image_search_id}'
            image_product_ids = flask_session.get(session_key)
            
            if image_product_ids:
                print(f"🖼️  [IMAGE SEARCH] Показываем результаты поиска по изображению: {len(image_product_ids)} товаров")
                where_conditions.append(f"p.id IN :image_ids")
                params["image_ids"] = tuple(image_product_ids)
                # Отключаем текстовый поиск при image search
                search = ''
            else:
                print(f"⚠️  [IMAGE SEARCH] Результаты не найдены в сессии (search_id: {image_search_id})")
        
        # ===== УМНЫЙ ПОИСК: pgvector → fallback на ILIKE =====
        vector_product_ids = None
        if search.strip():
            # 1. Пробуем pgvector поиск (СУПЕР БЫСТРО!)
            vector_product_ids = vector_search_pgvector(search.strip(), limit=200)
            
            # 2. Выбираем метод поиска
            if vector_product_ids:
                # pgvector поиск успешен - ищем по ID
                print(f"🔍 [SEARCH] Используем pgvector поиск: {len(vector_product_ids)} товаров")
                where_conditions.append(f"p.id IN :vector_ids")
                params["vector_ids"] = tuple(vector_product_ids)
            else:
                # Fallback на обычный текстовый поиск
                print(f"🔍 [SEARCH] Используем текстовый поиск (ILIKE)")
                where_conditions.append("(p.name ILIKE :search OR p.description ILIKE :search)")
                params["search"] = f"%{search.strip()}%"
        
        # Фильтр по региону ОАЭ
        if region_uae:
            where_conditions.append("pr.region = 'ОАЭ'")
        
        # Фильтры по цене, тиражу и сроку требуют JOIN с price_offers
        needs_price_join = max_quantity is not None or max_price is not None or max_delivery_days is not None
        
        if needs_price_join:
            # Добавляем подзапрос для фильтрации по ценовым предложениям
            # ВАЖНО: quantity и price_rub могут быть TEXT в БД, поэтому используем CAST
            price_filters = []
            if max_quantity is not None:
                price_filters.append("CAST(po.quantity AS INTEGER) <= :max_quantity")
                params["max_quantity"] = max_quantity
            if max_price is not None:
                price_filters.append("CAST(po.price_rub AS NUMERIC) <= :max_price")
                params["max_price"] = max_price
            if max_delivery_days is not None:
                price_filters.append("po.delivery_time_days <= :max_delivery_days")
                params["max_delivery_days"] = max_delivery_days
            
            price_where = " AND ".join(price_filters)
            where_conditions.append(f"p.id IN (SELECT DISTINCT product_id FROM price_offers po WHERE {price_where})")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Определяем SELECT и ORDER BY в зависимости от sort_by
        # ВАЖНО: для SELECT DISTINCT все поля в ORDER BY должны быть в SELECT
        # Используем offer_created_at (TIMESTAMP) вместо offer_creation_date (TEXT) для корректной сортировки
        base_select = """p.id, p.project_id, p.name, p.description, p.article_number, 
                   p.sample_price, p.sample_delivery_time, p.row_number, pr.region, pr.offer_created_at"""
        
        order_by = "p.id DESC"  # По умолчанию
        select_fields = base_select
        
        if sort_by == "date_asc":
            order_by = "pr.offer_created_at ASC NULLS LAST, p.id ASC"
        elif sort_by == "date_desc":
            order_by = "pr.offer_created_at DESC NULLS LAST, p.id DESC"
        elif sort_by == "price_asc":
            # Добавляем подзапрос для цены в SELECT для сортировки
            select_fields = base_select + """, (SELECT MIN(CAST(po.price_rub AS NUMERIC)) FROM price_offers po WHERE po.product_id = p.id) as min_price"""
            order_by = "min_price ASC NULLS LAST, p.id ASC"
        elif sort_by == "price_desc":
            select_fields = base_select + """, (SELECT MIN(CAST(po.price_rub AS NUMERIC)) FROM price_offers po WHERE po.product_id = p.id) as min_price"""
            order_by = "min_price DESC NULLS LAST, p.id DESC"
        
        # Подсчитываем общее количество с фильтрами
        count_sql = text(f"""
            SELECT COUNT(DISTINCT p.id) 
            FROM products p
            LEFT JOIN projects pr ON p.project_id = pr.id
            WHERE {where_clause}
        """)
        total = session.execute(count_sql, params).scalar()
        
        # Получаем товары с фильтрами
        products_sql = text(f"""
            SELECT DISTINCT {select_fields}
            FROM products p
            LEFT JOIN projects pr ON p.project_id = pr.id
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
        """)
        params["limit"] = PRODUCTS_PER_PAGE
        params["offset"] = (page - 1) * PRODUCTS_PER_PAGE
        
        rows = session.execute(products_sql, params).fetchall()
        
        # Преобразуем в объекты Product
        products = []
        for row in rows:
            product = Product()
            product.id = row[0]
            product.project_id = row[1]
            product.name = row[2]
            product.description = row[3]
            product.article_number = row[4]
            product.sample_price = parse_price(row[5])  # Используем parse_price для TEXT формата
            product.sample_delivery_time = int(row[6]) if row[6] is not None else None
            product.row_number = int(row[7]) if row[7] is not None else None
            product.region = row[8]  # Регион проекта
            # row[9] = offer_created_at (TIMESTAMP, используется для сортировки, не нужно присваивать)
            # row[10] = min_price (только для сортировки по цене, если применимо)
            
            # Получаем изображения для товара
            images_sql = text("""
                SELECT id, image_filename, is_main_image 
                FROM product_images 
                WHERE product_id = :product_id 
                ORDER BY is_main_image DESC, display_order
            """)
            image_rows = session.execute(images_sql, {"product_id": product.id}).fetchall()
            
            product.images = []
            for img_row in image_rows:
                img = ProductImage()
                img.id = img_row[0]
                img.image_filename = img_row[1]
                img.is_main_image = img_row[2]
                product.images.append(img)
            
            # Получаем ценовые предложения для товара (для отображения в листинге)
            offers_sql = text("""
                SELECT id, quantity, price_usd, price_rub, delivery_time_days
                FROM price_offers 
                WHERE product_id = :product_id 
                ORDER BY quantity
                LIMIT 3
            """)
            offer_rows = session.execute(offers_sql, {"product_id": product.id}).fetchall()
            
            product.price_offers = []
            for offer_row in offer_rows:
                offer = PriceOffer()
                offer.id = offer_row[0]
                offer.quantity = int(offer_row[1]) if offer_row[1] is not None else None
                offer.price_usd = parse_price(offer_row[2])  # Используем parse_price для TEXT формата
                offer.price_rub = parse_price(offer_row[3])  # Используем parse_price для TEXT формата
                offer.delivery_time_days = int(offer_row[4]) if offer_row[4] is not None else None
                product.price_offers.append(offer)
            
            # Получаем информацию о проекте
            project_sql = text("""
                SELECT id, project_name
                FROM projects 
                WHERE id = :project_id
            """)
            project_row = session.execute(project_sql, {"project_id": product.project_id}).fetchone()
            
            if project_row:
                product.project = Project()
                product.project.id = project_row[0]
                product.project.project_name = project_row[1]
            
            products.append(product)
        
        # Вычисляем данные для пагинации
        total_pages = math.ceil(total / PRODUCTS_PER_PAGE)
        has_prev = page > 1
        has_next = page < total_pages
        
        pagination = {
            'page': page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_num': page - 1 if has_prev else None,
            'next_num': page + 1 if has_next else None,
            'total': total
        }
        
        return render_template('products_list.html', 
                             products=products, 
                             pagination=pagination, 
                             search=search,
                             max_quantity=max_quantity,
                             max_price=max_price,
                             max_delivery_days=max_delivery_days,
                             region_uae=region_uae,
                             sort_by=sort_by)

@app.route('/projects')
@login_required
def projects_list():
    """Список проектов с пагинацией"""
    from sqlalchemy import text
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    with db_manager.get_session() as session:
        # Подсчитываем общее количество с поиском
        if search.strip():
            count_sql = text("""
                SELECT COUNT(*) FROM projects 
                WHERE project_name ILIKE :search OR table_id ILIKE :search
            """)
            total = session.execute(count_sql, {"search": f"%{search.strip()}%"}).scalar()
            
            # Получаем проекты с поиском (считаем товары на лету)
            projects_sql = text("""
                SELECT p.id, p.project_name, p.file_name, p.google_sheets_url, 
                       p.manager_name, 
                       (SELECT COUNT(*) FROM products WHERE project_id = p.id) as total_products_found,
                       p.total_images_found,
                       p.parsing_status, p.updated_at, p.created_at
                FROM projects p
                WHERE p.project_name ILIKE :search OR p.table_id ILIKE :search
                ORDER BY p.id DESC 
                LIMIT :limit OFFSET :offset
            """)
            rows = session.execute(projects_sql, {
                "search": f"%{search.strip()}%",
                "limit": PROJECTS_PER_PAGE,
                "offset": (page - 1) * PROJECTS_PER_PAGE
            }).fetchall()
        else:
            # Без поиска
            total = session.execute(text("SELECT COUNT(*) FROM projects")).scalar()
            
            projects_sql = text("""
                SELECT p.id, p.project_name, p.file_name, p.google_sheets_url, 
                       p.manager_name,
                       (SELECT COUNT(*) FROM products WHERE project_id = p.id) as total_products_found,
                       p.total_images_found,
                       p.parsing_status, p.updated_at, p.created_at
                FROM projects p
                ORDER BY p.id DESC 
                LIMIT :limit OFFSET :offset
            """)
            rows = session.execute(projects_sql, {
                "limit": PROJECTS_PER_PAGE,
                "offset": (page - 1) * PROJECTS_PER_PAGE
            }).fetchall()
        
        # Преобразуем в объекты Project
        projects = []
        for row in rows:
            project = Project()
            project.id = row[0]
            project.project_name = row[1]
            project.file_name = row[2]
            project.google_sheets_url = row[3]
            project.manager_name = row[4]
            project.total_products_found = int(row[5]) if row[5] is not None else 0
            project.total_images_found = int(row[6]) if row[6] is not None else 0
            project.parsing_status = row[7]
            # Преобразуем строки в datetime объекты
            project.updated_at = datetime.fromisoformat(str(row[8])) if row[8] else None
            project.created_at = datetime.fromisoformat(str(row[9])) if row[9] else None
            projects.append(project)
        
        # Вычисляем данные для пагинации
        total_pages = math.ceil(total / PROJECTS_PER_PAGE)
        has_prev = page > 1
        has_next = page < total_pages
        
        pagination = {
            'page': page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_num': page - 1 if has_prev else None,
            'next_num': page + 1 if has_next else None,
            'total': total
        }
        
        return render_template('projects_list.html', 
                             projects=projects, 
                             pagination=pagination, 
                             search=search)

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    """Детальная информация о проекте"""
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Получаем проект
        project_sql = text("""
            SELECT id, table_id, project_name, file_name, google_sheets_url, 
                   manager_name, total_products_found, total_images_found,
                   parsing_status, region, updated_at, created_at, offer_created_at,
                   planfix_task_url
            FROM projects 
            WHERE id = :project_id
        """)
        project_row = session.execute(project_sql, {"project_id": project_id}).fetchone()
        
        if not project_row:
            return "Проект не найден", 404
        
        project = Project()
        project.id = project_row[0]
        project.table_id = project_row[1]
        project.project_name = project_row[2]
        project.file_name = project_row[3]
        project.google_sheets_url = project_row[4]
        project.manager_name = project_row[5]
        project.total_products_found = int(project_row[6]) if project_row[6] is not None else 0
        project.total_images_found = int(project_row[7]) if project_row[7] is not None else 0
        project.parsing_status = project_row[8]
        project.region = project_row[9]
        # Преобразуем строки в datetime объекты
        project.updated_at = datetime.fromisoformat(str(project_row[10])) if project_row[10] else None
        project.created_at = datetime.fromisoformat(str(project_row[11])) if project_row[11] else None
        project.offer_created_at = project_row[12]  # TIMESTAMP
        project.planfix_task_url = project_row[13]  # Planfix URL
        
        # Получаем товары проекта с пагинацией
        page = request.args.get('page', 1, type=int)
        
        # Подсчитываем общее количество
        total = session.execute(
            text("SELECT COUNT(*) FROM products WHERE project_id = :project_id"),
            {"project_id": project_id}
        ).scalar()
        
        # Получаем товары (с регионом)
        products_sql = text("""
            SELECT p.id, p.project_id, p.name, p.description, p.article_number, 
                   p.sample_price, p.sample_delivery_time, p.row_number, pr.region
            FROM products p
            LEFT JOIN projects pr ON p.project_id = pr.id
            WHERE p.project_id = :project_id
            ORDER BY p.id DESC 
            LIMIT :limit OFFSET :offset
        """)
        rows = session.execute(products_sql, {
            "project_id": project_id,
            "limit": PRODUCTS_PER_PAGE,
            "offset": (page - 1) * PRODUCTS_PER_PAGE
        }).fetchall()
        
        # Преобразуем в объекты Product с изображениями и ценами
        products = []
        for row in rows:
            product = Product()
            product.id = row[0]
            product.project_id = row[1]
            product.name = row[2]
            product.description = row[3]
            product.article_number = row[4]
            product.sample_price = parse_price(row[5])  # Используем parse_price для TEXT формата
            product.sample_delivery_time = int(row[6]) if row[6] is not None else None
            product.row_number = int(row[7]) if row[7] is not None else None
            product.region = row[8] if len(row) > 8 else None  # Регион проекта
            
            # Получаем изображения
            images_sql = text("""
                SELECT id, image_filename, is_main_image 
                FROM product_images 
                WHERE product_id = :product_id 
                ORDER BY is_main_image DESC, display_order
            """)
            image_rows = session.execute(images_sql, {"product_id": product.id}).fetchall()
            product.images = []
            for img_row in image_rows:
                img = ProductImage()
                img.id = img_row[0]
                img.image_filename = img_row[1]
                img.is_main_image = img_row[2]
                product.images.append(img)
            
            # Получаем ценовые предложения
            offers_sql = text("""
                SELECT id, quantity, price_usd, price_rub, delivery_time_days
                FROM price_offers 
                WHERE product_id = :product_id 
                ORDER BY quantity
            """)
            offer_rows = session.execute(offers_sql, {"product_id": product.id}).fetchall()
            product.price_offers = []
            
            print(f"🔍 [DEBUG] Товар ID {product.id}: найдено {len(offer_rows)} ценовых предложений")
            
            for offer_row in offer_rows:
                offer = PriceOffer()
                offer.id = offer_row[0]
                offer.quantity = int(offer_row[1]) if offer_row[1] is not None else None
                offer.price_usd = parse_price(offer_row[2])  # Используем parse_price для TEXT формата
                offer.price_rub = parse_price(offer_row[3])  # Используем parse_price для TEXT формата
                offer.delivery_time_days = int(offer_row[4]) if offer_row[4] is not None else None
                product.price_offers.append(offer)
                
            print(f"✅ [DEBUG] Товар ID {product.id}: добавлено {len(product.price_offers)} предложений в объект")
            
            products.append(product)
        
        # Вычисляем данные для пагинации
        total_pages = math.ceil(total / PRODUCTS_PER_PAGE)
        has_prev = page > 1
        has_next = page < total_pages
        
        pagination = {
            'page': page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_num': page - 1 if has_prev else None,
            'next_num': page + 1 if has_next else None,
            'total': total
        }
        
        # Статистика проекта
        project_stats = {
            'products_count': session.execute(
                text("SELECT COUNT(*) FROM products WHERE project_id = :project_id"),
                {"project_id": project_id}
            ).scalar(),
            'offers_count': session.execute(
                text("""
                    SELECT COUNT(*) FROM price_offers po
                    JOIN products p ON po.product_id = p.id
                    WHERE p.project_id = :project_id
                """),
                {"project_id": project_id}
            ).scalar(),
            'images_count': session.execute(
                text("""
                    SELECT COUNT(*) FROM product_images pi
                    JOIN products p ON pi.product_id = p.id
                    WHERE p.project_id = :project_id
                """),
                {"project_id": project_id}
            ).scalar()
        }
        
        return render_template('project_detail.html', 
                             project=project, 
                             products=products, 
                             pagination=pagination,
                             project_stats=project_stats)

@app.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    """Детальная информация о товаре"""
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Получаем товар (с регионом)
        product_sql = text("""
            SELECT p.id, p.project_id, p.name, p.description, p.article_number, 
                   p.sample_price, p.sample_delivery_time, p.row_number, p.custom_field, pr.region
            FROM products p
            LEFT JOIN projects pr ON p.project_id = pr.id
            WHERE p.id = :product_id
        """)
        product_row = session.execute(product_sql, {"product_id": product_id}).fetchone()
        
        if not product_row:
            return "Товар не найден", 404
        
        product = Product()
        product.id = product_row[0]
        product.project_id = product_row[1]
        product.name = product_row[2]
        product.description = product_row[3]
        product.article_number = product_row[4]
        product.sample_price = parse_price(product_row[5])  # Используем parse_price для TEXT формата
        product.sample_delivery_time = int(product_row[6]) if product_row[6] is not None else None
        product.row_number = int(product_row[7]) if product_row[7] is not None else None
        product.custom_field = product_row[8]  # Дизайн
        product.region = product_row[9] if len(product_row) > 9 else None  # Регион проекта
        
        # Получаем информацию о проекте
        project_sql = text("SELECT id, project_name, table_id, offer_created_at, manager_name FROM projects WHERE id = :project_id")
        project_row_data = session.execute(project_sql, {"project_id": product.project_id}).fetchone()
        if project_row_data:
            product.project = Project()
            product.project.id = project_row_data[0]
            product.project.project_name = project_row_data[1]
            product.project.table_id = project_row_data[2]
            product.project.offer_created_at = project_row_data[3]  # TIMESTAMP
            product.project.manager_name = project_row_data[4]
        
        # Получаем все ценовые предложения
        offers_sql = text("""
            SELECT id, quantity, price_usd, price_rub, delivery_time_days, route
            FROM price_offers 
            WHERE product_id = :product_id 
            ORDER BY quantity
        """)
        offer_rows = session.execute(offers_sql, {"product_id": product_id}).fetchall()
        
        price_offers = []
        for row in offer_rows:
            offer = PriceOffer()
            offer.id = row[0]
            offer.quantity = int(row[1]) if row[1] is not None else None
            offer.price_usd = parse_price(row[2])  # Используем parse_price для TEXT формата
            offer.price_rub = parse_price(row[3])  # Используем parse_price для TEXT формата
            offer.delivery_time_days = int(row[4]) if row[4] is not None else None
            offer.route = row[5]
            price_offers.append(offer)
        
        # Получаем все изображения
        images_sql = text("""
            SELECT id, image_filename, is_main_image, display_order
            FROM product_images 
            WHERE product_id = :product_id 
            ORDER BY is_main_image DESC, display_order
        """)
        image_rows = session.execute(images_sql, {"product_id": product_id}).fetchall()
        
        images = []
        for row in image_rows:
            img = ProductImage()
            img.id = row[0]
            img.image_filename = row[1]
            img.is_main_image = bool(row[2]) if row[2] is not None else False
            img.display_order = int(row[3]) if row[3] is not None else 1
            images.append(img)
        
        return render_template('product_detail.html', 
                             product=product, 
                             price_offers=price_offers, 
                             images=images)

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Отдача изображений из облачного хранилища или локальной папки"""
    if CLOUD_STORAGE_ENABLED:
        # Перенаправляем на облачное хранилище
        from flask import redirect
        cloud_url = f"{S3_BASE_URL}/{CLOUD_IMAGES_PREFIX}{filename}"
        return redirect(cloud_url)
    else:
        # Используем локальную папку
        return send_from_directory(IMAGES_DIR, filename)

@app.route('/api/stats')
@login_required
def api_stats():
    """API для получения статистики"""
    with db_manager.get_session() as session:
        stats = {
            'projects': session.query(Project).count(),
            'products': session.query(Product).count(),
            'offers': session.query(PriceOffer).count(),
            'images': session.query(ProductImage).count(),
            'completed_projects': session.query(Project).filter(
                Project.parsing_status == 'complete'
            ).count()
        }
        return jsonify(stats)

@app.route('/api/search')
@login_required
def api_search():
    """API для поиска товаров"""
    query = request.args.get('q', '', type=str)
    limit = request.args.get('limit', 10, type=int)
    
    if not query.strip():
        return jsonify([])
    
    with db_manager.get_session() as session:
        search_term = f"%{query.strip()}%"
        products = session.query(Product).filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        ).limit(limit).all()
        
        results = []
        for product in products:
            # Получаем первое изображение
            first_image = session.query(ProductImage).filter(
                ProductImage.product_id == product.id
            ).first()
            
            # Получаем первое ценовое предложение
            first_offer = session.query(PriceOffer).filter(
                PriceOffer.product_id == product.id
            ).order_by(PriceOffer.quantity).first()
            
            results.append({
                'id': product.id,
                'name': product.name,
                'description': product.description[:100] + '...' if product.description and len(product.description) > 100 else product.description,
                'image': first_image.image_filename if first_image else None,
                'price': first_offer.price_usd if first_offer else None,
                'quantity': first_offer.quantity if first_offer else None
            })
        
        return jsonify(results)

# ===== API ДЛЯ КП (КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ) =====

import uuid
from flask import g

def get_session_id():
    """Получает или создает session_id для пользователя"""
    if 'session_id' not in flask_session:
        flask_session['session_id'] = str(uuid.uuid4())
        flask_session.permanent = True
    return flask_session['session_id']

@app.route('/api/kp/add', methods=['POST'])
def api_kp_add():
    """Добавляет вариант цены (price_offer) в КП"""
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        price_offer_id = data.get('price_offer_id')
        
        if not product_id or not price_offer_id:
            return jsonify({'success': False, 'error': 'Не указан product_id или price_offer_id'}), 400
        
        session_id = get_session_id()
        db_session = db_manager.get_session_direct()
        
        try:
            # Проверяем существование товара и варианта цены
            result = db_session.execute(text("""
                SELECT p.name, po.quantity, po.route
                FROM products p
                JOIN price_offers po ON po.product_id = p.id
                WHERE p.id = :product_id AND po.id = :price_offer_id
            """), {'product_id': product_id, 'price_offer_id': price_offer_id})
            
            row = result.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Товар или вариант цены не найден'}), 404
            
            # Добавляем в КП
            db_session.execute(text("""
                INSERT INTO kp_items (session_id, product_id, price_offer_id)
                VALUES (:session_id, :product_id, :price_offer_id)
                ON CONFLICT (session_id, price_offer_id) DO NOTHING
            """), {'session_id': session_id, 'product_id': product_id, 'price_offer_id': price_offer_id})
            db_session.commit()
            
            # Количество товаров в КП
            result = db_session.execute(text("SELECT COUNT(*) FROM kp_items WHERE session_id = :session_id"), {'session_id': session_id})
            kp_count = result.scalar()
            
            return jsonify({
                'success': True,
                'message': f'Добавлено в КП: {row[0]} ({row[1]} шт, {row[2]})',
                'kp_count': kp_count
            })
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kp/remove/<int:kp_item_id>', methods=['DELETE'])
def api_kp_remove(kp_item_id):
    """Удаляет товар из КП"""
    
    try:
        session_id = get_session_id()
        db_session = db_manager.get_session_direct()
        
        try:
            db_session.execute(text("""
                DELETE FROM kp_items
                WHERE id = :kp_item_id AND session_id = :session_id
            """), {'kp_item_id': kp_item_id, 'session_id': session_id})
            db_session.commit()
            
            result = db_session.execute(text("SELECT COUNT(*) FROM kp_items WHERE session_id = :session_id"), {'session_id': session_id})
            kp_count = result.scalar()
            
            return jsonify({'success': True, 'message': 'Удалено из КП', 'kp_count': kp_count})
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kp', methods=['GET'])
def api_kp_get():
    """Получает все товары в КП"""
    
    try:
        session_id = get_session_id()
        db_session = db_manager.get_session_direct()
        
        try:
            result = db_session.execute(text("""
                SELECT 
                    ki.id as kp_item_id,
                    ki.quantity,
                    ki.added_at,
                    p.id as product_id,
                    p.name as product_name,
                    p.description,
                    po.id as price_offer_id,
                    po.quantity as offer_quantity,
                    po.route,
                    po.price_usd,
                    po.price_rub,
                    po.delivery_days,
                    (SELECT image_url 
                     FROM product_images pi 
                     WHERE pi.product_id = p.id 
                     AND pi.image_url IS NOT NULL
                     ORDER BY CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END, pi.id
                     LIMIT 1) as image_url,
                    (SELECT image_filename 
                     FROM product_images pi 
                     WHERE pi.product_id = p.id 
                     AND pi.image_filename IS NOT NULL
                     ORDER BY CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END, pi.id
                     LIMIT 1) as image_filename
                FROM kp_items ki
                JOIN products p ON p.id = ki.product_id
                JOIN price_offers po ON po.id = ki.price_offer_id
                WHERE ki.session_id = :session_id
                ORDER BY ki.added_at DESC
            """), {'session_id': session_id})
            
            kp_items = []
            for row in result:
                # Формируем URL изображения
                image_url = row[12]
                if not image_url and row[13]:
                    image_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{row[13]}"
                
                kp_items.append({
                    'kp_item_id': row[0],
                    'quantity': row[1],
                    'added_at': row[2].isoformat() if row[2] else None,
                    'product': {
                        'id': row[3],
                        'name': row[4],
                        'description': row[5],
                        'image_url': image_url
                    },
                    'price_offer': {
                        'id': row[6],
                        'quantity': row[7],
                        'route': row[8],
                        'price_usd': float(row[9]) if row[9] else None,
                        'price_rub': float(row[10]) if row[10] else None,
                        'delivery_days': row[11]
                    }
                })
            
            return jsonify({'success': True, 'kp_items': kp_items, 'total_items': len(kp_items)})
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kp/clear', methods=['DELETE'])
def api_kp_clear():
    """Очищает весь КП"""
    
    try:
        session_id = get_session_id()
        db_session = db_manager.get_session_direct()
        
        try:
            db_session.execute(text("DELETE FROM kp_items WHERE session_id = :session_id"), {'session_id': session_id})
            db_session.commit()
            
            return jsonify({'success': True, 'message': 'КП очищен', 'kp_count': 0})
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/kp/check', methods=['POST'])
def api_kp_check():
    """Проверяет какие price_offer_id уже добавлены в КП"""
    
    try:
        data = request.get_json()
        price_offer_ids = data.get('price_offer_ids', [])
        
        if not price_offer_ids:
            return jsonify({'success': True, 'in_kp': []})
        
        session_id = get_session_id()
        db_session = db_manager.get_session_direct()
        
        try:
            placeholders = ','.join([f':id{i}' for i in range(len(price_offer_ids))])
            params = {'session_id': session_id}
            params.update({f'id{i}': pid for i, pid in enumerate(price_offer_ids)})
            
            result = db_session.execute(text(f"""
                SELECT price_offer_id
                FROM kp_items
                WHERE session_id = :session_id
                AND price_offer_id IN ({placeholders})
            """), params)
            
            in_kp = [row[0] for row in result.fetchall()]
            
            return jsonify({'success': True, 'in_kp': in_kp})
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

print("✅ [APP] API КП зарегистрирован (/api/kp/*)")

# ===== API ДЛЯ ПОИСКА ПО ИЗОБРАЖЕНИЮ =====

@app.route('/api/search-by-image', methods=['POST'])
def api_search_by_image():
    """Поиск товаров по загруженному изображению через Hugging Face CLIP API"""
    
    # Проверяем доступность pgvector БД
    if not PGVECTOR_ENGINE:
        return jsonify({
            'success': False, 
            'error': 'Поиск по изображениям недоступен: отсутствует подключение к БД'
        }), 503
    
    try:
        # Проверка наличия файла
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'Изображение не найдено'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
        
        # Проверка типа файла
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': 'Недопустимый тип файла'}), 400
        
        # Загружаем изображение
        image_bytes = file.read()
        
        # Конвертируем в base64 для API
        import base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Генерируем embedding через Hugging Face Inference API
        print(f"🔍 [IMAGE SEARCH] Генерация embedding через Hugging Face API...")
        
        HF_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
        if not HF_API_TOKEN:
            return jsonify({
                'success': False,
                'error': 'Не настроен HUGGINGFACE_API_TOKEN. Добавьте в переменные окружения.'
            }), 503
        
        import requests
        
        # Используем Hugging Face Inference API для CLIP
        hf_url = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # Отправляем изображение
        response = requests.post(
            hf_url,
            headers=headers,
            data=image_bytes,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ [IMAGE SEARCH] Hugging Face API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return jsonify({
                'success': False,
                'error': f'Ошибка API: {response.status_code}. Попробуйте позже.'
            }), 503
        
        # Получаем embedding из ответа
        result = response.json()
        
        # Hugging Face возвращает embedding напрямую для feature extraction
        if isinstance(result, list) and len(result) > 0:
            query_embedding = result[0]
        else:
            print(f"❌ [IMAGE SEARCH] Неожиданный формат ответа: {result}")
            return jsonify({
                'success': False,
                'error': 'Неожиданный формат ответа от API'
            }), 500
        
        # Ищем похожие изображения в pgvector БД
        query_vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        with PGVECTOR_ENGINE.connect() as conn:
            from sqlalchemy import text
            sql_query = f"""
                SELECT 
                    ie.product_id,
                    ie.image_url,
                    1 - (ie.image_embedding <=> '{query_vector_str}'::vector) as similarity
                FROM image_embeddings ie
                WHERE 1 - (ie.image_embedding <=> '{query_vector_str}'::vector) >= 0.3
                ORDER BY ie.image_embedding <=> '{query_vector_str}'::vector
                LIMIT 50
            """
            results = conn.execute(text(sql_query)).fetchall()
        
        # Извлекаем product_ids
        product_ids = [row[0] for row in results]
        
        print(f"✅ [IMAGE SEARCH] Найдено {len(product_ids)} похожих товаров")
        
        if not product_ids:
            return jsonify({
                'success': False, 
                'error': 'Не найдено похожих товаров. Попробуйте другое изображение.'
            }), 404
        
        # Сохраняем product_ids в сессии
        search_id = str(uuid.uuid4())
        flask_session[f'image_search_{search_id}'] = product_ids
        
        return jsonify({
            'success': True, 
            'search_id': search_id,
            'count': len(product_ids)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

print("✅ [APP] API поиска по изображению зарегистрирован (/api/search-by-image)")

if __name__ == '__main__':
    # Получаем порт из переменной окружения (Railway использует PORT)
    port = int(os.getenv('PORT', 5000))
    
    print("🚀 Запускаю веб-интерфейс для деплоя...")
    print(f"📁 Изображения: {IMAGES_DIR}")
    print(f"🌐 Порт: {port}")
    
    # Используем waitress для production (более надежный чем Flask dev server)
    try:
        from waitress import serve
        print("✅ Используем Waitress production server")
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        print("⚠️ Waitress не найден, используем Flask dev server")
        app.run(debug=False, host='0.0.0.0', port=port)
