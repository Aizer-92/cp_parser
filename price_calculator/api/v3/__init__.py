"""
V3 API - Новая архитектура API для работы с позициями, расчётами и фабриками
"""

from .factories import router as factories_router
from .positions import router as positions_router
from .calculations import router as calculations_router

__all__ = [
    'factories_router',
    'positions_router',
    'calculations_router',
]

