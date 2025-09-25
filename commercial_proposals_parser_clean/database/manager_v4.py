"""
Менеджер базы данных для v4 структуры
"""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import and_, or_, desc, asc, create_engine
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json

from .models_v4 import (
    Base, SheetMetadata, Product, PriceOffer, ProductImage, ParsingLog,
    serialize_characteristics, deserialize_characteristics,
    format_price, format_quantity, format_delivery_time
)
from config import DATABASE_URL_V4

class CommercialProposalsDB:
    """Менеджер базы данных для коммерческих предложений v4"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Создаем таблицы
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.Session()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        session = self.get_session()
        try:
            total_products = session.query(Product).count()
            total_price_offers = session.query(PriceOffer).count()
            total_images = session.query(ProductImage).count()
            total_sheets = session.query(SheetMetadata).count()
            
            return {
                'total_products': total_products,
                'total_price_offers': total_price_offers,
                'total_images': total_images,
                'total_sheets': total_sheets
            }
        finally:
            session.close()
    
    def get_all_products_with_details(self, limit: int = 100, offset: int = 0):
        """Получение всех товаров с полной информацией"""
        session = self.get_session()
        try:
            products = session.query(Product).offset(offset).limit(limit).all()
            result = []
            
            for product in products:
                # Получаем ценовые предложения
                price_offers = session.query(PriceOffer).filter(
                    PriceOffer.product_id == product.id
                ).all()
                
                # Получаем изображения
                images = session.query(ProductImage).filter(
                    ProductImage.product_id == product.id
                ).all()
                
                result.append((product, price_offers, images))
            
            return result
        finally:
            session.close()
    
    def get_product_with_details(self, product_id: int):
        """Получение товара с полной информацией по ID"""
        session = self.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return None
            
            # Получаем ценовые предложения
            price_offers = session.query(PriceOffer).filter(
                PriceOffer.product_id == product.id
            ).all()
            
            # Получаем изображения
            images = session.query(ProductImage).filter(
                ProductImage.product_id == product.id
            ).all()
            
            return (product, price_offers, images)
        finally:
            session.close()
    
    def search_products(self, query: str, limit: int = 100) -> List[Product]:
        """Поиск товаров по названию и описанию"""
        session = self.get_session()
        try:
            products = session.query(Product).filter(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            return products
        finally:
            session.close()
    
    def get_price_offers(self, product_id: int) -> List[PriceOffer]:
        """Получение ценовых предложений для товара"""
        session = self.get_session()
        try:
            return session.query(PriceOffer).filter(
                PriceOffer.product_id == product_id
            ).all()
        finally:
            session.close()
    
    def get_product_images(self, product_id: int) -> List[ProductImage]:
        """Получение изображений для товара"""
        session = self.get_session()
        try:
            return session.query(ProductImage).filter(
                ProductImage.product_id == product_id
            ).all()
        finally:
            session.close()
    
    def create_product(self, name: str, description: str = None, characteristics: Dict = None, 
                      custom_design: str = None, sheet_id: int = 1) -> Product:
        """Создание нового товара"""
        session = self.get_session()
        try:
            product = Product(
                name=name,
                description=description,
                characteristics=serialize_characteristics(characteristics),
                custom_design=custom_design,
                sheet_id=sheet_id
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
        finally:
            session.close()
    
    def create_price_offer(self, product_id: int, route_name: str, 
                          quantity: int = None, price_usd: float = None, 
                          price_rub: float = None, delivery_time: str = None,
                          sample_price: float = None, sample_time: str = None,
                          sample_price_currency: str = None, is_sample: bool = False,
                          notes: str = None) -> PriceOffer:
        """Создание ценового предложения"""
        session = self.get_session()
        try:
            price_offer = PriceOffer(
                product_id=product_id,
                route_name=route_name,
                quantity=quantity,
                price_usd=price_usd,
                price_rub=price_rub,
                delivery_time=delivery_time,
                sample_price=sample_price,
                sample_time=sample_time,
                sample_price_currency=sample_price_currency,
                is_sample=is_sample,
                notes=notes
            )
            session.add(price_offer)
            session.commit()
            session.refresh(price_offer)
            return price_offer
        finally:
            session.close()
    
    def create_image(self, product_id: int, local_path: str, image_type: str = 'main',
                    file_size: int = None, width: int = None, height: int = None,
                    format: str = None) -> ProductImage:
        """Создание изображения"""
        session = self.get_session()
        try:
            image = ProductImage(
                product_id=product_id,
                local_path=local_path,
                image_type=image_type,
                file_size=file_size,
                width=width,
                height=height,
                format=format
            )
            session.add(image)
            session.commit()
            session.refresh(image)
            return image
        finally:
            session.close()
    
    def create_sheet_metadata(self, sheet_url: str, sheet_title: str):
        """Создание записи о таблице"""
        session = self.get_session()
        try:
            # Извлекаем ID из URL
            if '/d/' in sheet_url:
                parts = sheet_url.split('/d/')
                if len(parts) > 1:
                    sheet_id = parts[1].split('/')[0]
                else:
                    sheet_id = 'unknown'
            else:
                sheet_id = 'unknown'
            
            sheet = SheetMetadata(
                sheet_url=sheet_url,
                sheet_title=sheet_title,
                sheet_id=sheet_id,
                status='processed',
                products_count=0
            )
            session.add(sheet)
            session.commit()
            session.refresh(sheet)
            return sheet.id
        finally:
            session.close()
    
    def group_products_by_name(self, products_with_details):
        """Группировка товаров по названию для объединения вариантов"""
        grouped = {}
        
        for product, price_offers, images in products_with_details:
            key = product.name.strip()
            
            if key not in grouped:
                grouped[key] = {
                    'product': product,
                    'price_offers': [],
                    'images': []
                }
            
            # Объединяем ценовые предложения
            grouped[key]['price_offers'].extend(price_offers)
            
            # Объединяем изображения (избегаем дублирования)
            existing_image_paths = {img.local_path for img in grouped[key]['images']}
            for img in images:
                if img.local_path not in existing_image_paths:
                    grouped[key]['images'].append(img)
        
        # Возвращаем список сгруппированных товаров
        result = []
        for key, data in grouped.items():
            result.append((data['product'], data['price_offers'], data['images']))
        
        return result
    
    def create_product_image(self, product_id: int, image_path: str, image_type: str = 'main') -> ProductImage:
        """Создание изображения товара"""
        session = self.get_session()
        try:
            product_image = ProductImage(
                product_id=product_id,
                local_path=image_path,
                image_type=image_type
            )
            session.add(product_image)
            session.commit()
            session.refresh(product_image)
            return product_image
        finally:
            session.close()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        session = self.get_session()
        try:
            return session.query(Product).filter(Product.id == product_id).first()
        finally:
            session.close()
    
    def get_price_offers_by_product_id(self, product_id: int) -> List[PriceOffer]:
        """Получение ценовых предложений по ID товара"""
        session = self.get_session()
        try:
            return session.query(PriceOffer).filter(PriceOffer.product_id == product_id).all()
        finally:
            session.close()
    
    def get_images_by_product_id(self, product_id: int) -> List[ProductImage]:
        """Получение изображений по ID товара"""
        session = self.get_session()
        try:
            return session.query(ProductImage).filter(ProductImage.product_id == product_id).all()
        finally:
            session.close()
    
    def get_product_with_details(self, product_id: int) -> Optional[Tuple[Product, List[PriceOffer], List[ProductImage]]]:
        """Получение товара с полной информацией по ID"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        price_offers = self.get_price_offers_by_product_id(product_id)
        images = self.get_images_by_product_id(product_id)
        
        return (product, price_offers, images)
    
    def get_product_with_sheet_info(self, product_id: int) -> Optional[Tuple[Product, List[PriceOffer], List[ProductImage], SheetMetadata]]:
        """Получение товара с полной информацией и данными о таблице по ID"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        price_offers = self.get_price_offers_by_product_id(product_id)
        images = self.get_images_by_product_id(product_id)
        
        # Получаем информацию о таблице
        session = self.get_session()
        try:
            sheet_metadata = session.query(SheetMetadata).filter(SheetMetadata.id == product.sheet_id).first()
            return (product, price_offers, images, sheet_metadata)
        finally:
            session.close()

# Создаем глобальный экземпляр менеджера базы данных
DatabaseManager = CommercialProposalsDB(DATABASE_URL_V4)
