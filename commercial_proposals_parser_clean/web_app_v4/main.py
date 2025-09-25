"""
Простой веб-интерфейс для просмотра товаров
"""
import sys
from pathlib import Path
import logging
from flask import Flask, render_template, request, jsonify
from sqlalchemy import func, and_, or_

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, PriceOffer, ProductImage, SheetMetadata, ProjectMetadata

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../storage', static_url_path='/storage')

# Отключаем кэширование для статических файлов
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def get_web_image_path(local_path):
    """Преобразует локальный путь к изображению в веб-путь"""
    if not local_path:
        return None
    
    # Обрабатываем разные форматы путей
    if 'storage/images/' in local_path:
        # Извлекаем часть пути после storage/images/
        if '/storage/images/' in local_path:
            # Абсолютный путь
            parts = local_path.split('/storage/images/')
        else:
            # Относительный путь
            parts = local_path.split('storage/images/')
        
        if len(parts) > 1:
            # Добавляем timestamp для предотвращения кэширования
            import time
            timestamp = int(time.time())
            return f'/storage/images/{parts[1]}?v={timestamp}'
    
    return local_path

# Добавляем функции в контекст шаблонов
app.jinja_env.globals['get_web_image_path'] = get_web_image_path

def get_min_price_info(product_id):
    """Получает минимальную цену и тираж для товара"""
    session = DatabaseManager.get_session()
    try:
        # Получаем минимальную цену в USD и RUB (исключаем образцы)
        min_usd = session.query(func.min(PriceOffer.price_usd)).filter(
            and_(
                PriceOffer.product_id == product_id,
                PriceOffer.route_name != 'ОБРАЗЕЦ',  # Исключаем образцы по route_name
                PriceOffer.price_usd.isnot(None),
                PriceOffer.price_usd > 0
            )
        ).scalar()
        
        min_rub = session.query(func.min(PriceOffer.price_rub)).filter(
            and_(
                PriceOffer.product_id == product_id,
                PriceOffer.route_name != 'ОБРАЗЕЦ',  # Исключаем образцы по route_name
                PriceOffer.price_rub.isnot(None),
                PriceOffer.price_rub > 0
            )
        ).scalar()
        
        # Получаем минимальный тираж (исключаем образцы)
        min_quantity = session.query(func.min(PriceOffer.quantity)).filter(
            and_(
                PriceOffer.product_id == product_id,
                PriceOffer.route_name != 'ОБРАЗЕЦ',  # Исключаем образцы по route_name
                PriceOffer.quantity.isnot(None),
                PriceOffer.quantity > 0
            )
        ).scalar()
        
        return {
            'min_price_usd': min_usd,
            'min_price_rub': min_rub,
            'min_quantity': min_quantity
        }
    finally:
        session.close()

