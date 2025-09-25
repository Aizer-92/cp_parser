"""
FastAPI приложение для каталога товаров v4
"""

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional
import os

# Импорты для работы с базой данных
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

# Создаем приложение
app = FastAPI(title="Каталог товаров v4", version="4.0.0")

# Настройка шаблонов и статических файлов
templates = Jinja2Templates(directory="web_app_v4/templates")
app.mount("/static", StaticFiles(directory="web_app_v4/static"), name="static")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Подключение к базе данных
db = CommercialProposalsDB(DATABASE_URL_V4)

def group_products_by_name(products_with_details):
    """Группировка товаров - показываем все товары без группировки"""
    result = []
    
    for product, price_offers, images in products_with_details:
        # Сортируем изображения - основные сначала
        images.sort(key=lambda x: (x.image_type != 'main', x.id))
        
        # Создаем отображаемое название с ID
        if product.name.strip() == "Ежедневник":
            quantities = [po.quantity for po in price_offers if po.quantity is not None]
            if quantities:
                min_quantity = min(quantities)
                max_quantity = max(quantities)
                if min_quantity == max_quantity:
                    product.display_name = f"Ежедневник #{product.id} (тираж: {min_quantity:,} шт)"
                else:
                    product.display_name = f"Ежедневник #{product.id} (тираж: {min_quantity:,}-{max_quantity:,} шт)"
            else:
                product.display_name = f"Ежедневник #{product.id}"
        else:
            product.display_name = f"{product.name} #{product.id}"
        
        # Добавляем все товары без группировки
        result.append((product, price_offers, images))
    
    return result

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    # Получаем статистику
    stats = db.get_statistics()
    
    # Получаем последние товары с полной информацией
    products_with_details = db.get_all_products_with_details(limit=50)
    
    # Группируем товары по названию
    grouped_products = group_products_by_name(products_with_details)
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "stats": stats,
        "products": grouped_products
    })

@app.get("/products", response_class=HTMLResponse)
async def products(request: Request,
                  search: Optional[str] = Query(None),
                  route_name: Optional[str] = Query(None),
                  min_price: Optional[float] = Query(None),
                  max_price: Optional[float] = Query(None)):
    """Страница каталога товаров"""
    
    # Получаем товары
    if search:
        products = db.search_products(search)
        products_with_details = []
        for product in products:
            price_offers = db.get_price_offers(product.id)
            images = db.get_product_images(product.id)
            products_with_details.append((product, price_offers, images))
    else:
        products_with_details = db.get_all_products_with_details(limit=50)
    
    # Группируем товары по названию
    grouped_products = group_products_by_name(products_with_details)
    
    # Фильтрация по маршруту
    if route_name:
        filtered_products = []
        for product, price_offers, images in grouped_products:
            filtered_offers = [po for po in price_offers if po.route_name == route_name]
            if filtered_offers:
                filtered_products.append((product, filtered_offers, images))
        grouped_products = filtered_products
    
    # Фильтрация по цене
    if min_price is not None or max_price is not None:
        filtered_products = []
        for product, price_offers, images in grouped_products:
            filtered_offers = []
            for po in price_offers:
                if po.price_usd is not None:
                    if min_price is not None and po.price_usd < min_price:
                        continue
                    if max_price is not None and po.price_usd > max_price:
                        continue
                    filtered_offers.append(po)
            if filtered_offers:
                filtered_products.append((product, filtered_offers, images))
        grouped_products = filtered_products
    
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": grouped_products,
        "search": search,
        "route_name": route_name,
        "min_price": min_price,
        "max_price": max_price
    })

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    """Детальная страница товара"""
    product_data = db.get_product_with_sheet_info(product_id)
    
    if not product_data:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    product, price_offers, images, sheet_metadata = product_data
    
    # Разделяем ценовые предложения на обычные и образцы
    regular_offers = [po for po in price_offers if not po.is_sample]
    sample_offers = [po for po in price_offers if po.is_sample]
    
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "product": product,
        "price_offers": regular_offers,  # Только обычные предложения
        "sample_offers": sample_offers,  # Отдельно образцы
        "images": images,
        "sheet_metadata": sheet_metadata
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
