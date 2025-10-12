#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Конфигурация для веб-интерфейса парсера коммерческих предложений
"""

import os
from pathlib import Path

# Базовые настройки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# Настройки пагинации
PRODUCTS_PER_PAGE = int(os.getenv('PRODUCTS_PER_PAGE', 24))
PROJECTS_PER_PAGE = int(os.getenv('PROJECTS_PER_PAGE', 20))

# Настройки облачного хранилища
CLOUD_STORAGE_ENABLED = os.getenv('CLOUD_STORAGE_ENABLED', 'True').lower() == 'true'
S3_BASE_URL = os.getenv('S3_BASE_URL', 'https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods')
CLOUD_IMAGES_PREFIX = os.getenv('CLOUD_IMAGES_PREFIX', 'images/')

# Локальные пути
PROJECT_ROOT = Path(__file__).parent.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
IMAGES_DIR = STORAGE_DIR / "images"

# Настройки базы данных
# Railway предоставляет DATABASE_URL или DATABASE_PUBLIC_URL
DATABASE_URL = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL', 'postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway')
SQLITE_DATABASE_URL = f'sqlite:///{PROJECT_ROOT}/database/cp_parser.db'

# Настройки безопасности
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Настройки кэширования
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))

def get_image_url(filename):
    """Получает URL изображения (облачный или локальный)"""
    if CLOUD_STORAGE_ENABLED:
        return f"{S3_BASE_URL}/{CLOUD_IMAGES_PREFIX}{filename}"
    else:
        return f"/images/{filename}"

def is_cloud_storage_enabled():
    """Проверяет, включено ли облачное хранилище"""
    return CLOUD_STORAGE_ENABLED

def get_cloud_base_url():
    """Получает базовый URL облачного хранилища"""
    return S3_BASE_URL

def get_cloud_images_prefix():
    """Получает префикс для изображений в облачном хранилище"""
    return CLOUD_IMAGES_PREFIX

