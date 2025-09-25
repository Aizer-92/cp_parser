"""
Модели базы данных v4 - правильная структура:
1. Товары (описание, кастом, фото)
2. Ценовые предложения (маршрут, тираж, цены, сроки)
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ProjectMetadata(Base):
    """Метаданные проектов из мастер-таблицы"""
    __tablename__ = 'project_metadata'
    
    id = Column(Integer, primary_key=True)
    
    # Основные данные проекта
    project_title = Column(Text, nullable=False)  # A: Тираж (на самом деле это название проекта)
    min_quantity = Column(String(200), nullable=True)  # B: Тираж MIN
    max_quantity = Column(String(200), nullable=True)  # C: Тираж MAX
    products_info = Column(Text, nullable=True)  # D: Товары
    min_price_usd = Column(Float, nullable=True)  # E: Минимальная стоимость в $
    max_price_usd = Column(Float, nullable=True)  # F: Максимальная стоимость в $
    min_price_rub = Column(Float, nullable=True)  # G: Минимальная в рублях
    max_price_rub = Column(Float, nullable=True)  # H: Максимальная в рублях
    description = Column(Text, nullable=True)  # I: Описание
    project_name = Column(String(500), nullable=True)  # J: Название
    manager = Column(String(200), nullable=True)  # K: Постановщик
    executors = Column(Text, nullable=True)  # L: Исполнители
    google_sheets_url = Column(String(1000), nullable=True)  # M: Ссылка на GoogleSheets
    creation_date = Column(String(50), nullable=True)  # N: Дата создания (как строка, может быть в разных форматах)
    counterparty = Column(String(300), nullable=True)  # O: Контрагент
    region = Column(String(100), nullable=True)  # P: Регион (РФ/Международная)
    
    # Статус обработки
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, error
    parsed_at = Column(DateTime, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с SheetMetadata
    sheet_metadata_id = Column(Integer, ForeignKey('sheets_metadata.id'), nullable=True)
    sheet_metadata = relationship("SheetMetadata", backref="project_metadata")

class SheetMetadata(Base):
    """Метаданные Google Sheets"""
    __tablename__ = 'sheets_metadata'
    
    id = Column(Integer, primary_key=True)
    sheet_url = Column(String(1000), nullable=False)
    sheet_title = Column(String(500), nullable=False)
    sheet_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), default='pending')
    products_count = Column(Integer, default=0)
    
    # Данные из таблицы просчетов
    project_name = Column(String(500), nullable=True)  # Тираж MAX
    executor = Column(String(200), nullable=True)  # Товары (исполнитель)
    min_price_usd = Column(Float, nullable=True)  # Минимальная стоимость в $
    max_price_usd = Column(Float, nullable=True)  # Максимальная стоимость в $
    min_price_rub = Column(Float, nullable=True)  # Минимальная в рублях
    max_price_rub = Column(Float, nullable=True)  # Максимальная в рублях
    description = Column(Text, nullable=True)  # Описание
    name = Column(String(300), nullable=True)  # Название
    performers = Column(Text, nullable=True)  # Исполнители
    creation_date = Column(DateTime, nullable=True)  # Дата создания
    counterparty = Column(String(200), nullable=True)  # Контрагент
    region = Column(String(100), nullable=True)  # Регион
    
    # Локальный путь к файлу
    local_file_path = Column(String(500), nullable=True)
    
    # Позиции изображений (JSON)
    image_positions = Column(JSON, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    products = relationship("Product", back_populates="sheet_metadata")
    images = relationship("ProductImage", back_populates="sheet")

class Product(Base):
    """Товары - основная информация, описание, кастом, фото"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    characteristics = Column(Text, nullable=True)  # Характеристики товара
    custom_design = Column(String(200), nullable=True)  # Возможность кастомного дизайна
    sheet_id = Column(Integer, ForeignKey('sheets_metadata.id'), nullable=False)
    
    # Диапазон строк товара в Excel файле
    start_row = Column(Integer, nullable=True)  # Начальная строка товара
    end_row = Column(Integer, nullable=True)    # Конечная строка товара
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    sheet_metadata = relationship("SheetMetadata", back_populates="products")
    price_offers = relationship("PriceOffer", back_populates="product", cascade="all, delete-orphan")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

