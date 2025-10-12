"""
Модуль авторизации для CP Parser
"""
import os
import secrets
from functools import wraps
from flask import redirect, url_for, request
from flask import session as flask_session

# Credentials
AUTH_USERNAME = "admin"
AUTH_PASSWORD = os.getenv('AUTH_PASSWORD', 'admin123')  # Читаем из переменной окружения

# Секретный ключ для сессий
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Хранилище активных сессий (в продакшене использовать Redis)
active_sessions = set()

def create_session_token():
    """Создает токен сессии"""
    token = secrets.token_urlsafe(32)
    active_sessions.add(token)
    return token

def check_session(token):
    """Проверяет валидность токена сессии"""
    return token in active_sessions

def login_required(f):
    """Декоратор для защиты роутов"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_token' not in flask_session or not check_session(flask_session.get('session_token')):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function
