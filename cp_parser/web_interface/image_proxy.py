#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Прокси для изображений из S3 хранилища с аутентификацией
"""

import boto3
from botocore.exceptions import ClientError
import io
from flask import Response, abort
import logging

# Настройки S3
S3_ACCESS_KEY = 'RECD00AQJIM4300MLJ0W'
S3_SECRET_KEY = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
S3_BUCKET = '73d16f7545b3-promogoods'
S3_REGION = 'ru1'
S3_ENDPOINT = 'https://s3.ru1.storage.beget.cloud'

# Создаем S3 клиент
s3_client = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT,
    config=boto3.session.Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
)

def get_image_from_s3(filename):
    """Получает изображение из S3 хранилища"""
    try:
        # Формируем ключ файла
        s3_key = f"images/{filename}"
        
        # Получаем объект из S3
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        
        # Читаем содержимое
        image_data = response['Body'].read()
        
        # Получаем метаданные
        content_type = response.get('ContentType', 'image/jpeg')
        content_length = response.get('ContentLength', len(image_data))
        
        return image_data, content_type, content_length
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            logging.warning(f"Файл не найден в S3: {filename}")
            return None, None, None
        else:
            logging.error(f"Ошибка S3 для файла {filename}: {e}")
            return None, None, None
    except Exception as e:
        logging.error(f"Критическая ошибка для файла {filename}: {e}")
        return None, None, None

def serve_image_proxy(filename):
    """Отдает изображение через прокси с аутентификацией"""
    # Получаем изображение из S3
    image_data, content_type, content_length = get_image_from_s3(filename)
    
    if image_data is None:
        abort(404)
    
    # Создаем ответ
    response = Response(
        image_data,
        mimetype=content_type,
        headers={
            'Content-Length': str(content_length),
            'Cache-Control': 'public, max-age=3600',  # Кэшируем на 1 час
            'ETag': f'"{filename}"'
        }
    )
    
    return response

def generate_presigned_url(filename, expiration=3600):
    """Генерирует подписанный URL для изображения"""
    try:
        s3_key = f"images/{filename}"
        
        # Генерируем подписанный URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=expiration
        )
        
        return presigned_url
        
    except ClientError as e:
        logging.error(f"Ошибка генерации подписанного URL для {filename}: {e}")
        return None
    except Exception as e:
        logging.error(f"Критическая ошибка генерации URL для {filename}: {e}")
        return None

def test_s3_connection():
    """Тестирует соединение с S3"""
    try:
        # Пробуем получить список объектов
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='images/',
            MaxKeys=1
        )
        
        if 'Contents' in response:
            print("✅ S3 соединение работает!")
            return True
        else:
            print("⚠️  S3 соединение работает, но папка images пуста")
            return True
            
    except ClientError as e:
        print(f"❌ Ошибка S3 соединения: {e}")
        return False
    except Exception as e:
        print(f"❌ Критическая ошибка S3: {e}")
        return False

if __name__ == "__main__":
    # Тестируем соединение
    print("🧪 Тестирую S3 соединение...")
    test_s3_connection()
