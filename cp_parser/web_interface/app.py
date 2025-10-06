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

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, send_from_directory, request

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

# image_proxy не нужен - изображения публично доступны в S3

from datetime import datetime

@app.route('/')
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
            completed_projects = session.query(Project).filter(Project.parsing_status == 'completed').count()
            
            # Получаем последние обработанные проекты
            print("🔍 [DEBUG] Пробуем получить последние проекты через RAW SQL...")
            
            # Используем RAW SQL чтобы обойти проблему с типами
            from sqlalchemy import text
            raw_sql = text("""
                SELECT id, project_name, file_name, google_sheets_url, 
                       manager_name, total_products_found, total_images_found,
                       updated_at, created_at
                FROM projects 
                WHERE parsing_status = 'completed'
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
def products_list():
    """Список товаров с пагинацией и поиском"""
    from sqlalchemy import text
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    with db_manager.get_session() as session:
        # Подсчитываем общее количество с поиском
        if search.strip():
            count_sql = text("""
                SELECT COUNT(*) FROM products 
                WHERE name ILIKE :search OR description ILIKE :search
            """)
            total = session.execute(count_sql, {"search": f"%{search.strip()}%"}).scalar()
            
            # Получаем товары с поиском
            products_sql = text("""
                SELECT id, project_id, name, description, article_number, 
                       sample_price, sample_delivery_time, row_number
                FROM products 
                WHERE name ILIKE :search OR description ILIKE :search
                ORDER BY id DESC 
                LIMIT :limit OFFSET :offset
            """)
            rows = session.execute(products_sql, {
                "search": f"%{search.strip()}%",
                "limit": PRODUCTS_PER_PAGE,
                "offset": (page - 1) * PRODUCTS_PER_PAGE
            }).fetchall()
        else:
            # Без поиска
            total = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
            
            products_sql = text("""
                SELECT id, project_id, name, description, article_number, 
                       sample_price, sample_delivery_time, row_number
                FROM products 
                ORDER BY id DESC 
                LIMIT :limit OFFSET :offset
            """)
            rows = session.execute(products_sql, {
                "limit": PRODUCTS_PER_PAGE,
                "offset": (page - 1) * PRODUCTS_PER_PAGE
            }).fetchall()
        
        # Преобразуем в объекты Product
        products = []
        for row in rows:
            product = Product()
            product.id = row[0]
            product.project_id = row[1]
            product.name = row[2]
            product.description = row[3]
            product.article_number = row[4]
            product.sample_price = float(row[5]) if row[5] is not None else None
            product.sample_delivery_time = int(row[6]) if row[6] is not None else None
            product.row_number = int(row[7]) if row[7] is not None else None
            
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
                             search=search)

@app.route('/projects')
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
            
            # Получаем проекты с поиском
            projects_sql = text("""
                SELECT id, project_name, file_name, google_sheets_url, 
                       manager_name, total_products_found, total_images_found,
                       parsing_status, updated_at, created_at
                FROM projects 
                WHERE project_name ILIKE :search OR table_id ILIKE :search
                ORDER BY id DESC 
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
                SELECT id, project_name, file_name, google_sheets_url, 
                       manager_name, total_products_found, total_images_found,
                       parsing_status, updated_at, created_at
                FROM projects 
                ORDER BY id DESC 
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
def project_detail(project_id):
    """Детальная информация о проекте"""
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Получаем проект
        project_sql = text("""
            SELECT id, project_name, file_name, google_sheets_url, 
                   manager_name, total_products_found, total_images_found,
                   parsing_status, updated_at, created_at
            FROM projects 
            WHERE id = :project_id
        """)
        project_row = session.execute(project_sql, {"project_id": project_id}).fetchone()
        
        if not project_row:
            return "Проект не найден", 404
        
        project = Project()
        project.id = project_row[0]
        project.project_name = project_row[1]
        project.file_name = project_row[2]
        project.google_sheets_url = project_row[3]
        project.manager_name = project_row[4]
        project.total_products_found = int(project_row[5]) if project_row[5] is not None else 0
        project.total_images_found = int(project_row[6]) if project_row[6] is not None else 0
        project.parsing_status = project_row[7]
        # Преобразуем строки в datetime объекты
        project.updated_at = datetime.fromisoformat(str(project_row[8])) if project_row[8] else None
        project.created_at = datetime.fromisoformat(str(project_row[9])) if project_row[9] else None
        
        # Получаем товары проекта с пагинацией
        page = request.args.get('page', 1, type=int)
        
        # Подсчитываем общее количество
        total = session.execute(
            text("SELECT COUNT(*) FROM products WHERE project_id = :project_id"),
            {"project_id": project_id}
        ).scalar()
        
        # Получаем товары
        products_sql = text("""
            SELECT id, project_id, name, description, article_number, 
                   sample_price, sample_delivery_time, row_number
            FROM products 
            WHERE project_id = :project_id
            ORDER BY id DESC 
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
            product.sample_price = float(row[5]) if row[5] is not None else None
            product.sample_delivery_time = int(row[6]) if row[6] is not None else None
            product.row_number = int(row[7]) if row[7] is not None else None
            
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
                offer.price_usd = float(offer_row[2]) if offer_row[2] is not None else None
                offer.price_rub = float(offer_row[3]) if offer_row[3] is not None else None
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
def product_detail(product_id):
    """Детальная информация о товаре"""
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Получаем товар
        product_sql = text("""
            SELECT id, project_id, name, description, article_number, 
                   sample_price, sample_delivery_time, row_number
            FROM products 
            WHERE id = :product_id
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
        product.sample_price = float(product_row[5]) if product_row[5] is not None else None
        product.sample_delivery_time = int(product_row[6]) if product_row[6] is not None else None
        product.row_number = int(product_row[7]) if product_row[7] is not None else None
        
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
            offer.price_usd = float(row[2]) if row[2] is not None else None
            offer.price_rub = float(row[3]) if row[3] is not None else None
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
def api_stats():
    """API для получения статистики"""
    with db_manager.get_session() as session:
        stats = {
            'projects': session.query(Project).count(),
            'products': session.query(Product).count(),
            'offers': session.query(PriceOffer).count(),
            'images': session.query(ProductImage).count(),
            'completed_projects': session.query(Project).filter(
                Project.parsing_status == 'completed'
            ).count()
        }
        return jsonify(stats)

@app.route('/api/search')
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
