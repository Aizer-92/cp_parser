"""
⚙️ SETTINGS API ROUTER
Эндпоинты для работы с настройками приложения
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

router = APIRouter(prefix="/api", tags=["settings"])

class CurrencySettings(BaseModel):
    yuan_to_usd: float
    usd_to_rub: float
    yuan_to_rub: float

class FormulaSettings(BaseModel):
    toni_commission_percent: float
    transfer_percent: float
    local_delivery_rate_yuan_per_kg: float
    msk_pickup_total_rub: float
    other_costs_percent: float

class Settings(BaseModel):
    currencies: CurrencySettings
    formula: FormulaSettings

@router.get("/settings", response_model=Settings)
async def get_settings():
    """
    Получить текущие настройки приложения
    """
    try:
        # Импортируем ConfigLoader
        config_dir = Path(__file__).parent.parent.parent / "config"
        if str(config_dir) not in sys.path:
            sys.path.insert(0, str(config_dir))
        
        from config_loader import get_app_config
        app_config = get_app_config()
        
        # Формируем ответ
        settings = {
            "currencies": {
                "yuan_to_usd": app_config.currencies.yuan_to_usd,
                "usd_to_rub": app_config.currencies.usd_to_rub,
                "yuan_to_rub": app_config.currencies.yuan_to_rub
            },
            "formula": {
                "toni_commission_percent": app_config.formula.toni_commission_percent,
                "transfer_percent": app_config.formula.transfer_percent,
                "local_delivery_rate_yuan_per_kg": app_config.formula.local_delivery_rate_yuan_per_kg,
                "msk_pickup_total_rub": app_config.formula.msk_pickup_total_rub,
                "other_costs_percent": app_config.formula.other_costs_percent
            }
        }
        
        return settings
    except Exception as e:
        print(f"❌ Ошибка получения настроек: {e}")
        # Возвращаем дефолтные настройки
        return {
            "currencies": {
                "yuan_to_usd": 0.139,
                "usd_to_rub": 84.0,
                "yuan_to_rub": 11.67
            },
            "formula": {
                "toni_commission_percent": 5.0,
                "transfer_percent": 18.0,
                "local_delivery_rate_yuan_per_kg": 2.0,
                "msk_pickup_total_rub": 1000.0,
                "other_costs_percent": 2.5
            }
        }

@router.post("/settings")
async def save_settings(settings: Settings):
    """
    Сохранить настройки приложения
    """
    try:
        # Импортируем ConfigLoader
        config_dir = Path(__file__).parent.parent.parent / "config"
        if str(config_dir) not in sys.path:
            sys.path.insert(0, str(config_dir))
        
        from config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        
        # Сохраняем настройки
        config_loader.save_settings(
            currencies={
                "yuan_to_usd": settings.currencies.yuan_to_usd,
                "usd_to_rub": settings.currencies.usd_to_rub,
                "yuan_to_rub": settings.currencies.yuan_to_rub
            },
            formula_params={
                "toni_commission_percent": settings.formula.toni_commission_percent,
                "transfer_percent": settings.formula.transfer_percent,
                "local_delivery_rate_yuan_per_kg": settings.formula.local_delivery_rate_yuan_per_kg,
                "msk_pickup_total_rub": settings.formula.msk_pickup_total_rub,
                "other_costs_percent": settings.formula.other_costs_percent
            }
        )
        
        return {"success": True, "message": "Настройки сохранены"}
    except Exception as e:
        print(f"❌ Ошибка сохранения настроек: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения настроек: {str(e)}")

@router.post("/settings/reset")
async def reset_settings():
    """
    Сбросить настройки к значениям по умолчанию
    """
    try:
        default_settings = {
            "currencies": {
                "yuan_to_usd": 0.139,
                "usd_to_rub": 84.0,
                "yuan_to_rub": 11.67
            },
            "formula": {
                "toni_commission_percent": 5.0,
                "transfer_percent": 18.0,
                "local_delivery_rate_yuan_per_kg": 2.0,
                "msk_pickup_total_rub": 1000.0,
                "other_costs_percent": 2.5
            }
        }
        
        # Сохраняем дефолтные настройки
        await save_settings(Settings(**default_settings))
        
        return default_settings
    except Exception as e:
        print(f"❌ Ошибка сброса настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сброса настроек: {str(e)}")
