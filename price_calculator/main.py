#!/usr/bin/env python3
"""
Price Calculator Web Application
FastAPI + Vue.js интерфейс для расчета цен товаров
"""

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import os
import secrets
from contextlib import asynccontextmanager

import importlib
import sys

# Принудительная перезагрузка модуля если он уже был импортирован
if 'price_calculator' in sys.modules:
    importlib.reload(sys.modules['price_calculator'])
    
from price_calculator import PriceCalculator
from database import init_database, save_calculation_to_db, get_calculation_history, restore_from_backup, update_calculation
from customs_data import customs_loader

# DTO models для type safety и валидации
from models.dto import (
    ProductInputDTO,
    CalculationResultDTO,
    CategoriesResponseDTO,
    CategoryDTO
)

# Загрузка настроек через ConfigLoader
try:
    import sys
    from pathlib import Path
    config_dir = Path(__file__).parent / "config"
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    
    from config_loader import get_app_config
    app_config = get_app_config()
    
    # Настройки аутентификации из конфигурации
    AUTH_USERNAME = app_config.auth.username
    AUTH_PASSWORD = app_config.auth.password  
    SESSION_SECRET = app_config.auth.session_secret
    
    print("OK Настройки загружены через ConfigLoader")
    
except ImportError:
    # Fallback к старым настройкам
    print("WARNING ConfigLoader недоступен, используем статичные настройки")
    AUTH_USERNAME = "admin"
    AUTH_PASSWORD = "admin123"
    SESSION_SECRET = secrets.token_urlsafe(32)

# Хранилище активных сессий (в продакшене лучше использовать Redis)
active_sessions = set()

def create_session_token() -> str:
    """Создание токена сессии"""
    token = secrets.token_urlsafe(32)
    active_sessions.add(token)
    return token

def verify_session(session_token: str = None) -> bool:
    """Проверка валидности сессии"""
    return session_token and session_token in active_sessions

def require_auth(request: Request):
    """Dependency для проверки авторизации"""
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        raise HTTPException(status_code=401, detail="Authentication required")
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске (НЕ КРИТИЧНО если упадет)
    try:
        # ✅ Инициализация БД - добавляет необходимые колонки если их нет
        from init_db import init_database as init_db_schema
        init_db_schema()
        
        # Стандартная инициализация таблиц
        init_database()
        restore_from_backup()
        print("OK База данных готова к работе!")
    except Exception as e:
        print(f"WARNING База данных недоступна: {e}")
        print("INFO Калькулятор будет работать без истории")
    
    print("OK Сервер запущен!")
    yield
    # Cleanup здесь если нужно

