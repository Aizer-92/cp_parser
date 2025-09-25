#!/usr/bin/env python3
"""
Веб-интерфейс для Промо-Калькулятора с PostgreSQL (исправленная версия)
"""

import psycopg2
from pathlib import Path
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from typing import Optional, List, Dict, Any
import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
from fts_module.fts_search import FullTextSearch

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(title="Промо-Калькулятор PostgreSQL", version="9.0.0")

# Настройка шаблонов и статических файлов
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory="templates")

static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProductViewerPG:
    """Веб-интерфейс для работы с PostgreSQL"""
    
    def __init__(self):
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'promo_calculator'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }
        
        # Инициализируем модуль полнотекстового поиска
        self.fts = FullTextSearch(self.pg_config)
        
        # Загружаем модель для векторного поиска
        try:
            self.vector_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("✅ Векторная модель загружена")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки векторной модели: {e}")
            self.vector_model = None
    
    def get_connection(self):
        """Создание соединения с PostgreSQL с правильной кодировкой"""
        conn = psycopg2.connect(**self.pg_config)
        conn.set_client_encoding('UTF8')
        return conn
    
    def safe_decode(self, text):
        """Безопасное декодирование текста с обработкой ошибок кодировки"""
        if text is None:
            return ""
        
        if isinstance(text, str):
            return text
        
        try:
            return text.decode('utf-8')
        except (UnicodeDecodeError, AttributeError) as e:
            try:
                return text.decode('latin-1')
            except (UnicodeDecodeError, AttributeError):
                try:
                    return str(text, errors='replace')
                except:
                    return str(text)
    
    def _enrich_product_data(self, product_dict):
        """Дополнение данных товара информацией о ценах и изображениях"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Получаем характеристики
            cursor.execute("""
                SELECT spec_name, spec_value, spec_type
                FROM specifications 
                WHERE product_id = %s
                ORDER BY id
            """, (product_dict['id'],))
            specs = cursor.fetchall()
            product_dict['specifications'] = [
                {'name': self.safe_decode(s[0]), 'value': self.safe_decode(s[1]), 'type': self.safe_decode(s[2])} 
                for s in specs
            ]
            
            # Получаем изображения
            cursor.execute("""
                SELECT image_url
                FROM images 
                WHERE product_id = %s
                ORDER BY is_primary DESC, id
            """, (product_dict['id'],))
            images = cursor.fetchall()
            all_images = [self.safe_decode(img[0]) for img in images if img[0]]
            product_dict['images'] = all_images
            product_dict['main_image'] = all_images[0] if all_images else ''
            
            # Получаем варианты цен (только 3 для листинга, исключая образцы)
            cursor.execute("""
                SELECT variant_name, price_cny, price_rub, moq
                FROM product_variants 
                WHERE product_id = %s AND moq > 1
                ORDER BY price_cny ASC
                LIMIT 3
            """, (product_dict['id'],))
            variants = cursor.fetchall()
            product_dict['price_variants'] = [
                {
                    'name': self.safe_decode(v[0]), 
                    'price_cny': v[1], 
                    'price_rub': v[2], 
                    'moq': v[3]
                } 
                for v in variants
            ]
            
            # Добавляем минимальную и максимальную цену для совместимости
            if variants:
                product_dict['price_cny_min'] = min(v[1] for v in variants if v[1])
                product_dict['price_cny_max'] = max(v[1] for v in variants if v[1])
                product_dict['price_rub_min'] = min(v[2] for v in variants if v[2])
                product_dict['price_rub_max'] = max(v[2] for v in variants if v[2])
            else:
                product_dict['price_cny_min'] = 0
                product_dict['price_cny_max'] = 0
                product_dict['price_rub_min'] = 0
                product_dict['price_rub_max'] = 0
            
            # Добавляем поля для совместимости с SQLite структурой
            product_dict['price_usd_min'] = round(product_dict['price_cny_min'] / 7.2, 2) if product_dict['price_cny_min'] else 0
            product_dict['price_usd_max'] = round(product_dict['price_cny_max'] / 7.2, 2) if product_dict['price_cny_max'] else 0
            
            return product_dict
            
        except Exception as e:
            logger.error(f"Ошибка дополнения данных товара {product_dict['id']}: {e}")
            return product_dict
        finally:
            cursor.close()
            conn.close()
    
    def get_products(self, page: int = 1, limit: int = 25, search: str = "", 
                     vendor: str = "", has_specifications: bool = None, 
                     has_images: bool = None):
        """Получение списка товаров с фильтрацией"""
        
        offset = (page - 1) * limit
        
        # Если есть поисковый запрос, используем FTS модуль
        if search.strip():
            try:
                fts_products, total_count = self.fts.search_products(search, limit, offset)
                
                # Применяем дополнительные фильтры к результатам FTS
                filtered_products = []
                for product in fts_products:
                    # Фильтр по поставщику
                    if vendor.strip() and vendor.lower() not in (product.get('vendor', '') or '').lower():
                        continue
                    
                    # Фильтр по наличию характеристик
                    if has_specifications is not None and product.get('has_specifications') != has_specifications:
                        continue
                    
                    # Фильтр по наличию изображений
                    if has_images is not None and product.get('has_images') != has_images:
                        continue
                    
                    filtered_products.append(product)
                
                # Пересчитываем total_count с учетом фильтров
                if vendor.strip() or has_specifications is not None or has_images is not None:
                    # Если есть дополнительные фильтры, делаем точный подсчет
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    
                    count_query = """
                        SELECT COUNT(*) FROM products p
                        WHERE p.search_vector @@ plainto_tsquery('russian', %s)
                    """
                    count_params = [search]
                    
                    if vendor.strip():
                        count_query += " AND p.vendor ILIKE %s"
                        count_params.append(f"%{vendor}%")
                    
                    if has_specifications is not None:
                        count_query += " AND p.has_specifications = %s"
                        count_params.append(has_specifications)
                    
                    if has_images is not None:
                        count_query += " AND p.has_images = %s"
                        count_params.append(has_images)
                    
                    cursor.execute(count_query, count_params)
                    total_count = cursor.fetchone()[0]
                    
                    cursor.close()
                    conn.close()
                
                # Дополняем данные о ценах и изображениях
                result_products = []
                for product in filtered_products:
                    enriched_product = self._enrich_product_data(product)
                    result_products.append(enriched_product)
                
                return {
                    'products': result_products,
                    'total_count': total_count,
                    'page': page,
                    'limit': limit,
                    'total_pages': (total_count + limit - 1) // limit
                }
                
            except Exception as e:
                logger.error(f"Ошибка FTS поиска: {e}")
                # Fallback к обычному поиску
        
        # Обычный поиск без FTS
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Базовый запрос
        query = """
            SELECT p.id, p.offer_id, p.title, p.original_title, p.vendor, 
                   p.has_specifications, p.has_images, p.moq_min, p.moq_max,
                   p.brand, p.description, p.lead_time, p.source_url, p.source_databases
            FROM products p
            WHERE 1=1
        """
        params = []
        
        # Поиск по тексту (fallback к LIKE)
        if search.strip():
            query += " AND (p.title ILIKE %s OR p.description ILIKE %s OR p.original_title ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Фильтр по поставщику
        if vendor.strip():
            query += " AND p.vendor ILIKE %s"
            params.append(f"%{vendor}%")
        
        # Фильтр по наличию характеристик
        if has_specifications is not None:
            query += " AND p.has_specifications = %s"
            params.append(has_specifications)
        
        # Фильтр по наличию изображений
        if has_images is not None:
            query += " AND p.has_images = %s"
            params.append(has_images)
        
        # Сортировка и пагинация
        query += """
            ORDER BY p.id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        try:
            cursor.execute(query, params)
            products = cursor.fetchall()
            
            # Обрабатываем результаты
            result_products = []
            for product in products:
                try:
                    product_dict = {
                        'id': product[0],
                        'offer_id': self.safe_decode(product[1]),
                        'title': self.safe_decode(product[2]),
                        'original_title': self.safe_decode(product[3]),
                        'vendor': self.safe_decode(product[4]),
                        'currency': 'CNY',  # По умолчанию CNY
                        'main_image': '',  # Будет получено из images
                        'has_specifications': product[5],
                        'has_images': product[6],
                        'brand': self.safe_decode(product[7]),
                        'description': self.safe_decode(product[8]),
                        'moq_min': 0,  # Будет получено из product_variants
                        'moq_max': 0,  # Будет получено из product_variants
                        'lead_time': self.safe_decode(product[9]),
                        'source_url': self.safe_decode(product[10]),
                        'source_databases': self.safe_decode(product[11])
                    }
                    
                    # Получаем характеристики
                    try:
                        cursor.execute("""
                            SELECT spec_name, spec_value, spec_type
                            FROM specifications 
                            WHERE product_id = %s
                            ORDER BY id
                        """, (product_dict['id'],))
                        specs = cursor.fetchall()
                        product_dict['specifications'] = [
                            {'name': self.safe_decode(s[0]), 'value': self.safe_decode(s[1]), 'type': self.safe_decode(s[2])} 
                            for s in specs
                        ]
                    except Exception as e:
                        logger.error(f"Ошибка получения характеристик для товара {product_dict['id']}: {e}")
                        product_dict['specifications'] = []
                    
                    # Получаем изображения
                    try:
                        cursor.execute("""
                            SELECT image_url
                            FROM images 
                            WHERE product_id = %s
                            ORDER BY is_primary DESC, id
                        """, (product_dict['id'],))
                        images = cursor.fetchall()
                        all_images = [self.safe_decode(img[0]) for img in images if img[0]]
                        product_dict['images'] = all_images
                        product_dict['main_image'] = all_images[0] if all_images else ''
                    except Exception as e:
                        logger.error(f"Ошибка получения изображений для товара {product_dict['id']}: {e}")
                        product_dict['images'] = []
                    
                    # Получаем варианты цен (только 3 для листинга, исключая образцы)
                    try:
                        cursor.execute("""
                            SELECT variant_name, price_cny, price_rub, moq
                            FROM product_variants 
                            WHERE product_id = %s AND moq > 1
                            ORDER BY price_cny ASC
                            LIMIT 3
                        """, (product_dict['id'],))
                        variants = cursor.fetchall()
                        product_dict['price_variants'] = [
                            {
                                'name': self.safe_decode(v[0]), 
                                'price_cny': v[1], 
                                'price_rub': v[2], 
                                'moq': v[3]
                            } 
                            for v in variants
                        ]
                        # Добавляем минимальную и максимальную цену для совместимости
                        if variants:
                            product_dict['price_cny_min'] = min(v[1] for v in variants if v[1])
                            product_dict['price_cny_max'] = max(v[1] for v in variants if v[1])
                            product_dict['price_rub_min'] = min(v[2] for v in variants if v[2])
                            product_dict['price_rub_max'] = max(v[2] for v in variants if v[2])
                        else:
                            product_dict['price_cny_min'] = 0
                            product_dict['price_cny_max'] = 0
                            product_dict['price_rub_min'] = 0
                            product_dict['price_rub_max'] = 0
                        
                        # Добавляем поля для совместимости с SQLite структурой
                        product_dict['price_usd_min'] = round(product_dict['price_cny_min'] / 7.2, 2) if product_dict['price_cny_min'] else 0
                        product_dict['price_usd_max'] = round(product_dict['price_cny_max'] / 7.2, 2) if product_dict['price_cny_max'] else 0
                    except Exception as e:
                        logger.error(f"Ошибка получения вариантов цен для товара {product_dict['id']}: {e}")
                        product_dict['price_variants'] = []
                        product_dict['price_cny_min'] = 0
                        product_dict['price_cny_max'] = 0
                        product_dict['price_rub_min'] = 0
                        product_dict['price_rub_max'] = 0
                        product_dict['price_usd_min'] = 0
                        product_dict['price_usd_max'] = 0
                    
                    result_products.append(product_dict)
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки товара {product[0]}: {e}")
                    continue
            
            # Получаем общее количество товаров
            count_query = """
                SELECT COUNT(*)
                FROM products p
                WHERE 1=1
            """
            count_params = []
            
            if search.strip():
                count_query += " AND p.search_vector @@ plainto_tsquery('russian', %s)"
                count_params.append(search)
            
            if vendor.strip():
                count_query += " AND p.vendor ILIKE %s"
                count_params.append(f"%{vendor}%")
            
            if has_specifications is not None:
                count_query += " AND p.has_specifications = %s"
                count_params.append(has_specifications)
            
            if has_images is not None:
                count_query += " AND p.has_images = %s"
                count_params.append(has_images)
            
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'products': result_products,
                'total_count': total_count,
                'page': page,
                'limit': limit,
                'total_pages': (total_count + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения товаров: {e}")
            cursor.close()
            conn.close()
            return {
                'products': [],
                'total_count': 0,
                'page': page,
                'limit': limit,
                'total_pages': 0
            }
    
    def get_product_by_id(self, product_id: int):
        """Получение товара по ID"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT p.id, p.offer_id, p.title, p.original_title, p.vendor, 
                       p.has_specifications, p.has_images, p.moq_min, p.moq_max,
                       p.brand, p.description, p.lead_time, p.source_url, p.source_databases
                FROM products p
                WHERE p.id = %s
            """, (product_id,))
            
            product = cursor.fetchone()
            if not product:
                return None
            
            product_dict = {
                'id': product[0],
                'offer_id': self.safe_decode(product[1]),
                'title': self.safe_decode(product[2] or product[3]),
                'original_title': self.safe_decode(product[3]),
                'vendor': self.safe_decode(product[4]),
                'currency': 'CNY',  # По умолчанию CNY
                'main_image': '',  # Будет получено из images
                'has_specifications': product[5],
                'has_images': product[6],
                'moq_min': product[7] or 0,  # Из базы данных
                'moq_max': product[8] or 0,  # Из базы данных
                'brand': self.safe_decode(product[9]),
                'description': self.safe_decode(product[10]),
                'lead_time': self.safe_decode(product[11]),
                'source_url': self.safe_decode(product[12]),
                'source_databases': self.safe_decode(product[13])
            }
            
            # Получаем характеристики
            cursor.execute("""
                SELECT spec_name, spec_value, spec_type
                FROM specifications 
                WHERE product_id = %s
                ORDER BY id
            """, (product_id,))
            specs = cursor.fetchall()
            product_dict['specifications'] = [
                {'name': self.safe_decode(s[0]), 'value': self.safe_decode(s[1]), 'type': self.safe_decode(s[2])} 
                for s in specs
            ]
            
            # Получаем изображения
            cursor.execute("""
                SELECT image_url
                FROM images 
                WHERE product_id = %s
                ORDER BY is_primary DESC, id
            """, (product_id,))
            images = cursor.fetchall()
            all_images = [self.safe_decode(img[0]) for img in images if img[0]]
            product_dict['images'] = all_images
            product_dict['main_image'] = all_images[0] if all_images else ''
            
            # Получаем варианты товара с полными данными
            cursor.execute("""
                SELECT variant_name, price_cny, price_rub, price_usd, moq, 
                       transport_tariff, quantity_in_box, box_width, box_height, box_length,
                       box_weight, item_weight, cargo_density, cost_price, markup_percent
                FROM product_variants 
                WHERE product_id = %s
                ORDER BY price_cny ASC
            """, (product_id,))
            variants = cursor.fetchall()
            product_dict['variants'] = [
                {
                    'variant_name': self.safe_decode(v[0]), 
                    'price_cny': v[1], 
                    'price_rub': v[2], 
                    'price_usd': v[3],
                    'moq': v[4],
                    'transport_tariff': v[5],
                    'quantity_in_box': v[6],
                    'box_width': v[7],
                    'box_height': v[8],
                    'box_length': v[9],
                    'box_weight': v[10],
                    'item_weight': v[11],
                    'cargo_density': v[12],
                    'cost_price': v[13],
                    'markup_percent': v[14]
                } 
                for v in variants
            ]
            # Добавляем варианты цен для совместимости
            product_dict['price_variants'] = product_dict['variants']
            # Добавляем all_images для совместимости с шаблоном
            product_dict['all_images'] = product_dict['images']
            
            # Добавляем недостающие поля для детальной карточки
            if variants:
                product_dict['price_cny_min'] = min(v[1] for v in variants if v[1])
                product_dict['price_cny_max'] = max(v[1] for v in variants if v[1])
                product_dict['price_rub_min'] = min(v[2] for v in variants if v[2])
                product_dict['price_rub_max'] = max(v[2] for v in variants if v[2])
            else:
                product_dict['price_cny_min'] = 0
                product_dict['price_cny_max'] = 0
                product_dict['price_rub_min'] = 0
                product_dict['price_rub_max'] = 0
            
            # Добавляем поля для совместимости с SQLite структурой
            product_dict['price_usd_min'] = round(product_dict['price_cny_min'] / 7.2, 2) if product_dict['price_cny_min'] else 0
            product_dict['price_usd_max'] = round(product_dict['price_cny_max'] / 7.2, 2) if product_dict['price_cny_max'] else 0
            
            cursor.close()
            conn.close()
            
            return product_dict
            
        except Exception as e:
            logger.error(f"Ошибка получения товара {product_id}: {e}")
            cursor.close()
            conn.close()
            return None
    
    def get_vendors(self):
        """Получение списка поставщиков"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT vendor FROM products 
            WHERE vendor IS NOT NULL AND vendor != ''
            ORDER BY vendor
        """)
        
        vendors = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return vendors
    
    def get_statistics(self):
        """Получение статистики"""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE has_specifications = TRUE")
        products_with_specs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE has_images = TRUE")
        products_with_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM specifications")
        total_specs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM images")
        total_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_variants")
        total_variants = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'total_products': total_products,
            'products_with_specs': products_with_specs,
            'products_with_images': products_with_images,
            'total_specifications': total_specs,
            'total_images': total_images,
            'total_variants': total_variants
        }