class PriceOffer(Base):
    """Ценовые предложения - маршрут, тираж, цены, сроки"""
    __tablename__ = 'price_offers'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Маршрут доставки
    route_name = Column(String(100), nullable=False)  # ЖД, АВИА, Контейнер, Образец
    
    # Тираж
    quantity = Column(Integer, nullable=True)  # Тираж для этого предложения
    
    # Цены
    price_usd = Column(Float, nullable=True)  # Цена в долларах
    price_rub = Column(Float, nullable=True)  # Цена в рублях
    
    # Сроки
    delivery_time = Column(String(100), nullable=True)  # Срок реализации в днях
    
    # Дополнительная информация
    is_available = Column(Boolean, default=True)  # Доступно ли предложение
    is_sample = Column(Boolean, default=False)  # Является ли это предложением по образцу
    
    # Поля для образцов
    sample_price = Column(Float, nullable=True)  # Цена образца
    sample_time = Column(String(100), nullable=True)  # Срок изготовления образца
    sample_price_currency = Column(String(10), nullable=True)  # Валюта цены образца
    
    notes = Column(Text, nullable=True)  # Дополнительные заметки
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    product = relationship("Product", back_populates="price_offers")

class ProductImage(Base):
    """Изображения товаров"""
    __tablename__ = 'product_images'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    sheet_id = Column(Integer, ForeignKey('sheets_metadata.id'), nullable=True)  # ID таблицы
    local_path = Column(String(500), nullable=True)  # Локальный путь к изображению
    image_type = Column(String(50), default='main')  # main, additional
    file_size = Column(Integer, nullable=True)  # Размер файла в байтах
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String(10), nullable=True)  # jpg, png, gif, etc.
    is_downloaded = Column(Boolean, default=True)
    
    # Позиция изображения в Excel файле
    position = Column(JSON, nullable=True)  # JSON с позицией: {row, col, cell, worksheet, found}
    row = Column(Integer, nullable=True)  # Номер строки в Excel
    column = Column(String(10), nullable=True)  # Буква столбца в Excel (A, B, C, etc.)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    product = relationship("Product", back_populates="images")
    sheet = relationship("SheetMetadata", back_populates="images")

class ParsingLog(Base):
    """Логи парсинга"""
    __tablename__ = 'parsing_logs'
    
    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey('sheets_metadata.id'), nullable=False)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    sheet_metadata = relationship("SheetMetadata")

# Вспомогательные функции
def serialize_characteristics(characteristics):
    """Сериализация характеристик в JSON"""
    if isinstance(characteristics, dict):
        return characteristics
    elif isinstance(characteristics, str):
        try:
            import json
            return json.loads(characteristics)
        except:
            return {}
    return {}

def deserialize_characteristics(characteristics):
    """Десериализация характеристик из JSON"""
    if isinstance(characteristics, str):
        try:
            import json
            return json.loads(characteristics)
        except:
            return {}
    return characteristics or {}

def format_price(price, currency='USD'):
    """Форматирование цены"""
    if price is None:
        return 'Не указана'
    
    if currency == 'USD':
        return f"${price:.2f}"
    elif currency == 'RUB':
        return f"{price:.2f} ₽"
    else:
        return f"{price:.2f} {currency}"

def format_quantity(quantity):
    """Форматирование количества"""
    if quantity is None:
        return 'Не указан'
    
    return f"{quantity:,}".replace(',', ' ')

def format_delivery_time(delivery_time):
    """Форматирование срока доставки"""
    if delivery_time is None:
        return 'Не указан'
    
    return f"{delivery_time} дней"
