"""
Конфигурация проекта для парсинга коммерческих предложений
"""

import os
from pathlib import Path

# Базовые пути
PROJECT_ROOT = Path(__file__).parent
DATABASE_DIR = PROJECT_ROOT / "database"
STORAGE_DIR = PROJECT_ROOT / "storage"
IMAGES_DIR = STORAGE_DIR / "images"
EXPORTS_DIR = STORAGE_DIR / "exports"
WEB_DIR = PROJECT_ROOT / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Создание директорий
for directory in [DATABASE_DIR, STORAGE_DIR, IMAGES_DIR, EXPORTS_DIR, WEB_DIR, TEMPLATES_DIR, STATIC_DIR]:
    directory.mkdir(exist_ok=True)

# База данных
DATABASE_URL = f"sqlite:///{STORAGE_DIR}/commercial_proposals.db"
DATABASE_URL_V4 = f"sqlite:///{STORAGE_DIR}/commercial_proposals_v4.db"

# Google Sheets API
GOOGLE_CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Настройки парсинга
PARSING_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2,
    'batch_size': 100,
    'image_download_timeout': 30,
    'max_image_size_mb': 10
}

# Настройки изображений
IMAGE_CONFIG = {
    'allowed_formats': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'max_width': 1920,
    'max_height': 1080,
    'thumbnail_size': (300, 300),
    'quality': 85
}

# Веб-приложение
WEB_CONFIG = {
    'host': 'localhost',
    'port': 8002,
    'debug': True,
    'secret_key': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
}

# Логирование
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}',
    'rotation': '1 day',
    'retention': '30 days',
    'log_file': PROJECT_ROOT / 'logs' / 'parser.log'
}

# Создание директории для логов
(PROJECT_ROOT / 'logs').mkdir(exist_ok=True)

# Шаблоны для определения структуры таблиц
SHEET_TEMPLATES = {
    'default': {
        'name_column': ['Наименование', 'Название', 'Товар', 'Product'],
        'price_columns': ['Цена', 'Price', 'Стоимость', 'Цена за шт'],
        'description_columns': ['Характеристики', 'Описание', 'Description', 'Спецификация'],
        'image_columns': ['Фото', 'Изображение', 'Image', 'Photo', 'Картинка']
    }
}

# Настройки экспорта
EXPORT_CONFIG = {
    'formats': ['csv', 'xlsx', 'json'],
    'include_images': True,
    'compress_images': True
}


