#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Современный веб-интерфейс для просмотра результатов парсинга
С поддержкой Tailwind CSS, пагинации и полнотекстового поиска
"""

from flask import Flask, render_template, jsonify, send_from_directory, request
import os
from pathlib import Path
from database.manager import db_manager
from database.models import Project, Product, PriceOffer, ProductImage
from sqlalchemy import or_, func
import math

app = Flask(__name__)

# Настройка путей
PROJECT_ROOT = Path(__file__).parent
STORAGE_DIR = PROJECT_ROOT / "storage"
IMAGES_DIR = STORAGE_DIR / "images"

# Настройки пагинации
PRODUCTS_PER_PAGE = 24
PROJECTS_PER_PAGE = 20

@app.route('/')
def index():
    """Главная страница с общей статистикой"""
    with db_manager.get_session() as session:
        # Получаем статистику
        projects_count = session.query(Project).count()
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
    
    with db_manager.get_session() as session:
        # Подсчитываем общее количество
        total = session.query(Project).count()
        
        # Получаем проекты с пагинацией
        projects = session.query(Project).order_by(
            Project.updated_at.desc()
        ).offset((page - 1) * PROJECTS_PER_PAGE).limit(PROJECTS_PER_PAGE).all()
        
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
        
        return render_template('projects_list.html', projects=projects, pagination=pagination)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Детальная информация о проекте"""
    with db_manager.get_session() as session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            return "Проект не найден", 404
        
        # Получаем товары проекта с ограничением
        products = session.query(Product).filter(
            Product.project_id == project_id
        ).limit(50).all()
        
        # Получаем статистику по проекту
        products_count = session.query(Product).filter(Product.project_id == project_id).count()
        images_count = session.query(ProductImage).join(Product).filter(Product.project_id == project_id).count()
        offers_count = session.query(PriceOffer).join(Product).filter(Product.project_id == project_id).count()
        
        project_stats = {
            'products_count': products_count,
            'images_count': images_count,
            'offers_count': offers_count
        }
        
        return render_template('project_detail.html', 
                             project=project, 
                             products=products, 
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
    """Отдача изображений"""
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
            'completed_projects': session.query(Project).filter(Project.parsing_status == 'completed').count()
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
    # Создаем папку для шаблонов если её нет
    templates_dir = PROJECT_ROOT / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    print("🚀 Запускаю современный веб-интерфейс...")
    print(f"📁 Изображения: {IMAGES_DIR}")
    print(f"🌐 Откройте: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
