#!/usr/bin/env python3
"""
Price Calculator Web Application
FastAPI + Vue.js интерфейс для расчета цен товаров
"""

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.staticfiles import StaticFiles
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
from database import init_database, save_calculation_to_db, get_calculation_history, restore_from_backup

# Настройки аутентификации
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
        init_database()
        restore_from_backup()
        print("✅ База данных инициализирована!")
    except Exception as e:
        print(f"⚠️ База данных недоступна: {e}")
        print("🔧 Калькулятор будет работать без истории")
    
    print("✅ Сервер запущен!")
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

# Инициализация калькулятора  
calculator = None

def get_calculator():
    global calculator
    if calculator is None:
        calculator = PriceCalculator()
    return calculator

# Pydantic модели
class CalculationRequest(BaseModel):
    product_name: str
    price_yuan: float
    weight_kg: float
    quantity: int
    product_url: Optional[str] = ""
    custom_rate: Optional[float] = None
    delivery_type: str = "rail"  # rail или air
    markup: float = 1.7

class CalculationResponse(BaseModel):
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

class CategoryInfo(BaseModel):
    category: str
    material: str
    density: float
    rates: Dict[str, float]

# База данных инициализируется через database.py

def save_calculation(calculation: dict) -> int:
    """Сохранение расчета в базу данных"""
    try:
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
            'profit_total_usd': calculation['profit']['total']['usd']
        }
        
        return save_calculation_to_db(db_data)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
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
                    <p class="text-red-700 text-sm">⚠️ {{ errorMessage }}</p>
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
    """Главная страница"""
    # Проверяем авторизацию
    session_token = request.cookies.get("session_token")
    if not verify_session(session_token):
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse('index.html')

@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate_price(request: CalculationRequest, auth: bool = Depends(require_auth)):
    """Расчет цены товара"""
    try:
        # Выполняем расчет
        calc = get_calculator()
        result = calc.calculate_cost(
            price_yuan=request.price_yuan,
            weight_kg=request.weight_kg,
            quantity=request.quantity,
            product_name=request.product_name,
            custom_rate=request.custom_rate,
            delivery_type=request.delivery_type,
            markup=request.markup
        )
        
        # Добавляем URL товара
        result['product_url'] = request.product_url or ""
        
        # Сохраняем в базу данных (НЕ КРИТИЧНО если не получится)
        try:
            calculation_id = save_calculation(result)
            result['id'] = calculation_id
            result['created_at'] = datetime.now().isoformat()
        except Exception as e:
            print(f"⚠️ Не удалось сохранить в БД: {e}")
            result['id'] = None
            result['created_at'] = datetime.now().isoformat()
        
        return CalculationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка расчета: {str(e)}")

@app.get("/api/categories", response_model=List[CategoryInfo])
async def get_categories(auth: bool = Depends(require_auth)):
    """Получение списка категорий товаров"""
    try:
        calc = get_calculator()
        categories = []
        for cat in calc.categories:
            categories.append(CategoryInfo(**cat))
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки категорий: {str(e)}")

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

@app.get("/api/history")
async def get_history(auth: bool = Depends(require_auth)):
    """Получение истории расчетов"""
    try:
        history = get_history_calculations()
        return {"history": history}
    except Exception as e:
        print(f"⚠️ Ошибка загрузки истории: {e}")
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
        print(f"⚠️ Ошибка загрузки расчета: {e}")
        raise HTTPException(status_code=503, detail="База данных недоступна")

# Инициализация БД происходит в lifespan

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    print(f"🔧 Запуск Price Calculator на порту {port}...")
    
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
