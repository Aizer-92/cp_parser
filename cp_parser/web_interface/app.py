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
        recent_projects = session.query(Project).filter(
            Project.parsing_status == 'completed'
        ).order_by(Project.updated_at.desc()).limit(6).all()
        
        stats = {
            'projects': projects_count,
            'products': products_count,
            'offers': offers_count,
            'images': images_count,
            'completed_projects': completed_projects
        }
        
        return render_template('index_new.html', stats=stats, recent_projects=recent_projects)

@app.route('/products')
def products_list():
    """Список товаров с пагинацией и поиском"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    with db_manager.get_session() as session:
        # Базовый запрос
        query = session.query(Product)
        
        # Применяем поиск если есть
        if search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        # Подсчитываем общее количество
        total = query.count()
        
        # Применяем пагинацию
        products = query.order_by(Product.id.desc()).offset(
            (page - 1) * PRODUCTS_PER_PAGE
        ).limit(PRODUCTS_PER_PAGE).all()
        
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
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    with db_manager.get_session() as session:
        # Базовый запрос
        query = session.query(Project)
        
        # Применяем поиск если есть
        if search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Project.project_name.ilike(search_term),
                    Project.table_id.ilike(search_term)
                )
            )
        
        # Подсчитываем общее количество
        total = query.count()
        
        # Применяем пагинацию
        projects = query.order_by(Project.id.desc()).offset(
            (page - 1) * PROJECTS_PER_PAGE
        ).limit(PROJECTS_PER_PAGE).all()
        
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
    with db_manager.get_session() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            return "Проект не найден", 404
        
        # Получаем товары проекта с пагинацией
        page = request.args.get('page', 1, type=int)
        products_query = session.query(Product).filter(Product.project_id == project_id)
        
        # Подсчитываем общее количество
        total = products_query.count()
        
        # Применяем пагинацию
        products = products_query.order_by(Product.id.desc()).offset(
            (page - 1) * PRODUCTS_PER_PAGE
        ).limit(PRODUCTS_PER_PAGE).all()
        
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
            'products_count': session.query(Product).filter(Product.project_id == project_id).count(),
            'offers_count': session.query(PriceOffer).join(Product).filter(Product.project_id == project_id).count(),
            'images_count': session.query(ProductImage).join(Product).filter(Product.project_id == project_id).count()
        }
        
        return render_template('project_detail.html', 
                             project=project, 
                             products=products, 
                             pagination=pagination,
                             project_stats=project_stats)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Детальная информация о товаре"""
    with db_manager.get_session() as session:
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return "Товар не найден", 404
        
        # Получаем все ценовые предложения
        price_offers = session.query(PriceOffer).filter(
            PriceOffer.product_id == product_id
        ).order_by(PriceOffer.quantity).all()
        
        # Получаем все изображения
        images = session.query(ProductImage).filter(
            ProductImage.product_id == product_id
        ).order_by(ProductImage.is_main_image.desc()).all()
        
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
