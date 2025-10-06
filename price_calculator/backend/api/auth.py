"""
🔐 AUTH API ROUTER
Эндпоинты для авторизации
"""

from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel
import secrets
import sys
from pathlib import Path

router = APIRouter(tags=["auth"])

# Хранилище активных сессий (в продакшене использовать Redis)
active_sessions = set()

# Настройки авторизации (будут загружены из конфига)
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "admin123"

def load_auth_config():
    """Загрузить настройки авторизации из конфига"""
    global AUTH_USERNAME, AUTH_PASSWORD
    try:
        config_dir = Path(__file__).parent.parent.parent / "config"
        if str(config_dir) not in sys.path:
            sys.path.insert(0, str(config_dir))
        
        from config_loader import get_app_config
        app_config = get_app_config()
        
        AUTH_USERNAME = app_config.auth.username
        AUTH_PASSWORD = app_config.auth.password
        print("✅ Настройки авторизации загружены из конфига")
    except Exception as e:
        print(f"⚠️ Используем дефолтные настройки авторизации: {e}")

# Загружаем конфиг при импорте
load_auth_config()

def create_session_token() -> str:
    """Создание токена сессии"""
    token = secrets.token_urlsafe(32)
    active_sessions.add(token)
    return token

def verify_session(session_token: str = None) -> bool:
    """Проверка валидности сессии"""
    return session_token and session_token in active_sessions

class LoginRequest(BaseModel):
    username: str
    password: str

@router.get("/login")
async def login_page():
    """Страница входа"""
    return FileResponse('login.html')

@router.post("/api/login")
async def login(request: LoginRequest, response: Response):
    """
    Вход в систему
    """
    if request.username == AUTH_USERNAME and request.password == AUTH_PASSWORD:
        # Создаем сессию
        session_token = create_session_token()
        
        # Устанавливаем cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=86400,  # 24 часа
            samesite="lax"
        )
        
        return {
            "success": True,
            "message": "Успешный вход",
            "redirect": "/"
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )

@router.post("/api/logout")
async def logout(response: Response, request: Request):
    """
    Выход из системы
    """
    session_token = request.cookies.get("session_token")
    
    # Удаляем сессию
    if session_token and session_token in active_sessions:
        active_sessions.remove(session_token)
    
    # Удаляем cookie
    response.delete_cookie("session_token")
    
    return {"success": True, "message": "Выход выполнен"}

@router.get("/api/auth/status")
async def auth_status(request: Request):
    """
    Проверка статуса авторизации
    """
    session_token = request.cookies.get("session_token")
    is_authenticated = verify_session(session_token)
    
    return {
        "authenticated": is_authenticated,
        "username": AUTH_USERNAME if is_authenticated else None
    }

# Экспортируем функции для использования в других модулях
__all__ = ['router', 'verify_session', 'active_sessions']