@app.route('/')
def index():
    """Главная страница со списком товаров"""
    session = DatabaseManager.get_session()
    try:
        # Получаем все товары с их изображениями
        products = session.query(Product).order_by(Product.name).all()
        
        products_data = []
        for product in products:
            # Получаем главное изображение (первое в столбце A)
            main_image = session.query(ProductImage).filter(
                and_(
                    ProductImage.product_id == product.id,
                    ProductImage.image_type == 'main'
                )
            ).first()
            
            # Получаем количество изображений
            images_count = session.query(ProductImage).filter(
                ProductImage.product_id == product.id
            ).count()
            
            # Получаем минимальные и максимальные цены
            price_info = get_min_price_info(product.id)
            
            # Получаем максимальные значения
            max_usd = session.query(func.max(PriceOffer.price_usd)).filter(
                and_(
                    PriceOffer.product_id == product.id,
                    PriceOffer.route_name != 'ОБРАЗЕЦ',
                    PriceOffer.price_usd.isnot(None),
                    PriceOffer.price_usd > 0
                )
            ).scalar()
            
            max_rub = session.query(func.max(PriceOffer.price_rub)).filter(
                and_(
                    PriceOffer.product_id == product.id,
                    PriceOffer.route_name != 'ОБРАЗЕЦ',
                    PriceOffer.price_rub.isnot(None),
                    PriceOffer.price_rub > 0
                )
            ).scalar()
            
            max_quantity = session.query(func.max(PriceOffer.quantity)).filter(
                and_(
                    PriceOffer.product_id == product.id,
                    PriceOffer.route_name != 'ОБРАЗЕЦ',  # Исключаем образцы по route_name
                    PriceOffer.quantity.isnot(None),
                    PriceOffer.quantity > 0
                )
            ).scalar()
            
            # Получаем время доставки
            delivery_time = session.query(PriceOffer.delivery_time).filter(
                and_(
                    PriceOffer.product_id == product.id,
                    PriceOffer.delivery_time.isnot(None)
                )
            ).first()
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.characteristics,
                'main_image': get_web_image_path(main_image.local_path) if main_image else None,
                'images_count': images_count,
                'min_price_usd': price_info['min_price_usd'],
                'max_price_usd': max_usd,
                'min_price_rub': price_info['min_price_rub'],
                'max_price_rub': max_rub,
                'min_quantity': price_info['min_quantity'],
                'max_quantity': max_quantity,
                'delivery_time': delivery_time[0] if delivery_time else None
            })
        
        # Получаем все таблицы для фильтра
        sheets = session.query(SheetMetadata).filter(SheetMetadata.products_count > 0).all()
        total_products = len(products)
        
        return render_template('index_tailwind.html', 
                             products=products_data,
                             sheets=sheets,
                             total_products=total_products,
                             timestamp=int(__import__('time').time()))
    finally:
        session.close()

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Детальная страница товара"""
    session = DatabaseManager.get_session()
    try:
        # Получаем товар
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return "Товар не найден", 404
        
        # Получаем метаданные таблицы
        sheet_metadata = session.query(SheetMetadata).filter(SheetMetadata.id == product.sheet_id).first()
        
        # Получаем связанную информацию из мастер-таблицы
        project_metadata = None
        if sheet_metadata:
            try:
                # Ищем проект по частичному совпадению sheet_id с URL проекта
                if sheet_metadata.sheet_id and len(sheet_metadata.sheet_id) > 10:
                    project_metadata = session.query(ProjectMetadata).filter(
                        ProjectMetadata.google_sheets_url.contains(sheet_metadata.sheet_id)
                    ).first()
                
                # Если не найден, ищем по точному совпадению URL
                if not project_metadata and sheet_metadata.sheet_url:
                    project_metadata = session.query(ProjectMetadata).filter(
                        ProjectMetadata.google_sheets_url == sheet_metadata.sheet_url
                    ).first()
                
                # Если не найден - оставляем None (пустые поля)
                
                # Исправляем ссылку на Google Sheets - используем URL из проекта
                if project_metadata and project_metadata.google_sheets_url:
                    correct_google_url = project_metadata.google_sheets_url
                else:
                    # Формируем корректную ссылку из sheet_id
                    if sheet_metadata.sheet_id and 'sheet_' in sheet_metadata.sheet_id:
                        sheet_id = sheet_metadata.sheet_id.replace('sheet_', '')
                        correct_google_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
                    else:
                        correct_google_url = sheet_metadata.sheet_url
                        
            except Exception as e:
                logger.warning(f"Could not fetch project metadata: {e}")
                project_metadata = None
                correct_google_url = sheet_metadata.sheet_url if sheet_metadata else None
        
        # Получаем все изображения товара (сначала главные, потом дополнительные)
        images = session.query(ProductImage).filter(
            ProductImage.product_id == product_id
        ).order_by(ProductImage.image_type.desc(), ProductImage.id).all()
        
        # Получаем ВСЕ варианты цен (включая образцы)
        all_price_offers = session.query(PriceOffer).filter(
            PriceOffer.product_id == product_id
        ).order_by(PriceOffer.route_name, PriceOffer.quantity).all()
        
        # Разделяем образцы и обычные варианты
        price_variants = [offer for offer in all_price_offers if offer.route_name != 'ОБРАЗЕЦ']
        sample_offer = next((offer for offer in all_price_offers if offer.route_name == 'ОБРАЗЕЦ'), None)
        
        # Преобразуем пути к изображениям для веб-интерфейса
        web_images = []
        for image in images:
            web_image = {
                'id': image.id,
                'local_path': get_web_image_path(image.local_path),
                'image_type': image.image_type,
                'file_size': image.file_size,
                'width': image.width,
                'height': image.height,
                'format': image.format
            }
            web_images.append(web_image)
        
        return render_template('product_detailed.html', 
                              product=product,
                              images=web_images,
                              price_variants=price_variants,
                              sample_offer=sample_offer,
                              sheet_metadata=sheet_metadata,
                              project_metadata=project_metadata,
                              correct_google_url=correct_google_url)
    finally:
        session.close()

@app.route('/api/products')
def api_products():
    """API для получения списка товаров"""
    session = DatabaseManager.get_session()
    try:
        products = session.query(Product).order_by(Product.name).all()
        
        products_data = []
        for product in products:
            # Получаем главное изображение
            main_image = session.query(ProductImage).filter(
                and_(
                    ProductImage.product_id == product.id,
                    ProductImage.image_type == 'main'
                )
            ).first()
            
            # Получаем минимальные цены
            price_info = get_min_price_info(product.id)
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'characteristics': product.characteristics,
                'main_image': get_web_image_path(main_image.local_path) if main_image else None,
                'min_price_usd': price_info['min_price_usd'],
                'min_price_rub': price_info['min_price_rub'],
                'min_quantity': price_info['min_quantity']
            })
        
        return jsonify(products_data)
    finally:
        session.close()

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса...")
    print("📱 Откройте http://localhost:8001 в браузере")
    app.run(host='0.0.0.0', port=8001, debug=True)