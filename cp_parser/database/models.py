"""
Модели базы данных для умного парсера коммерческих предложений v2.0
Структура: 4 основные таблицы для хранения результатов парсинга
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Project(Base):
    """
    ТАБЛИЦА 1: ПРОЕКТЫ (Коммерческие предложения)
    Хранит метаданные о загруженных файлах и проектах
    """
    __tablename__ = 'projects'
    
    # Первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ID таблицы для привязки
    table_id = Column(String(100), nullable=True, comment="ID таблицы для привязки данных")
    
    # Основная информация о проекте
    project_name = Column(String(500), nullable=False, comment="Название проекта")
    file_name = Column(String(500), nullable=False, comment="Имя исходного файла")
    file_path = Column(String(1000), nullable=True, comment="Путь к файлу")
    file_size_mb = Column(Float, nullable=True, comment="Размер файла в МБ")
    
    # Ссылка на Google Sheets
    google_sheets_url = Column(String(1000), nullable=True, comment="Ссылка на Google Sheets")
    
    # Бизнес информация
    client_name = Column(String(300), nullable=True, comment="Название клиента/контрагента")
    manager_name = Column(String(200), nullable=True, comment="Менеджер проекта")
    region = Column(String(100), nullable=True, comment="Регион (РФ/Международная/ОАЭ)")
    offer_creation_date = Column(String(50), nullable=True, comment="Дата создания КП из мастер-таблицы")
    
    # Ценовые рамки проекта (общие)
    min_budget_usd = Column(Float, nullable=True, comment="Минимальный бюджет в USD")
    max_budget_usd = Column(Float, nullable=True, comment="Максимальный бюджет в USD")
    min_budget_rub = Column(Float, nullable=True, comment="Минимальный бюджет в RUB")
    max_budget_rub = Column(Float, nullable=True, comment="Максимальный бюджет в RUB")
    
    # Тиражи
    min_quantity = Column(Integer, nullable=True, comment="Минимальный тираж")
    max_quantity = Column(Integer, nullable=True, comment="Максимальный тираж")
    
    # Метаданные парсинга
    parsing_status = Column(String(50), default='pending', comment="Статус парсинга: pending/processing/completed/error")
    structure_type = Column(String(100), nullable=True, comment="Тип структуры таблицы")
    parsing_complexity = Column(String(50), nullable=True, comment="Сложность парсинга: simple/medium/complex")
    total_products_found = Column(Integer, default=0, comment="Количество найденных товаров")
    total_images_found = Column(Integer, default=0, comment="Количество найденных изображений")
    parsing_errors = Column(Text, nullable=True, comment="Ошибки парсинга (JSON)")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    parsed_at = Column(DateTime, nullable=True, comment="Время завершения парсинга")
    
    # Связи
    products = relationship("Product", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', status='{self.parsing_status}')>"


class Product(Base):
    """
    ТАБЛИЦА 2: ТОВАРЫ
    Хранит информацию о товарах из коммерческих предложений
    """
    __tablename__ = 'products'
    
    # Первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Связь с проектом
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # ID таблицы для привязки
    table_id = Column(String(100), nullable=True, comment="ID таблицы для привязки данных")
    
    # Основная информация о товаре
    name = Column(Text, nullable=False, comment="Название товара")
    description = Column(Text, nullable=True, comment="Описание/характеристики товара")
    article_number = Column(String(200), nullable=True, comment="Артикул товара")
    custom_field = Column(Text, nullable=True, comment="Кастом - дополнительное текстовое поле")
    
    # Позиция в исходной таблице
    sheet_name = Column(String(200), nullable=True, comment="Название листа Excel")
    row_number = Column(Integer, nullable=True, comment="Номер строки в исходной таблице")
    row_number_end = Column(Integer, nullable=True, comment="Конечный номер строки (для многострочных товаров)")
    
    # Поля по образцу
    sample_price = Column(Float, nullable=True, comment="Цена образца")
    sample_delivery_time = Column(Integer, nullable=True, comment="Срок образца в днях")
    
    # Характеристики товара (JSON для гибкости)
    specifications = Column(JSON, nullable=True, comment="Технические характеристики (JSON)")
    custom_fields = Column(JSON, nullable=True, comment="Дополнительные поля (JSON)")
    
    # Метаданные парсинга
    data_quality = Column(String(50), default='good', comment="Качество данных: good/partial/poor")
    parsing_notes = Column(Text, nullable=True, comment="Заметки парсера")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    project = relationship("Project", back_populates="products")
    price_offers = relationship("PriceOffer", back_populates="product", cascade="all, delete-orphan")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', project_id={self.project_id})>"


class PriceOffer(Base):
    """
    ТАБЛИЦА 3: ЦЕНОВЫЕ ПРЕДЛОЖЕНИЯ
    Хранит различные ценовые предложения для товаров (тиражи, цены, сроки)
    """
    __tablename__ = 'price_offers'
    
    # Первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Связь с товаром
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # ID таблицы для привязки
    table_id = Column(String(100), nullable=True, comment="ID таблицы для привязки данных")
    
    # Тираж
    quantity = Column(Integer, nullable=False, comment="Тираж")
    quantity_unit = Column(String(50), default='шт', comment="Единица измерения")
    
    # Цены за единицу товара
    price_usd = Column(Float, nullable=True, comment="Цена за единицу в USD")
    price_rub = Column(Float, nullable=True, comment="Цена за единицу в RUB")
    
    # Маршрут и сроки доставки
    route = Column(String(100), nullable=True, comment="Маршрут доставки (МСК, АВИА и т.д.)")
    delivery_time_days = Column(Integer, nullable=True, comment="Срок поставки в днях")
    delivery_conditions = Column(Text, nullable=True, comment="Условия поставки")
    
    # Дополнительная информация
    discount_percent = Column(Float, nullable=True, comment="Размер скидки в %")
    special_conditions = Column(Text, nullable=True, comment="Особые условия")
    
    # Позиция в таблице
    row_position = Column(String(10), nullable=True, comment="Позиция строки в таблице")
    
    # Метаданные
    is_recommended = Column(Boolean, default=False, comment="Рекомендуемое предложение")
    data_source = Column(String(100), nullable=True, comment="Источник данных (parsed/calculated)")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    product = relationship("Product", back_populates="price_offers")
    
    def __repr__(self):
        return f"<PriceOffer(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, price_usd={self.price_usd})>"


class ProductImage(Base):
    """
    ТАБЛИЦА 4: ИЗОБРАЖЕНИЯ ТОВАРОВ
    Хранит информацию об изображениях, привязанных к товарам
    """
    __tablename__ = 'product_images'
    
    # Первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Связь с товаром
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)  # Сделали необязательным для логотипов
    
    # ID таблицы для привязки
    table_id = Column(String(100), nullable=True, comment="ID таблицы для привязки данных")
    
    # Информация об изображении
    image_url = Column(String(1000), nullable=True, comment="URL изображения (если онлайн)")
    local_path = Column(String(1000), nullable=True, comment="Локальный путь к файлу")
    image_filename = Column(String(500), nullable=True, comment="Имя файла изображения")
    
    # Позиция в исходной таблице
    sheet_name = Column(String(200), nullable=True, comment="Название листа Excel")
    cell_position = Column(String(10), nullable=True, comment="Позиция ячейки (A1, B2...)")
    row_number = Column(Integer, nullable=True, comment="Номер строки")
    column_number = Column(Integer, nullable=True, comment="Номер столбца")
    
    # Технические характеристики изображения
    width_px = Column(Integer, nullable=True, comment="Ширина в пикселях")
    height_px = Column(Integer, nullable=True, comment="Высота в пикселях")
    file_size_kb = Column(Float, nullable=True, comment="Размер файла в КБ")
    format = Column(String(10), nullable=True, comment="Формат изображения (jpg, png...)")
    
    # Основные свойства изображения
    is_main_image = Column(Boolean, default=False, comment="Главное изображение товара")
    display_order = Column(Integer, default=1, comment="Порядок отображения")
    
    # Метаданные
    extraction_method = Column(String(100), nullable=True, comment="Метод извлечения изображения")
    quality_score = Column(Float, nullable=True, comment="Оценка качества изображения (0-1)")
    processing_status = Column(String(50), default='pending', comment="Статус обработки")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связи
    product = relationship("Product", back_populates="images")
    
    def __repr__(self):
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, filename='{self.image_filename}')>"


# Индексы для оптимизации запросов
from sqlalchemy import Index

# Индексы для таблицы проектов
Index('idx_projects_status', Project.parsing_status)
Index('idx_projects_client', Project.client_name)
Index('idx_projects_created', Project.created_at)
Index('idx_projects_table_id', Project.table_id)

# Индексы для таблицы товаров
Index('idx_products_project', Product.project_id)
Index('idx_products_name', Product.name)
Index('idx_products_table_id', Product.table_id)
Index('idx_products_row', Product.row_number)

# Индексы для ценовых предложений
Index('idx_price_offers_product', PriceOffer.product_id)
Index('idx_price_offers_quantity', PriceOffer.quantity)
Index('idx_price_offers_price_usd', PriceOffer.price_usd)
Index('idx_price_offers_table_id', PriceOffer.table_id)

# Индексы для изображений
Index('idx_product_images_product', ProductImage.product_id)
Index('idx_product_images_main', ProductImage.is_main_image)
Index('idx_product_images_table_id', ProductImage.table_id)