app = FastAPI(
    title="Price Calculator",
    description="Сервис для быстрого расчета цен товаров",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ФАЗА 2: Настройка статических файлов и шаблонов (Railway-совместимо)
from pathlib import Path

# Определяем базовую директорию проекта
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Создаем директории если их нет (для Railway)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# Vite build assets
DIST_DIR = Path(__file__).parent / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="vite-assets")
    # Vite assets для /vite/ маршрута
    app.mount("/vite/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="vite-route-assets")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Инициализация калькулятора  
calculator = None

def get_calculator():
    global calculator
    if calculator is None:
        try:
            print("🔄 Инициализируем калькулятор...")
            calculator = PriceCalculator()
            print("✅ Калькулятор инициализирован успешно")
        except Exception as e:
            print(f"❌ Ошибка инициализации калькулятора: {e}")
            import traceback
            traceback.print_exc()
            return None
    return calculator

# Pydantic модели
class RouteLogisticsParams(BaseModel):
    """Параметры логистики для конкретного маршрута"""
    custom_rate: Optional[float] = None  # Кастомная ставка доставки (USD/kg)
    duty_type: Optional[str] = None  # Тип пошлины: 'percent', 'combined', 'specific'
    duty_rate: Optional[float] = None  # Процентная пошлина (%)
    specific_rate: Optional[float] = None  # Специфическая пошлина (EUR/kg или USD/kg)
    vat_rate: Optional[float] = None  # НДС (%)
    
    class Config:
        extra = "forbid"  # Запретить дополнительные поля

class CalculationRequest(BaseModel):
    """Модель запроса для расчета цены товара"""
    product_name: str
    link_or_wechat: Optional[str] = ""  # Ссылка на товар или WeChat поставщика
    price_yuan: float
    weight_kg: Optional[float] = None  # Опционально, вычисляется из packing_box_weight если is_precise_calculation=True
    quantity: int
    product_url: Optional[str] = ""  # Legacy поле для обратной совместимости
    custom_rate: Optional[float] = None
    delivery_type: str = "rail"  # rail или air
    markup: float = 1.7
    # Флаг для точных расчетов с пакингом
    is_precise_calculation: bool = False
    # Поля пакинга (используются только при is_precise_calculation=True)
    packing_units_per_box: Optional[int] = None
    packing_box_weight: Optional[float] = None
    packing_box_length: Optional[float] = None
    packing_box_width: Optional[float] = None
    packing_box_height: Optional[float] = None
    # Кастомные параметры логистики для конкретных маршрутов (только для этого расчета)
    # Ключи: 'highway_rail', 'highway_air', 'contract', 'prologix', 'sea_container'
    custom_logistics: Optional[Dict[str, Dict[str, Any]]] = None
    # Принудительная категория (переопределяет автоопределение)
    forced_category: Optional[str] = None

class CalculationResponse(BaseModel):
    """Модель ответа с результатами расчета цены"""
    id: Optional[int] = None
    product_name: str
    category: str
    quantity: int
    unit_price_yuan: float
    total_price: Dict[str, float]
    logistics: Dict[str, Any]
    additional_costs: dict
    cost_price: Dict[str, Any]
    sale_price: Dict[str, Any] 
    markup: float
    profit: Dict[str, Any]
    weight_kg: float
    estimated_weight: float
    product_url: str
    created_at: Optional[str] = None
    # Тип расчета для правильной навигации
    calculation_type: str = "quick"  # "quick" или "precise"
    # Поля пакинга (заполняются только для точных расчетов)
    packing_units_per_box: Optional[int] = None
    packing_box_weight: Optional[float] = None
    packing_box_length: Optional[float] = None
    packing_box_width: Optional[float] = None
    packing_box_height: Optional[float] = None
    # Данные по пошлинам
    customs_info: Optional[Dict[str, Any]] = None
    customs_calculations: Optional[Dict[str, float]] = None
    density_warning: Optional[Dict[str, Any]] = None
    # НОВОЕ ПОЛЕ: Данные о плотности и надбавке
    density_info: Optional[Dict[str, Any]] = None
    # НОВЫЕ ПОЛЯ ДЛЯ КОНТРАКТА
    contract_cost: Optional[Dict[str, Any]] = None
    cost_difference: Optional[Dict[str, Any]] = None
    # НОВОЕ ПОЛЕ: Prologix расчет
    prologix_cost: Optional[Dict[str, Any]] = None
    # 🚀 КРИТИЧНО: Все маршруты логистики в едином формате
    routes: Optional[Dict[str, Any]] = None

class CategoryInfo(BaseModel):
    category: str
    material: str
    density: Optional[float] = None
    rates: Dict[str, float]
    tnved_code: Optional[str] = ""
    recommendations: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "ignore"  # Игнорируем дополнительные поля

# База данных инициализируется через database.py

def save_calculation(calculation: dict, request: CalculationRequest = None) -> int:
    """Сохранение расчета в базу данных"""
    try:
        print(f"🔧 save_calculation: Начало обработки для '{calculation.get('product_name')}'")
        
        # Адаптируем данные под универсальный модуль
        db_data = {
            'product_name': calculation['product_name'],
            'category': calculation['category'],
            'price_yuan': calculation['unit_price_yuan'],
            'weight_kg': calculation['weight_kg'],
            'quantity': calculation['quantity'],
            'markup': calculation['markup'],
            'custom_rate': calculation['logistics'].get('rate_usd'),
            'product_url': calculation.get('product_url', ''),
            'cost_price_total_rub': calculation['cost_price']['total']['rub'],
            'cost_price_total_usd': calculation['cost_price']['total']['usd'],
            'sale_price_total_rub': calculation['sale_price']['total']['rub'],
            'sale_price_total_usd': calculation['sale_price']['total']['usd'],
            'profit_total_rub': calculation['profit']['total']['rub'],
            'profit_total_usd': calculation['profit']['total']['usd'],
            # Добавляем тип расчета
            'calculation_type': calculation.get('calculation_type', 'quick')
        }
        
        print(f"🔧 Базовые данные подготовлены: {len(db_data)} полей")
        
        # Добавляем данные пакинга если они есть
        if request and request.packing_units_per_box:
            db_data.update({
                'packing_units_per_box': request.packing_units_per_box,
                'packing_box_weight': request.packing_box_weight,
                'packing_box_length': request.packing_box_length,
                'packing_box_width': request.packing_box_width,
                'packing_box_height': request.packing_box_height,
                # Вычисляемые поля
                'packing_total_boxes': (calculation['quantity'] + request.packing_units_per_box - 1) // request.packing_units_per_box,  # ceiling division
                'packing_total_volume': (request.packing_box_length * request.packing_box_width * request.packing_box_height) * ((calculation['quantity'] + request.packing_units_per_box - 1) // request.packing_units_per_box),
                'packing_total_weight': request.packing_box_weight * ((calculation['quantity'] + request.packing_units_per_box - 1) // request.packing_units_per_box)
            })
        
        # Добавляем данные о пошлинах если они есть
        customs_info = calculation.get('customs_info', {})
        customs_calculations = calculation.get('customs_calculations', {})
        density_warning = calculation.get('density_warning', {})
        
        if customs_info:
            db_data.update({
                'tnved_code': customs_info.get('tnved_code'),
                'duty_rate': customs_info.get('duty_rate'),
                'vat_rate': customs_info.get('vat_rate'),
                'certificates': ', '.join(customs_info.get('certificates', [])) if customs_info.get('certificates') else None,
                'customs_notes': customs_info.get('required_documents')
            })
        
        if customs_calculations:
            db_data.update({
                'duty_amount_usd': customs_calculations.get('duty_amount_usd'),
                'vat_amount_usd': customs_calculations.get('vat_amount_usd'),
                'total_customs_cost_usd': customs_calculations.get('total_customs_cost_usd')
            })
        
        if density_warning:
            db_data.update({
                'density_warning_message': density_warning.get('message'),
                'calculated_density': density_warning.get('calculated_density'),
                'category_density': density_warning.get('category_density')
            })
        
        # Добавляем кастомные параметры логистики и принудительную категорию
        if request:
            if request.custom_logistics:
                db_data['custom_logistics'] = request.custom_logistics
            if request.forced_category:
                db_data['forced_category'] = request.forced_category
        
        print(f"🔧 Вызов save_calculation_to_db с {len(db_data)} полями")
        result_id = save_calculation_to_db(db_data)
        
        if result_id:
            print(f"✅ save_calculation_to_db вернул ID: {result_id}")
        else:
            print(f"⚠️ save_calculation_to_db вернул None или 0")
        
        return result_id
    except Exception as e:
        print(f"❌ Ошибка в save_calculation: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_history_calculations() -> List[dict]:
    """Получение истории расчетов через database.py"""
    try:
        return get_calculation_history()
    except Exception as e:
        print(f"Ошибка получения истории: {e}")
        return []

# Страница авторизации
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Страница авторизации"""
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Авторизация - Price Calculator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        body {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .input-field {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.75rem;
            transition: all 0.2s ease;
        }
        .input-field:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .btn-primary {
            background: #000;
            color: white;
            transition: all 0.2s ease;
        }
        .btn-primary:hover {
            background: #1f2937;
        }
        .card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            transition: all 0.2s ease;
        }
        .card:hover {
            border-color: #d1d5db;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .loading-spinner {
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div id="app">
        <header class="bg-white border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center">
                        <h1 class="text-xl font-semibold text-gray-900">Price Calculator</h1>
                    </div>
                    <div class="text-sm text-gray-500">Защищенная система расчета цен</div>
                </div>
            </div>
        </header>

        <main class="flex items-center justify-center min-h-screen -mt-16 px-4">
            <div class="card w-full max-w-md p-8">
                <div class="text-center mb-8">
                    <div class="mb-4">
                        <div class="text-4xl text-gray-900 mb-2">🧮</div>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-900 mb-2">Вход в систему</h2>
                    <p class="text-gray-500">Введите ваши учетные данные</p>
                </div>

            <form @submit.prevent="handleLogin" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Логин</label>
                    <input 
                        v-model="credentials.username" 
                        type="text" 
                        required
                        class="input-field w-full" 
                        placeholder="Введите логин">
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
                    <input 
                        v-model="credentials.password" 
                        type="password" 
                        required
                        class="input-field w-full" 
                        placeholder="Введите пароль">
                </div>

                <div v-if="errorMessage" class="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p class="text-red-700 text-sm">WARNING {{ errorMessage }}</p>
                </div>

                <button 
                    type="submit" 
                    :disabled="isLoading"
                    :class="['btn-primary px-8 py-3 rounded-lg font-medium w-full', 
                            isLoading ? 'opacity-50 cursor-not-allowed' : '']">
                    <span v-if="isLoading" class="loading-spinner inline-block w-4 h-4 mr-2">⏳</span>
                    {{ isLoading ? 'Вход...' : 'Войти' }}
                </button>
            </form>

                <div class="mt-8 pt-6 border-t border-gray-200 text-center">
                    <p class="text-xs text-gray-400">
                        © 2025 Price Calculator. Все права защищены.
                    </p>
                </div>
            </div>
        </main>
    </div>

    <script>
        const { createApp } = Vue;
        
        createApp({
            data() {
                return {
                    credentials: {
                        username: '',
                        password: ''
                    },
                    isLoading: false,
                    errorMessage: ''
                }
            },
            methods: {
                async handleLogin() {
                    if (!this.credentials.username || !this.credentials.password) {
                        this.errorMessage = 'Заполните все поля';
                        return;
                    }

                    this.isLoading = true;
                    this.errorMessage = '';

                    try {
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(this.credentials)
                        });

                        const data = await response.json();

                        if (data.success) {
                            window.location.href = '/';
                        } else {
                            this.errorMessage = data.error || 'Ошибка авторизации';
                        }

                    } catch (error) {
                        console.error('Login error:', error);
                        this.errorMessage = 'Произошла ошибка. Попробуйте снова.';
                    } finally {
                        this.isLoading = false;
                    }
                }
            },
            mounted() {
                this.$nextTick(() => {
                    const usernameInput = document.querySelector('input[type="text"]');
                    if (usernameInput) {
                        usernameInput.focus();
                    }
                });
            }
        }).mount('#app');
    </script>
</body>
</html>
    """

@app.post("/api/login")
async def login(request: Request, response: Response):
    """API endpoint для авторизации"""
    try:
        data = await request.json()
        username = data.get("username", "")
        password = data.get("password", "")
        
        if username == AUTH_USERNAME and password == AUTH_PASSWORD:
            # Создаем токен сессии
            session_token = create_session_token()
            
            # Устанавливаем cookie с токеном
            response.set_cookie(
                key="session_token",
                value=session_token,
                max_age=86400 * 7,  # 7 дней
                httponly=True,
                secure=False,  # В продакшене должно быть True для HTTPS
                samesite="lax"
            )
            
            return {"success": True, "message": "Авторизация успешна"}
        else:
            return {"success": False, "error": "Неверный логин или пароль"}
            
    except Exception as e:
        print(f"Login error: {e}")
        return {"success": False, "error": "Ошибка обработки запроса"}

@app.post("/api/logout")
async def logout(request: Request, response: Response):
    """API endpoint для выхода"""
    session_token = request.cookies.get("session_token")
    if session_token and session_token in active_sessions:
        active_sessions.remove(session_token)
    
    response.delete_cookie("session_token")
    return {"success": True, "message": "Выход выполнен"}

# API endpoints
@app.get("/")
async def root(request: Request):
    """🚀 Главная страница - V2 (новая версия интерфейса)"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('index_v2.html')

@app.get("/v1")
async def v1_page(request: Request):
    """📦 V1 - Старая версия интерфейса (с авторизацией)"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    # Возвращаем старую версию
    return FileResponse('index.html')

@app.get("/refactored")
async def refactored_version(request: Request):
    """🚀 Новая рефакторенная версия с модульной архитектурой"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    # Возвращаем новую версию
    return FileResponse('index-refactored.html')

@app.get("/vite")
async def vite_version(request: Request):
    """Vite оптимизированная версия"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    # Возвращаем Vite build версию
    return FileResponse('frontend/dist/src/index.html')

@app.get("/monolith")
async def monolith_version(request: Request):
    """Монолитная версия (для сравнения и отката)"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('index_monolith_backup.html')

@app.get("/test-components")
async def test_components(request: Request):
    """Тестовая страница для диагностики компонентов"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('test_components.html')

@app.get("/test-simple")
async def test_simple(request: Request):
    """Тестовая страница с упрощенными компонентами"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('test_simple.html')

@app.get("/test-fixed")
async def test_fixed(request: Request):
    """Тестовая страница с исправленными компонентами"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('test_fixed.html')

@app.get("/test-minimal")
async def test_minimal(request: Request):
    """Минимальный тест Vue.js"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('test_minimal.html')

@app.post("/api/reload-calculator")
async def reload_calculator():
    """Перезагружает калькулятор с новыми данными из БД"""
    try:
        global calculator
        
        # Сбрасываем кэшированный калькулятор
        calculator = None
        print("🔄 Сброс кэшированного калькулятора...")
        
        # Принудительно создаем новый экземпляр
        calc = get_calculator()
        
        if calc and hasattr(calc, 'categories') and calc.categories:
            categories_count = len(calc.categories)
            
            # Проверяем наличие данных по пошлинам в категориях
            categories_with_customs = 0
            sample_category = None
            
            for category in calc.categories:
                if isinstance(category, dict) and 'duty_rate' in category and 'vat_rate' in category:
                    categories_with_customs += 1
                    if not sample_category:
                        sample_category = {
                            'name': category.get('category', 'Unknown'),
                            'duty_rate': category.get('duty_rate'),
                            'vat_rate': category.get('vat_rate'),
                            'tnved_code': category.get('tnved_code')
                        }
            
            return {
                "status": "success",
                "message": "Калькулятор успешно перезагружен",
                "categories_total": categories_count,
                "categories_with_customs": categories_with_customs,
                "sample_category": sample_category,
                "customs_loader_available": hasattr(calc, 'customs_loader') and calc.customs_loader is not None
            }
        else:
            return {
                "status": "warning", 
                "message": "Калькулятор перезагружен, но категории не найдены",
                "categories_total": 0,
                "categories_with_customs": 0
            }
            
    except Exception as e:
        print(f"❌ Ошибка перезагрузки калькулятора: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка перезагрузки калькулятора: {str(e)}")

@app.post("/api/fix-missing-customs")
async def fix_missing_customs():
    """Исправляет отсутствующие данные по пошлинам для всех категорий с ТН ВЭД"""
    try:
        from database import get_database_connection
        import json
        
        # Универсальные пошлины по типам ТН ВЭД
        TNVED_CUSTOMS_MAP = {
            # Электроника и аккумуляторы
            "85": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Текстиль и одежда  
            "61": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "62": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "63": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "65": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Сумки и кожгалантерея
            "42": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Керамика и посуда
            "69": {"duty_rate": "11.5%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Пластмассы
            "39": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
            
            # Игрушки
            "95": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Металлы
            "71": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            "73": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "83": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            
            # Книги и печатная продукция
            "48": {"duty_rate": "0%", "vat_rate": "10%", "certificates": []},
            
            # Зонты
            "66": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            
            # Часы
            "91": {"duty_rate": "6%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # По умолчанию
            "default": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]}
        }
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Получаем все категории без пошлин, но с ТН ВЭД
        cursor.execute("SELECT category, data FROM categories")
        all_categories = cursor.fetchall()
        
        updated_count = 0
        results = []
        
        for row in all_categories:
            try:
                if db_type == 'postgres':
                    category_name = row['category'] if isinstance(row, dict) else row[0]
                    category_data = row['data'] if isinstance(row, dict) else row[1]
                else:
                    category_name = row['category'] if hasattr(row, 'keys') else row[0]
                    category_data = row['data'] if hasattr(row, 'keys') else row[1]
                
                # Парсим JSON данные
                if isinstance(category_data, str):
                    category_json = json.loads(category_data)
                else:
                    category_json = category_data
                
                tnved_code = category_json.get('tnved_code', '')
                has_duty_rate = bool(category_json.get('duty_rate'))
                has_vat_rate = bool(category_json.get('vat_rate'))
                
                # Обрабатываем только категории с ТН ВЭД, но без пошлин
                if tnved_code and not (has_duty_rate and has_vat_rate):
                    # Определяем пошлины по первым 2 цифрам ТН ВЭД
                    tnved_prefix = tnved_code[:2] if len(tnved_code) >= 2 else ""
                    
                    customs_info = TNVED_CUSTOMS_MAP.get(tnved_prefix, TNVED_CUSTOMS_MAP["default"])
                    
                    # Обновляем данные
                    category_json['duty_rate'] = customs_info['duty_rate']
                    category_json['vat_rate'] = customs_info['vat_rate']
                    category_json['certificates'] = customs_info['certificates']
                    
                    # Сохраняем в БД
                    updated_data = json.dumps(category_json, ensure_ascii=False)
                    
                    if db_type == 'postgres':
                        cursor.execute(
                            "UPDATE categories SET data = %s WHERE category = %s",
                            (updated_data, category_name)
                        )
                    else:
                        cursor.execute(
                            "UPDATE categories SET data = ? WHERE category = ?",
                            (updated_data, category_name)
                        )
                    
                    updated_count += 1
                    results.append(f"✅ {category_name} (ТН ВЭД: {tnved_code[:2]}**) -> {customs_info['duty_rate']}/{customs_info['vat_rate']}")
                    
            except Exception as e:
                results.append(f"❌ Ошибка с {category_name}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        return {
            "status": "success",
            "message": "Пошлины добавлены для всех категорий с ТН ВЭД",
            "categories_updated": updated_count,
            "details": results[:30]  # Первые 30 результатов
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Ошибка исправления пошлин: {str(e)}"}

@app.post("/api/load-customs-data")
async def load_customs_data_endpoint():
    """Загрузка данных по пошлинам для всех категорий"""
    try:
        from database import get_database_connection
        import json
        
        # Данные по пошлинам для всех категорий
        CUSTOMS_DATA = {
            # Основные категории с пошлинами
            "повербанки": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "кружки": {"duty_rate": "11.5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "термосы": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "термобутылки": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "термокружки": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "термостаканы": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "кофферы": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "ежедневники": {"duty_rate": "0%", "vat_rate": "10%", "certificates": []},
            "блокноты": {"duty_rate": "0%", "vat_rate": "10%", "certificates": []},
            "картхолдер": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "ланьярд": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "ретрактор": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "пакеты": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
            "флешки": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "ручки": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            "футболки": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "сумки": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "зонты": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            "часы": {"duty_rate": "6%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Дополнительные категории
            "бутылка": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "коффер": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "термос": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]},
            "ручка": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            "лампа": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "игрушка": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "игрушки": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "кабель": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "брелок": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            "чехол": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "рюкзак": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "аккумулятор": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "косметичка": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "колонка": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "флешка": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "футболка": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "плед": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "увлажнитель": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "зонт": {"duty_rate": "6.5%", "vat_rate": "20%", "certificates": []},
            "подушка": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "коробка": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
            "органайзер": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "пенал": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "бейдж": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "наушники": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "блокнот": {"duty_rate": "0%", "vat_rate": "10%", "certificates": []},
            "массажер": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "посуда": {"duty_rate": "11.5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "проектор": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "кепка": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "шарф": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "перчатки": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "дождевик": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "фонарь": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "гирлянда": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "свеча": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
            "магнит": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
            "толстовка": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "худи": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            "конструктор": {"duty_rate": "5%", "vat_rate": "20%", "certificates": ["EAC"]},
            "таблетница": {"duty_rate": "9.6%", "vat_rate": "20%", "certificates": ["EAC"]},
            "стикеры": {"duty_rate": "5%", "vat_rate": "20%", "certificates": []},
            "мышь": {"duty_rate": "0%", "vat_rate": "20%", "certificates": ["EAC"]},
            "носки": {"duty_rate": "8.8%", "vat_rate": "20%", "certificates": ["EAC"]},
            
            # Общая категория по умолчанию
            "общая": {"duty_rate": "15%", "vat_rate": "20%", "certificates": ["EAC"]}
        }
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        print(f"🚛 Загружаем данные по пошлинам в {db_type}...")
        
        # Получаем все существующие категории
        cursor.execute("SELECT category, data FROM categories")
        existing_categories = cursor.fetchall()
        
        print(f"📦 Найдено категорий в БД: {len(existing_categories)}")
        
        updated_count = 0
        results = []
        
        for row in existing_categories:
            try:
                if db_type == 'postgres':
                    category_name = row['category'] if isinstance(row, dict) else row[0]
                    category_data = row['data'] if isinstance(row, dict) else row[1]
                else:
                    category_name = row['category'] if hasattr(row, 'keys') else row[0]
                    category_data = row['data'] if hasattr(row, 'keys') else row[1]
                
                # Парсим JSON данные категории
                if isinstance(category_data, str):
                    category_json = json.loads(category_data)
                else:
                    category_json = category_data
                
                # Ищем соответствующие данные по пошлинам
                customs_info = None
                category_lower = category_name.lower()
                
                # Точное совпадение
                if category_lower in CUSTOMS_DATA:
                    customs_info = CUSTOMS_DATA[category_lower]
                else:
                    # Поиск по частичному совпадению
                    for customs_key, customs_value in CUSTOMS_DATA.items():
                        if customs_key in category_lower or category_lower in customs_key:
                            customs_info = customs_value
                            break
                
                if customs_info:
                    # Сохраняем существующий ТН ВЭД код если он есть
                    existing_tnved = category_json.get('tnved_code', '')
                    
                    # Добавляем/обновляем данные по пошлинам
                    if existing_tnved:
                        # Если ТН ВЭД уже есть, только добавляем пошлины
                        category_json['duty_rate'] = customs_info['duty_rate']
                        category_json['vat_rate'] = customs_info['vat_rate']
                        category_json['certificates'] = customs_info['certificates']
                        results.append(f"✅ Обновлены пошлины для: {category_name} (ТН ВЭД: {existing_tnved})")
                    else:
                        # Если ТН ВЭД нет, используем общий код
                        category_json['tnved_code'] = "9999999999"  # Общий код для уточнения
                        category_json['duty_rate'] = customs_info['duty_rate']
                        category_json['vat_rate'] = customs_info['vat_rate']
                        category_json['certificates'] = customs_info['certificates']
                        results.append(f"✅ Добавлены данные для: {category_name} (общий ТН ВЭД)")
                    
                    # Обновляем в БД
                    updated_data = json.dumps(category_json, ensure_ascii=False)
                    
                    if db_type == 'postgres':
                        cursor.execute(
                            "UPDATE categories SET data = %s WHERE category = %s",
                            (updated_data, category_name)
                        )
                    else:
                        cursor.execute(
                            "UPDATE categories SET data = ? WHERE category = ?",
                            (updated_data, category_name)
                        )
                    
                    updated_count += 1
                else:
                    results.append(f"⚠️ Нет данных по пошлинам для: {category_name}")
                    
            except Exception as e:
                error_msg = f"❌ Ошибка обработки категории {category_name}: {e}"
                results.append(error_msg)
                continue
        
        conn.commit()
        cursor.close()
        
        return {
            "status": "success",
            "database_type": db_type,
            "categories_found": len(existing_categories),
            "categories_updated": updated_count,
            "details": results[:50]  # Ограничиваем вывод
        }
        
    except Exception as e:
        print(f"❌ Критическая ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных по пошлинам: {str(e)}")

@app.post("/api/force-migrate")
async def force_migrate_database():
    """Принудительная миграция БД - добавляет все недостающие колонки"""
    try:
        from database import get_database_connection
        
        conn, db_type = get_database_connection()
        
        print(f"🔧 Принудительная миграция для {db_type}...")
        
        # Полный список колонок которые должны быть
        required_columns = [
            ('calculation_type', 'VARCHAR(50) DEFAULT \'quick\''),
            ('packing_units_per_box', 'INTEGER'),
            ('packing_box_weight', 'DECIMAL(10,3)'),
            ('packing_box_length', 'DECIMAL(10,2)'),
            ('packing_box_width', 'DECIMAL(10,2)'),
            ('packing_box_height', 'DECIMAL(10,2)'),
            ('packing_total_boxes', 'INTEGER'),
            ('packing_total_volume', 'DECIMAL(10,4)'),
            ('packing_total_weight', 'DECIMAL(10,3)'),
            ('tnved_code', 'VARCHAR(20)'),
            ('duty_rate', 'VARCHAR(20)'),
            ('vat_rate', 'VARCHAR(20)'),
            ('duty_amount_usd', 'DECIMAL(10,2)'),
            ('vat_amount_usd', 'DECIMAL(10,2)'),
            ('total_customs_cost_usd', 'DECIMAL(10,2)'),
            ('certificates', 'TEXT'),
            ('customs_notes', 'TEXT'),
            ('density_warning_message', 'TEXT'),
            ('calculated_density', 'DECIMAL(10,3)'),
            ('category_density', 'DECIMAL(10,3)')
        ]
        
        success_count = 0
        results = []
        
        for column_name, column_type in required_columns:
            # Каждая колонка в отдельной транзакции для PostgreSQL
            cursor = conn.cursor()
            try:
                if db_type == 'postgres':
                    # Проверяем существование колонки
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'calculations' AND column_name = %s
                    """, (column_name,))
                    
                    if not cursor.fetchone():
                        print(f"➕ Добавляем {column_name}...")
                        cursor.execute(f'ALTER TABLE calculations ADD COLUMN {column_name} {column_type}')
                        conn.commit()
                        print(f"✅ {column_name} добавлена")
                        results.append(f"✅ {column_name} добавлена")
                        success_count += 1
                    else:
                        results.append(f"✓ {column_name} уже существует")
                        
                else:  # SQLite
                    cursor.execute("PRAGMA table_info(calculations)")
                    existing_columns = [row[1] for row in cursor.fetchall()]
                    
                    if column_name not in existing_columns:
                        print(f"➕ Добавляем {column_name}...")
                        # Конвертируем типы для SQLite
                        sqlite_type = column_type.replace('VARCHAR', 'TEXT').replace('DECIMAL', 'REAL')
                        cursor.execute(f'ALTER TABLE calculations ADD COLUMN {column_name} {sqlite_type}')
                        conn.commit()
                        print(f"✅ {column_name} добавлена")
                        results.append(f"✅ {column_name} добавлена")
                        success_count += 1
                    else:
                        results.append(f"✓ {column_name} уже существует")
                        
            except Exception as e:
                # Откатываем транзакцию при ошибке
                try:
                    conn.rollback()
                    print(f"🔄 Rollback для {column_name}")
                except:
                    pass
                    
                error_msg = f"❌ Ошибка с {column_name}: {e}"
                print(error_msg)
                results.append(error_msg)
                continue
            finally:
                cursor.close()
        
        # Проверяем финальное состояние
        cursor = conn.cursor()
        try:
            if db_type == 'postgres':
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'calculations' 
                    ORDER BY column_name
                """)
                final_columns = cursor.fetchall()
                results.append(f"📋 Итого колонок в PostgreSQL: {len(final_columns)}")
            else:
                cursor.execute("PRAGMA table_info(calculations)")
                final_columns = cursor.fetchall()
                results.append(f"📋 Итого колонок в SQLite: {len(final_columns)}")
        except Exception as e:
            results.append(f"⚠️ Не удалось проверить финальное состояние: {e}")
        finally:
            cursor.close()
        
        return {
            "status": "success",
            "database_type": db_type,
            "columns_added": success_count,
            "total_columns_checked": len(required_columns),
            "details": results
        }
        
    except Exception as e:
        print(f"❌ Критическая ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка миграции БД: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка работоспособности системы"""
    try:
        # Проверяем калькулятор
        calc = get_calculator()
        calculator_status = "OK" if calc else "ERROR"
        
        # Проверяем базу данных
        try:
            conn, db_type = get_database_connection()
            if conn:
                db_status = f"OK ({db_type})"
            else:
                db_status = "ERROR"
        except Exception as e:
            db_status = f"ERROR: {str(e)}"
        
        # Проверяем конфигурацию
        try:
            config_loader = ConfigLoader()
            currencies = config_loader.load_currency_rates()
            config_status = "OK" if currencies else "ERROR"
        except Exception as e:
            config_status = f"ERROR: {str(e)}"
        
        status = {
            "status": "healthy" if all([
                calculator_status == "OK",
                db_status.startswith("OK"),
                config_status == "OK"
            ]) else "unhealthy",
            "calculator": calculator_status,
            "database": db_status,
            "config": config_status,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"🏥 Health check: {status}")
        return status
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/reconnect-db")
async def reconnect_database_endpoint(auth: bool = Depends(require_auth)):
    """Принудительное переподключение к базе данных"""
    try:
        from database import reconnect_database
        conn, db_type = reconnect_database()
        
        return {
            "success": True,
            "database_type": db_type,
            "message": f"Переподключение к {db_type} выполнено успешно",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Ошибка переподключения к БД: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/debug/calculate")
async def debug_calculate(request: CalculationRequest):
    """Debug расчет с подробной информацией о категории"""
    try:
        calc = get_calculator()
        
        # Находим категорию
        category = calc.find_category_by_name(request.product_name)
        
        debug_info = {
            "product_name": request.product_name,
            "found_category": category.get('category') if category else None,
            "has_customs_data": bool(category and category.get('duty_rate') and category.get('vat_rate')),
            "category_data": {
                "duty_rate": category.get('duty_rate') if category else None,
                "vat_rate": category.get('vat_rate') if category else None,
                "tnved_code": category.get('tnved_code') if category else None,
                "certificates": category.get('certificates') if category else None
            } if category else None
        }
        
        return debug_info
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate_price(request: CalculationRequest, auth: bool = Depends(require_auth)):
    """Расчет цены товара (требует авторизацию)"""
    return await _calculate_price_logic(request)

@app.post("/api/v2/calculate", response_model=CalculationResponse)
async def calculate_price_v2(request: CalculationRequest):
    """Расчет цены товара V2 (без авторизации для разработки)"""
    # Используем унифицированную функцию (calculation_id=None для создания нового)
    return await _perform_calculation_and_save(request, calculation_id=None)

@app.get("/api/v2/history")
async def get_history_v2():
    """Получение истории расчетов V2 (без авторизации для разработки)"""
    try:
        from database import get_calculation_history
        
        # Получаем последние 50 расчетов
        history = get_calculation_history()
        
        # Форматируем для V2 (упрощенная структура + поля пакинга)
        formatted_history = []
        for item in history:
            formatted_history.append({
                'id': item.get('id'),
                'product_name': item.get('product_name'),
                'product_url': item.get('product_url'),  # Ссылка или WeChat
                'price_yuan': item.get('price_yuan'),
                'weight_kg': item.get('weight_kg'),
                'quantity': item.get('quantity'),
                'markup': item.get('markup'),
                'category': item.get('category'),
                'cost_price_rub': item.get('cost_price_rub'),
                'sale_price_rub': item.get('sale_price_rub'),
                'profit_rub': item.get('profit_rub'),
                'created_at': item.get('created_at'),
                'calculation_type': item.get('calculation_type'),
                # Поля пакинга для копирования
                'packing_units_per_box': item.get('packing_units_per_box'),
                'packing_box_weight': item.get('packing_box_weight'),
                'packing_box_length': item.get('packing_box_length'),
                'packing_box_width': item.get('packing_box_width'),
                'packing_box_height': item.get('packing_box_height'),
                # Кастомные параметры (Stage 3)
                'custom_logistics': item.get('custom_logistics'),
                'forced_category': item.get('forced_category')
            })
        
        # 🔍 DEBUG: Проверяем custom_logistics перед отправкой
        custom_count = sum(1 for item in formatted_history if item.get('custom_logistics'))
        print(f"✅ История V2: {len(formatted_history)} расчетов, {custom_count} с custom_logistics")
        
        return formatted_history
    except Exception as e:
        print(f"❌ Ошибка получения истории V2: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.get("/api/v2/calculation/{calculation_id}/raw")
async def get_calculation_raw_v2(calculation_id: int):
    """DEBUG: Получить сырые данные расчета из БД"""
    try:
        from database import get_database_connection
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgres':
            cursor.execute('SELECT * FROM calculations WHERE id = %s', (calculation_id,))
        else:
            cursor.execute('SELECT * FROM calculations WHERE id = ?', (calculation_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Расчет #{calculation_id} не найден")
        
        # Используем ту же логику, что и в основном endpoint
        if db_type == 'postgres':
            if hasattr(row, 'keys'):
                calculation = dict(row)
            else:
                columns = [desc[0] for desc in cursor.description]
                calculation = dict(zip(columns, row))
        else:
            columns = [desc[0] for desc in cursor.description]
            calculation = dict(zip(columns, row))
        
        cursor.close()
        conn.close()
        
        # Возвращаем сырые данные с типами
        return {
            "id": calculation_id,
            "raw_data": {
                col: {
                    "value": str(calculation.get(col)),
                    "type": type(calculation.get(col)).__name__,
                    "repr": repr(calculation.get(col))
                }
                for col in ['product_name', 'price_yuan', 'quantity', 'weight_kg', 'markup', 
                           'calculation_type', 'packing_units_per_box', 'packing_box_weight']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

@app.get("/api/v2/calculation/{calculation_id}")
async def get_calculation_by_id_v2(calculation_id: int):
    """Получить расчет по ID для V2 (для прямых ссылок)"""
    try:
        from database import get_database_connection
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Получаем расчет из БД (правильный placeholder для типа БД)
        if db_type == 'postgres':
            cursor.execute('SELECT * FROM calculations WHERE id = %s', (calculation_id,))
        else:
            cursor.execute('SELECT * FROM calculations WHERE id = ?', (calculation_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Расчет #{calculation_id} не найден")
        
        # Преобразуем в dict
        # КРИТИЧНО: для PostgreSQL используем column_names из cursor.description
        columns = [desc[0] for desc in cursor.description]  # Всегда получаем имена колонок
        
        if db_type == 'postgres':
            # PostgreSQL cursor возвращает RealDictRow или обычный tuple
            # Пробуем использовать как словарь напрямую
            if hasattr(row, 'keys'):
                # Это уже словарь (RealDictRow)
                calculation = dict(row)
            else:
                # Обычный tuple - создаем dict вручную
                calculation = dict(zip(columns, row))
        else:
            # SQLite всегда возвращает tuple
            calculation = dict(zip(columns, row))
        
        print(f"\n{'='*60}")
        print(f"📖 ЗАГРУЖЕН РАСЧЕТ #{calculation_id}")
        print(f"{'='*60}")
        print(f"🏷️ Товар: {calculation.get('product_name')}")
        print(f"📊 Все колонки из БД: {columns}")
        print(f"\n🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА ТИПОВ ДАННЫХ:")
        for col in ['price_yuan', 'weight_kg', 'quantity', 'markup', 'packing_units_per_box']:
            val = calculation.get(col)
            print(f"   {col:25} = {repr(val):20} | type: {type(val).__name__}")
        print(f"{'='*60}\n")
        
        # Безопасное извлечение значений с проверкой типов
        def safe_float(value, default=None):
            """Безопасное преобразование в float"""
            print(f"🔄 safe_float: входное значение = {repr(value)} | тип = {type(value).__name__} | default = {default}")
            if value is None or value == '':
                print(f"   → Возвращаем default: {default}")
                return default
            try:
                result = float(value)
                print(f"   → ✅ Успешно: {result}")
                return result
            except (ValueError, TypeError) as e:
                print(f"   → ❌ Ошибка преобразования: {e}")
                print(f"   → Возвращаем default: {default}")
                return default
        
        def safe_int(value, default=None):
            """Безопасное преобразование в int"""
            print(f"🔄 safe_int: входное значение = {repr(value)} | тип = {type(value).__name__} | default = {default}")
            if value is None or value == '':
                print(f"   → Возвращаем default: {default}")
                return default
            try:
                result = int(value)
                print(f"   → ✅ Успешно: {result}")
                return result
            except (ValueError, TypeError) as e:
                print(f"   → ❌ Ошибка преобразования: {e}")
                print(f"   → Возвращаем default: {default}")
                return default
        
        # Извлекаем данные с безопасным приведением типов
        price_yuan = safe_float(calculation.get('price_yuan'), None)
        quantity = safe_int(calculation.get('quantity'), None)
        weight_kg = safe_float(calculation.get('weight_kg'), None)
        
        # Проверяем критичные поля ПЕРЕД созданием запроса
        if not price_yuan or price_yuan <= 0:
            raise HTTPException(
                status_code=400, 
                detail=f"❌ Расчет #{calculation_id} поврежден: цена в юанях = {calculation.get('price_yuan')} (тип: {type(calculation.get('price_yuan'))}). Невозможно пересчитать."
            )
        
        if not quantity or quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"❌ Расчет #{calculation_id} поврежден: количество = {calculation.get('quantity')}. Невозможно пересчитать."
            )
        
        # Десериализуем custom_logistics если есть
        custom_logistics = None
        custom_logistics_raw = calculation.get('custom_logistics')
        if custom_logistics_raw:
            import json
            try:
                if isinstance(custom_logistics_raw, str):
                    custom_logistics = json.loads(custom_logistics_raw)
                elif isinstance(custom_logistics_raw, dict):
                    custom_logistics = custom_logistics_raw
                print(f"✅ Загружены кастомные параметры логистики: {list(custom_logistics.keys()) if custom_logistics else 'None'}")
            except json.JSONDecodeError as e:
                print(f"⚠️ Ошибка десериализации custom_logistics: {e}")
        
        # Пересчитываем для получения актуальных маршрутов (с безопасным приведением типов)
        request_data = CalculationRequest(
            product_name=str(calculation.get('product_name', '')),
            product_url=str(calculation.get('product_url', '')),  # Ссылка или WeChat
            price_yuan=price_yuan,
            quantity=quantity,
            markup=safe_float(calculation.get('markup'), 1.4),
            weight_kg=weight_kg,
            is_precise_calculation=(calculation.get('calculation_type') == 'precise'),
            packing_units_per_box=safe_int(calculation.get('packing_units_per_box'), None),
            packing_box_weight=safe_float(calculation.get('packing_box_weight'), None),
            packing_box_length=safe_float(calculation.get('packing_box_length'), None),
            packing_box_width=safe_float(calculation.get('packing_box_width'), None),
            packing_box_height=safe_float(calculation.get('packing_box_height'), None),
            custom_logistics=custom_logistics,
            forced_category=calculation.get('forced_category') or calculation.get('category')
        )
        
        # Выполняем пересчет (без сохранения в БД)
        result = await _calculate_price_logic(request_data)
        
        # КРИТИЧНО: _calculate_price_logic возвращает Pydantic модель,
        # которая не поддерживает item assignment (result['key'] = value)
        # Преобразуем в dict
        result_dict = result.dict() if hasattr(result, 'dict') else dict(result)
        
        # Добавляем ID и дату создания оригинального расчета
        result_dict['id'] = calculation_id
        result_dict['created_at'] = calculation.get('created_at')
        
        print(f"✅ Расчет #{calculation_id} пересчитан и возвращен")
        return result_dict
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка загрузки расчета #{calculation_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def _perform_calculation_and_save(request: CalculationRequest, calculation_id: Optional[int] = None):
    """
    Единая функция для создания и обновления расчетов (использует CalculationService)
    
    Args:
        request: Данные для расчета
        calculation_id: ID существующего расчета (для обновления) или None (для создания)
    
    Returns:
        Результат расчета с ID
    """
    # Получаем сервис
    from services import get_calculation_service
    service = get_calculation_service()
    
    # Выполняем расчет
    result = service.perform_calculation(
        product_name=request.product_name,
        price_yuan=request.price_yuan,
        weight_kg=request.weight_kg,
        quantity=request.quantity,
        custom_rate=request.custom_rate,
        delivery_type=request.delivery_type,
        markup=request.markup,
        product_url=request.product_url,
        packing_units_per_box=request.packing_units_per_box,
        packing_box_weight=request.packing_box_weight,
        packing_box_length=request.packing_box_length,
        packing_box_width=request.packing_box_width,
        packing_box_height=request.packing_box_height,
        custom_logistics=request.custom_logistics,
        forced_category=request.forced_category
    )
    
    # Сохраняем или обновляем в БД
    if calculation_id:
        # Обновление существующего расчета
        service.update_calculation(
            calculation_id,
            result,
            custom_logistics=request.custom_logistics,
            forced_category=request.forced_category
        )
        result['id'] = calculation_id
        print(f"✅ Расчет {calculation_id} обновлен через сервис")
    else:
        # Создание нового расчета
        saved_id = service.create_calculation(
            result,
            custom_logistics=request.custom_logistics,
            forced_category=request.forced_category
        )
        if saved_id:
            result['id'] = saved_id
            result['created_at'] = datetime.now().isoformat()
            print(f"✅ Новый расчет создан через сервис с ID: {saved_id}")
        else:
            result['id'] = None
            result['created_at'] = datetime.now().isoformat()
            print("⚠️ Расчет не сохранен в БД (ID отсутствует)")
    
    return result

async def _calculate_price_logic(request: CalculationRequest):
    """Общая логика расчета цены"""
    try:
        # Логируем входящий запрос для диагностики
        print(f"🔍 API CALCULATE REQUEST:")
        print(f"   product_name: {request.product_name}")
        print(f"   price_yuan: {request.price_yuan}")
        print(f"   weight_kg: {request.weight_kg}")
        print(f"   quantity: {request.quantity}")
        print(f"   is_precise_calculation: {request.is_precise_calculation}")
        
        # Проверяем обязательные поля
        if not request.product_name or not request.product_name.strip():
            raise HTTPException(status_code=400, detail="Название товара не может быть пустым")
        
        if request.price_yuan <= 0:
            raise HTTPException(status_code=400, detail="Цена в юанях должна быть больше 0")
        
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Количество должно быть больше 0")
        
        # Для точных расчетов проверяем данные упаковки
        if request.is_precise_calculation:
            if not request.packing_units_per_box or request.packing_units_per_box <= 0:
                raise HTTPException(status_code=400, detail="Для точных расчетов укажите количество в коробке")
            if not request.packing_box_weight or request.packing_box_weight <= 0:
                raise HTTPException(status_code=400, detail="Для точных расчетов укажите вес коробки")
            if not request.packing_box_length or request.packing_box_length <= 0:
                raise HTTPException(status_code=400, detail="Для точных расчетов укажите длину коробки")
            if not request.packing_box_width or request.packing_box_width <= 0:
                raise HTTPException(status_code=400, detail="Для точных расчетов укажите ширину коробки")
            if not request.packing_box_height or request.packing_box_height <= 0:
                raise HTTPException(status_code=400, detail="Для точных расчетов укажите высоту коробки")
        
        # Вычисляем вес 1 штуки из данных упаковки (для точного расчета)
        calculated_weight_kg = request.weight_kg
        if request.is_precise_calculation:
            if request.packing_box_weight and request.packing_units_per_box:
                calculated_weight_kg = request.packing_box_weight / request.packing_units_per_box
                print(f"📦 Вычислен вес 1 шт из пакинга: {calculated_weight_kg:.3f} кг (вес коробки {request.packing_box_weight} / {request.packing_units_per_box} шт)")
            else:
                raise HTTPException(status_code=400, detail="Для точного расчета нужны данные упаковки")
        else:
            # Для быстрого расчета weight_kg обязателен
            if not calculated_weight_kg or calculated_weight_kg <= 0:
                raise HTTPException(status_code=400, detail="Для быстрого расчета укажите вес 1 шт (weight_kg)")
        
        # Выполняем расчет
        calc = get_calculator()
        if not calc:
            raise HTTPException(status_code=500, detail="Калькулятор не инициализирован")
        
        result = calc.calculate_cost(
            price_yuan=request.price_yuan,
            weight_kg=calculated_weight_kg,
            quantity=request.quantity,
            product_name=request.product_name,
            custom_rate=request.custom_rate,
            delivery_type=request.delivery_type,
            markup=request.markup,
            product_url=request.product_url,
            # Передаем данные упаковки для расчета плотности и Prologix
            packing_units_per_box=request.packing_units_per_box,
            packing_box_weight=request.packing_box_weight,
            packing_box_length=request.packing_box_length,
            packing_box_width=request.packing_box_width,
            packing_box_height=request.packing_box_height,
            # Передаем кастомные параметры логистики (только для этого расчета!)
            custom_logistics_params=request.custom_logistics,
            # Передаем принудительную категорию (если указана)
            forced_category=request.forced_category
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Расчет вернул пустой результат")
        
        print(f"✅ Расчет выполнен успешно для: {request.product_name}")
        
        # Добавляем данные пакинга и тип расчета в результат
        if request.is_precise_calculation or (request.packing_units_per_box is not None and request.packing_units_per_box > 0):
            # Точные расчеты
            result['calculation_type'] = 'precise'
            packing_data = {
                'packing_units_per_box': request.packing_units_per_box or 0,
                'packing_box_weight': request.packing_box_weight or 0,
                'packing_box_length': request.packing_box_length or 0,
                'packing_box_width': request.packing_box_width or 0,
                'packing_box_height': request.packing_box_height or 0
            }
            result.update(packing_data)
            
            # Проверка плотности для точных расчетов
            if all([request.packing_units_per_box, request.packing_box_weight, 
                   request.packing_box_length, request.packing_box_width, request.packing_box_height]):
                
                # Рассчитываем плотность из пакинга
                box_volume = request.packing_box_length * request.packing_box_width * request.packing_box_height
                calculated_density = (request.packing_box_weight / box_volume) if box_volume > 0 else 0
                
                # Получаем плотность из категории
                category_density = result.get('category_density')
                
                if category_density and calculated_density > 0:
                    density_diff_percent = abs(calculated_density - category_density) / category_density * 100
                    
                    if density_diff_percent > 30:
                        result['density_warning'] = {
                            'message': f'Плотность отличается от категории на {density_diff_percent:.1f}%',
                            'calculated_density': round(calculated_density, 1),
                            'category_density': round(category_density, 1),
                            'difference_percent': round(density_diff_percent, 1)
                        }
            
        else:
            # Быстрые расчеты
            result['calculation_type'] = 'quick'
        
        # Проверяем наличие данных контракта
        if 'contract_cost' in result and result['contract_cost'] is not None:
            try:
                cost_per_unit = result['contract_cost']['per_unit']['rub']
                print(f"✅ Контракт рассчитан: {cost_per_unit:.2f} руб за единицу")
            except (KeyError, TypeError) as e:
                print(f"⚠️ Ошибка в структуре contract_cost: {e}")
        else:
            print("ℹ️ Данные контракта отсутствуют (нет информации по пошлинам)")
        
        # Получаем данные по пошлинам
        try:
            category_name = result.get('category', '')
            
            if category_name:
                customs_info = customs_loader.get_customs_info_by_category(category_name)
                if customs_info:
                    result['customs_info'] = customs_info
                    
                    # Рассчитываем таможенные расходы
                    unit_price_usd = result.get('unit_price_yuan', 0) / 7.2  # Примерный курс
                    total_value_usd = unit_price_usd * request.quantity
                    
                    customs_calc = customs_loader.calculate_customs_cost(total_value_usd, customs_info)
                    result['customs_calculations'] = customs_calc
        except Exception as e:
            print(f"WARNING Ошибка получения данных по пошлинам: {e}")
            import traceback
            traceback.print_exc()
            # Не критично, продолжаем без данных по пошлинам
        
        # Сохраняем в базу данных
        try:
            print(f"💾 Попытка сохранения расчета: {request.product_name}")
            calculation_id = save_calculation(result, request)
            
            if calculation_id:
                result['id'] = calculation_id
                result['created_at'] = datetime.now().isoformat()
                print(f"✅ Расчет сохранен в БД с ID: {calculation_id}")
            else:
                print(f"❌ save_calculation вернул None!")
                result['id'] = None
                result['created_at'] = datetime.now().isoformat()
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА сохранения в БД: {e}")
            import traceback
            traceback.print_exc()
            result['id'] = None
            result['created_at'] = datetime.now().isoformat()
        
        return CalculationResponse(**result)
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except ValueError as e:
        print(f"❌ Ошибка валидации данных: {e}")
        raise HTTPException(status_code=400, detail=f"Некорректные данные: {str(e)}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка расчета: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

# CATEGORIES API - moved to backend/api/categories.py
# Подключаем модульный роутер для управления категориями
try:
    from backend.api import categories
    app.include_router(categories.router)
    print("Categories router connected from backend/api/categories.py")
except Exception as e:
    print(f"WARNING: Could not load categories router: {e}")

# V3 API Routers
try:
    from api.v3 import factories_router, positions_router, calculations_router
    app.include_router(factories_router)
    app.include_router(positions_router)
    app.include_router(calculations_router)
    print("✅ V3 API routers connected (factories, positions, calculations)")
except Exception as e:
    print(f"⚠️ WARNING: Could not load V3 API routers: {e}")

@app.get("/debug/categories-without-customs")
async def debug_categories_without_customs():
    """Debug: Анализ категорий без данных по пошлинам"""
    try:
        from database import get_database_connection
        import json
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Получаем все категории
        cursor.execute("SELECT category, data FROM categories")
        all_categories = cursor.fetchall()
        cursor.close()
        
        categories_without_customs = []
        categories_with_tnved_but_no_customs = []
        
        for row in all_categories:
            try:
                if db_type == 'postgres':
                    category_name = row['category'] if isinstance(row, dict) else row[0]
                    category_data = row['data'] if isinstance(row, dict) else row[1]
                else:
                    category_name = row['category'] if hasattr(row, 'keys') else row[0]
                    category_data = row['data'] if hasattr(row, 'keys') else row[1]
                
                # Парсим JSON данные
                if isinstance(category_data, str):
                    category_json = json.loads(category_data)
                else:
                    category_json = category_data
                
                has_tnved = bool(category_json.get('tnved_code'))
                has_duty_rate = bool(category_json.get('duty_rate'))
                has_vat_rate = bool(category_json.get('vat_rate'))
                
                category_info = {
                    "name": category_name,
                    "tnved_code": category_json.get('tnved_code', ''),
                    "duty_rate": category_json.get('duty_rate', ''),
                    "vat_rate": category_json.get('vat_rate', ''),
                    "has_tnved": has_tnved,
                    "has_customs": has_duty_rate and has_vat_rate
                }
                
                if not (has_duty_rate and has_vat_rate):
                    categories_without_customs.append(category_info)
                    
                    if has_tnved:
                        categories_with_tnved_but_no_customs.append(category_info)
                        
            except Exception as e:
                categories_without_customs.append({
                    "name": category_name,
                    "error": str(e)
                })
        
        return {
            "total_categories": len(all_categories),
            "categories_without_customs": len(categories_without_customs),
            "categories_with_tnved_but_no_customs": len(categories_with_tnved_but_no_customs),
            "details": {
                "without_customs": categories_without_customs[:20],  # Первые 20
                "with_tnved_but_no_customs": categories_with_tnved_but_no_customs[:20]
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Ошибка анализа категорий: {str(e)}"}

@app.get("/debug/category/{product_name}")
async def debug_category_by_name(product_name: str):
    """Debug: Получение категории товара по названию без аутентификации"""
    try:
        calc = get_calculator()
        if not calc:
            return {"error": "Calculator not initialized"}
            
        category = calc.find_category_by_name(product_name)
        
        # Отладочная информация
        print(f"🔍 DEBUG: product_name='{product_name}'")
        print(f"🔍 DEBUG: found_category='{category.get('category', 'None') if category else 'None'}'")
        
        if category:
            print(f"🔍 DEBUG: duty_rate='{category.get('duty_rate', 'None')}'")
            print(f"🔍 DEBUG: vat_rate='{category.get('vat_rate', 'None')}'")
            print(f"🔍 DEBUG: tnved_code='{category.get('tnved_code', 'None')}'")
            
        return {
            "product_name": product_name,
            "category_found": category is not None,
            "category_data": category,
            "has_customs_data": bool(category and category.get('duty_rate') and category.get('vat_rate'))
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Ошибка определения категории: {str(e)}"}

@app.get("/api/categories/names")
async def get_category_names():
    """Получение списка названий категорий для автокомплита (без авторизации для V2)"""
    try:
        calc = get_calculator()
        if not calc:
            print("⚠️ get_calculator() вернул None")
            return []
        
        if not hasattr(calc, 'categories'):
            print("⚠️ У калькулятора нет атрибута 'categories'")
            return []
        
        # Формируем список категорий с названием и материалом
        category_names = []
        for cat in calc.categories:
            name = cat.get('category', '')
            material = cat.get('material', '')
            
            if not name:
                continue
            
            # Создаем красивое отображение
            if material:
                display_name = f"{name} ({material})"
            else:
                display_name = name
            
            category_names.append({
                'value': name,  # Реальное значение для отправки в API
                'label': display_name  # Отображаемое название
            })
        
        print(f"✅ Загружено категорий: {len(category_names)}")
        return sorted(category_names, key=lambda x: x['label'])
    except Exception as e:
        print(f"❌ Ошибка получения категорий: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.get("/api/categories/combined-duties")
async def get_combined_duty_categories():
    """Получение списка категорий с комбинированными пошлинами (процент ИЛИ EUR/кг)"""
    try:
        calc = get_calculator()
        if not calc or not hasattr(calc, 'categories'):
            return {"categories": []}
        
        combined_duty_categories = []
        for cat in calc.categories:
            if cat.get('duty_type') == 'combined':
                combined_duty_categories.append({
                    'category': cat.get('category'),
                    'material': cat.get('material'),
                    'duty_type': 'combined',
                    'ad_valorem_rate': cat.get('ad_valorem_rate'),
                    'specific_rate': cat.get('specific_rate'),
                    'vat_rate': cat.get('vat_rate'),
                    'tnved_code': cat.get('tnved_code')
                })
        
        print(f"✅ Найдено категорий с комбинированными пошлинами: {len(combined_duty_categories)}")
        return {
            "count": len(combined_duty_categories),
            "categories": sorted(combined_duty_categories, key=lambda x: x['category'])
        }
    except Exception as e:
        print(f"❌ Ошибка получения категорий с комбинированными пошлинами: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/category/{product_name}")
async def get_category_by_name(product_name: str, auth: bool = Depends(require_auth)):
    """Получение категории товара по названию"""
    try:
        calc = get_calculator()
        category = calc.find_category_by_name(product_name)
        
        # Отладочная информация
        print(f"DEBUG: product_name='{product_name}', result_category='{category['category']}'")
        
        return CategoryInfo(**category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка определения категории: {str(e)}")

@app.get("/api/recommendations/{product_name}")
async def get_recommendations(product_name: str, auth: bool = Depends(require_auth)):
    """Получение рекомендаций по цене, количеству и весу для товара"""
    try:
        calc = get_calculator()
        recommendations = calc.get_recommendations(product_name)
        category = calc.find_category_by_name(product_name)
        
        return {
            "product_name": product_name,
            "category": category.get('category', 'Не определена'),
            "material": category.get('material', ''),
            "tnved_code": category.get('tnved_code', ''),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения рекомендаций: {str(e)}")

@app.get("/api/exchange-rates")
async def get_exchange_rates(auth: bool = Depends(require_auth)):
    """Получение текущих курсов валют"""
    try:
        calc = get_calculator()
        return {
            "yuan_to_usd": calc.currencies["yuan_to_usd"],
            "usd_to_rub": calc.currencies["usd_to_rub"],
            "yuan_to_rub": calc.currencies["yuan_to_rub"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения курсов валют: {str(e)}")

@app.get("/api/settings")
async def get_settings(auth: bool = Depends(require_auth)):
    """Получение всех настроек для страницы настроек"""
    try:
        calc = get_calculator()
        
        # Получаем настройки из конфигурации
        if hasattr(calc, 'formula_config') and calc.formula_config:
            formula = calc.formula_config
            settings = {
                "currencies": {
                    "yuan_to_usd": calc.currencies["yuan_to_usd"],
                    "usd_to_rub": calc.currencies["usd_to_rub"],
                    "yuan_to_rub": calc.currencies["yuan_to_rub"]
                },
                "formula": {
                    "toni_commission_percent": formula.toni_commission_percent,
                    "transfer_percent": formula.transfer_percent,
                    "local_delivery_rate_yuan_per_kg": formula.local_delivery_rate_yuan_per_kg,
                    "msk_pickup_total_rub": formula.msk_pickup_total_rub,
                    "other_costs_percent": formula.other_costs_percent
                }
            }
        else:
            # Fallback к значениям по умолчанию
            settings = {
                "currencies": {
                    "yuan_to_usd": calc.currencies["yuan_to_usd"],
                    "usd_to_rub": calc.currencies["usd_to_rub"],
                    "yuan_to_rub": calc.currencies["yuan_to_rub"]
                },
                "formula": {
                    "toni_commission_percent": 5.0,
                    "transfer_percent": 18.0,
                    "local_delivery_rate_yuan_per_kg": 2.0,
                    "msk_pickup_total_rub": 1000.0,
                    "other_costs_percent": 2.5
                }
            }
        
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@app.post("/api/settings")
async def update_settings(settings: dict, auth: bool = Depends(require_auth)):
    """Обновление настроек"""
    try:
        # Импортируем ConfigLoader для сохранения
        from config.config_loader import get_config_loader
        
        config_loader = get_config_loader()
        success = config_loader.save_settings(settings)
        
        if success:
            # Перезагружаем калькулятор с новыми настройками
            global calculator
            calculator = None  # Это заставит get_calculator() создать новый экземпляр
            calc = get_calculator()
            
            return {"success": True, "message": "Настройки успешно сохранены"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось сохранить настройки")
            
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения настроек: {str(e)}")

@app.get("/api/history")
async def get_history(auth: bool = Depends(require_auth)):
    """Получение истории расчетов"""
    try:
        history = get_history_calculations()
        
        # 🔍 DEBUG: Проверяем custom_logistics перед отправкой на frontend
        print(f"📤 Отправка истории на frontend: {len(history)} записей")
        for item in history:
            if item.get('custom_logistics'):
                print(f"   ✅ ID={item['id']}: custom_logistics присутствует, тип={type(item['custom_logistics'])}")
        
        return {"history": history}
    except Exception as e:
        print(f"WARNING Ошибка загрузки истории: {e}")
        # Возвращаем пустую историю вместо ошибки
        return {"history": [], "error": "База данных недоступна"}

@app.get("/api/calculation/{calculation_id}")
async def get_calculation(calculation_id: int, auth: bool = Depends(require_auth)):
    """Получение конкретного расчета"""
    try:
        # Используем универсальный database модуль
        history = get_history_calculations()
        
        # Ищем расчет по ID
        for calc in history:
            if calc.get('id') == calculation_id:
                return calc
        
        raise HTTPException(status_code=404, detail="Расчет не найден")
        
    except HTTPException:
        raise  # Пропускаем 404 дальше
    except Exception as e:
        print(f"WARNING Ошибка загрузки расчета: {e}")
        raise HTTPException(status_code=503, detail="База данных недоступна")


async def _update_calculation_logic(calculation_id: int, request: CalculationRequest):
    """Общая логика обновления расчета (использует единую функцию)"""
    try:
        print(f"🔄 _update_calculation_logic: ID={calculation_id}, product={request.product_name}")
        result = await _perform_calculation_and_save(request, calculation_id=calculation_id)
        print(f"✅ _update_calculation_logic завершён успешно")
        return result
    except Exception as e:
        print(f"❌ Ошибка в _update_calculation_logic: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.put("/api/calculation/{calculation_id}")
async def update_calculation_endpoint(calculation_id: int, request: CalculationRequest, auth: bool = Depends(require_auth)):
    """Обновление существующего расчета (endpoint /api/calculation/:id)"""
    try:
        return await _update_calculation_logic(calculation_id, request)
    except ValueError as e:
        print(f"ERROR Расчет не найден: {e}")
        raise HTTPException(status_code=404, detail="Расчет не найден")
    except Exception as e:
        print(f"ERROR Ошибка обновления расчета: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка обновления расчета")

@app.put("/api/history/{calculation_id}")
async def update_history_calculation(calculation_id: int, request: CalculationRequest, auth: bool = Depends(require_auth)):
    """Обновление существующего расчета (endpoint /api/history/:id, алиас для совместимости)"""
    try:
        print(f"🔄 PUT /api/history/{calculation_id} - обновление расчета")
        return await _update_calculation_logic(calculation_id, request)
    except ValueError as e:
        print(f"ERROR Расчет не найден: {e}")
        raise HTTPException(status_code=404, detail="Расчет не найден")
    except Exception as e:
        print(f"ERROR Ошибка обновления расчета: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка обновления расчета")

@app.put("/api/v2/calculation/{calculation_id}")
async def update_calculation_v2(calculation_id: int, request: CalculationRequest):
    """Обновление существующего расчета V2 (без авторизации для разработки)"""
    print(f"📥 PUT /api/v2/calculation/{calculation_id} - START")
    print(f"   product_name: {request.product_name}")
    print(f"   price_yuan: {request.price_yuan}")
    print(f"   quantity: {request.quantity}")
    print(f"   custom_logistics (тип: {type(request.custom_logistics)}): {request.custom_logistics}")
    print(f"   forced_category: {request.forced_category}")
    
    try:
        print(f"🔄 Вызов _update_calculation_logic...")
        result = await _update_calculation_logic(calculation_id, request)
        print(f"✅ PUT /api/v2/calculation/{calculation_id} - SUCCESS")
        return result
    except ValueError as e:
        print(f"❌ ERROR Расчет не найден: {e}")
        raise HTTPException(status_code=404, detail="Расчет не найден")
    except Exception as e:
        print(f"❌ ERROR Ошибка обновления расчета: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления расчета: {str(e)}")

# ============================================================================
# V3 API - NEW ARCHITECTURE (State Machine + Strategy Pattern)
# ============================================================================

@app.post("/api/v3/calculate/start")
async def start_calculation_v3(request: CalculationRequest):
    """
    V3: Начало нового расчёта с новой архитектурой.
    
    Возвращает:
    - state: состояние расчёта (READY, PENDING_PARAMS)
    - needs_user_input: нужен ли ввод параметров
    - required_params: список требуемых параметров
    - category: определённая категория
    """
    try:
        from services.calculation_orchestrator import CalculationOrchestrator
        import json
        
        # Загружаем категории из Railway
        with open('config/categories_from_railway.json', 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        # Преобразуем в словарь {category_name: category_data}
        categories = {cat['category']: cat for cat in categories_data['categories']}
        
        # Создаём оркестратор
        orchestrator = CalculationOrchestrator(categories)
        
        # Начинаем расчёт
        response = orchestrator.start_calculation(
            product_name=request.product_name,
            quantity=request.quantity,
            weight_kg=request.weight_kg or 0.5,  # Дефолтный вес
            unit_price_yuan=request.price_yuan,
            markup=request.markup,
            forced_category=request.forced_category
        )
        
        # Добавляем context info для frontend
        context_info = orchestrator.get_context_info()
        response['context'] = context_info
        
        print(f"✅ V3 START: {response['state']} | needs_input: {response['needs_user_input']}")
        
        return response
        
    except Exception as e:
        print(f"❌ V3 START ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v3/calculate/params")
async def provide_custom_params_v3(request: Dict[str, Any]):
    """
    V3: Предоставление кастомных параметров.
    
    Body:
    {
        "product_name": "...",
        "quantity": 100,
        "weight_kg": 0.5,
        "unit_price_yuan": 50,
        "markup": 1.7,
        "forced_category": "...",
        "custom_logistics": {
            "highway_rail": {"custom_rate": 8.5, "duty_rate": 10, "vat_rate": 20},
            "highway_air": {...},
            ...
        }
    }
    """
    try:
        from services.calculation_orchestrator import CalculationOrchestrator
        import json
        
        # Загружаем категории
        with open('config/categories_from_railway.json', 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        categories = {cat['category']: cat for cat in categories_data['categories']}
        
        # Создаём оркестратор
        orchestrator = CalculationOrchestrator(categories)
        
        # Сначала начинаем расчёт
        orchestrator.start_calculation(
            product_name=request.get('product_name'),
            quantity=request.get('quantity'),
            weight_kg=request.get('weight_kg', 0.5),
            unit_price_yuan=request.get('unit_price_yuan'),
            markup=request.get('markup', 1.7),
            forced_category=request.get('forced_category')
        )
        
        # Предоставляем кастомные параметры
        custom_logistics = request.get('custom_logistics', {})
        result = orchestrator.provide_custom_params(custom_logistics)
        
        print(f"✅ V3 PARAMS: valid={result['valid']} | can_calculate={result['can_calculate']}")
        
        return result
        
    except Exception as e:
        print(f"❌ V3 PARAMS ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v3/calculate/execute", response_model=CalculationResultDTO)
async def execute_calculation_v3(request: ProductInputDTO):
    """
    V3: Выполнение расчёта (State Machine + Strategy Pattern).
    
    **Использует Pydantic DTO для валидации входных данных.**
    
    Поддерживает:
    - Стандартные категории (сразу рассчитываются)
    - Кастомные категории (требуют custom_logistics)
    - Переопределение параметров для ЛЮБОЙ категории
    
    Args:
        request (ProductInputDTO): Данные товара с валидацией
        
    Returns:
        CalculationResultDTO: Результат расчёта
    """
    try:
        from services.calculation_orchestrator import CalculationOrchestrator
        
        print(f"🔵 V3 EXECUTE: {request.product_name}")
        print(f"   forced_category: {request.forced_category}")
        print(f"   custom_logistics: {bool(request.custom_logistics)}")
        if request.custom_logistics:
            print(f"   custom_logistics содержимое: {request.custom_logistics}")
            print(f"   custom_logistics тип: {type(request.custom_logistics)}")
        
        # Загружаем категории из БД (как в V2)
        calc = get_calculator()
        if not calc or not hasattr(calc, 'categories'):
            raise ValueError("Не удалось загрузить калькулятор или категории")
        
        # Конвертируем в словарь для оркестратора
        categories = {cat['category']: cat for cat in calc.categories}
        print(f"✅ Загружено категорий из БД: {len(categories)}")
        
        # Создаём оркестратор
        orchestrator = CalculationOrchestrator(categories)
        
        # Начинаем расчёт
        orchestrator.start_calculation(
            product_name=request.product_name,
            quantity=request.quantity,
            weight_kg=request.weight_kg or 0.5,
            unit_price_yuan=request.price_yuan,
            markup=request.markup,
            forced_category=request.forced_category,
            product_url=request.product_url  # Передаём URL товара или WeChat
        )
        
        # Если есть кастомные параметры, предоставляем их
        if request.custom_logistics:
            # request.custom_logistics уже Dict (не DTO), используем напрямую
            params_result = orchestrator.provide_custom_params(request.custom_logistics)
            if not params_result['valid']:
                print(f"❌ Невалидные параметры: {params_result['errors']}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Невалидные параметры: {', '.join(params_result['errors'])}"
                )
        
        # Выполняем расчёт
        calc_result = orchestrator.calculate()
        
        if not calc_result['success']:
            print(f"⚠️ Расчёт не выполнен: {calc_result['error']}")
            
            # Если причина в ожидании параметров - возвращаем частичный ответ
            if 'Ожидание параметров' in calc_result.get('error', ''):
                # Создаём заглушки маршрутов для заполнения
                # ВАЖНО: Добавляем ВСЕ поля которые используются в template
                placeholder_route = {
                    'per_unit': 0,
                    'cost_rub': 0,
                    'cost_usd': 0,
                    'total_cost_rub': 0,
                    'sale_per_unit_rub': 0,  # Для отображения цены продажи
                    'cost_per_unit_rub': 0,  # Для отображения себестоимости
                    'needs_params': True,
                    'placeholder': True
                }
                
                placeholder_routes = {
                    'highway_rail': placeholder_route.copy(),
                    'highway_air': placeholder_route.copy(),
                    'highway_contract': placeholder_route.copy(),
                    'prologix': placeholder_route.copy()
                }
                
                # Создаём минимальный ответ для UI
                partial_result = {
                    'product_name': request.product_name,
                    'category': request.forced_category or 'Новая категория',
                    'unit_price_yuan': request.price_yuan,
                    'quantity': request.quantity,
                    'weight_kg': request.weight_kg or 0.5,
                    'markup': request.markup,
                    'needs_custom_params': True,  # 🔑 Флаг для UI
                    'routes': placeholder_routes,  # Заглушки маршрутов
                    'message': 'Для этой категории требуется указать кастомные параметры логистики'
                }
                print(f"📋 Возвращаем частичный результат с заглушками маршрутов")
                return partial_result
            else:
                # Другая ошибка - возвращаем 400
                raise HTTPException(status_code=400, detail=calc_result['error'])
        
        # Сохраняем в БД через существующий сервис
        from services import get_calculation_service
        service = get_calculation_service()
        
        # ВАЖНО: Если были использованы кастомные параметры, берём их из request
        # (т.к. calculate_cost() не возвращает их в результате)
        # request.custom_logistics уже Dict (не DTO)
        custom_logistics_dict = request.custom_logistics if request.custom_logistics else None
        if custom_logistics_dict:
            # Добавляем в результат для отображения в UI
            calc_result['result']['custom_logistics'] = custom_logistics_dict
        
        saved_id = service.create_calculation(
            calc_result['result'],
            custom_logistics=custom_logistics_dict,
            forced_category=request.forced_category
        )
        
        if saved_id:
            orchestrator.mark_saved(saved_id)
            calc_result['result']['id'] = saved_id
            calc_result['result']['created_at'] = datetime.now().isoformat()
            print(f"✅ V3 EXECUTE SUCCESS: ID={saved_id}")
        
        # Возвращаем результат в формате совместимом с V2
        return calc_result['result']
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ V3 EXECUTE ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v3/categories")
async def get_categories_v3():
    """
    V3: Получение списка всех категорий с метаданными из БД.
    
    Возвращает категории в новом формате с:
    - requirements (что требуется вводить)
    - needs_custom_params (флаг для UI)
    - keywords, tnved_code, certificates
    """
    try:
        # Загружаем категории из БД (как в V2)
        calc = get_calculator()
        if not calc or not hasattr(calc, 'categories'):
            raise ValueError("Не удалось загрузить калькулятор или категории")
        
        return {
            'total': len(calc.categories),
            'version': '3.0',
            'source': 'PostgreSQL (Railway)',
            'categories': calc.categories
        }
        
    except Exception as e:
        print(f"❌ V3 CATEGORIES ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Инициализация БД происходит в lifespan

# 🚀 VUE ROUTER SUPPORT - Явные роуты для SPA (вместо catch-all)
# ВАЖНО: Эти роуты должны быть ПОСЛЕ API endpoints и ПЕРЕД StaticFiles
async def serve_spa(request: Request):
    """
    Обслуживает SPA для Vue Router (history mode)
    Возвращает index.html для всех SPA маршрутов
    """
    # Проверяем авторизацию для всех маршрутов SPA
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    # Возвращаем index.html для Vue Router
    return FileResponse('index.html')

# Явные роуты для Vue Router (чтобы не перехватывать /static/)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return await serve_spa(request)

# 🆕 V2 - Новая версия интерфейса (с авторизацией)
@app.get("/v2", response_class=HTMLResponse)
async def v2_page(request: Request):
    """Новая версия интерфейса с двумя этапами"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    
    return FileResponse('index_v2.html')

@app.get("/precise", response_class=HTMLResponse)
async def precise_page(request: Request):
    return await serve_spa(request)

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return await serve_spa(request)

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return await serve_spa(request)

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    print(f"INFO Запуск Price Calculator на порту {port}...")
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