# Создаем экземпляр
viewer = ProductViewerPG()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, 
                page: int = Query(1, ge=1),
                search: str = Query(""),
                vendor: str = Query(""),
                has_specifications: str = Query(""),
                has_images: str = Query("")):
    """Главная страница"""
    
    try:
        # Преобразование строковых значений в boolean
        has_specs = None
        has_imgs = None
        
        if has_specifications.lower() == 'true':
            has_specs = True
        elif has_specifications.lower() == 'false':
            has_specs = False
        
        if has_images.lower() == 'true':
            has_imgs = True
        elif has_images.lower() == 'false':
            has_imgs = False
        
        # Получаем данные
        data = viewer.get_products(
            page=page,
            search=search,
            vendor=vendor,
            has_specifications=has_specs,
            has_images=has_imgs
        )
        
        # Получаем список поставщиков
        vendors = viewer.get_vendors()
        
        # Получаем статистику
        stats = viewer.get_statistics()
        
        return templates.TemplateResponse("final_index.html", {
            "request": request,
            "products": data['products'],
            "total_count": data['total_count'],
            "page": data['page'],
            "total_pages": data['total_pages'],
            "search": search,
            "vendor": vendor,
            "has_specifications": has_specifications,
            "has_images": has_images,
            "vendors": vendors,
            "stats": stats,
            "filters": {
                "search": search,
                "vendor": vendor,
                "has_specifications": has_specifications,
                "has_images": has_images,
                "min_price": "",
                "max_price": ""
            },
            "pagination": {
                "page": data['page'],
                "total_pages": data['total_pages']
            },
            "categories": {
                "main_categories": {},
                "subcategories": {},
                "detailed_categories": {}
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка главной страницы: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    """Страница товара"""
    
    try:
        product = viewer.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return templates.TemplateResponse("final_product_detail.html", {
            "request": request,
            "product": product
        })
        
    except Exception as e:
        logger.error(f"Ошибка страницы товара {product_id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/api/products")
async def api_products(page: int = Query(1, ge=1),
                      limit: int = Query(25, ge=1, le=100),
                      search: str = Query(""),
                      vendor: str = Query(""),
                      has_specifications: bool = Query(None),
                      has_images: bool = Query(None)):
    """API для получения товаров"""
    
    try:
        data = viewer.get_products(
            page=page,
            limit=limit,
            search=search,
            vendor=vendor,
            has_specifications=has_specifications,
            has_images=has_images
        )
        
        return data
        
    except Exception as e:
        logger.error(f"Ошибка API товаров: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/product/{product_id}")
async def api_product(product_id: int):
    """API для получения товара по ID"""
    
    try:
        product = viewer.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return product
        
    except Exception as e:
        logger.error(f"Ошибка API товара {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def api_statistics():
    """API для получения статистики"""
    
    try:
        stats = viewer.get_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка API статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
