"""
V3 Models - Новая архитектура с разделением на Position, Calculation, LogisticsRoute

Структура:
- Factory: Справочник фабрик (для селектора)
- Position: Позиция (что считаем)
- Calculation: Конкретный расчёт от фабрики для тиража
- LogisticsRoute: Маршрут логистики с рассчитанными ценами
- AuditLog: История изменений (для будущего)
"""

from .base import Base
from .factory import Factory
from .position import Position
from .calculation import Calculation
from .logistics_route import LogisticsRoute
from .audit_log import AuditLog

__all__ = [
    'Base',
    'Factory',
    'Position',
    'Calculation',
    'LogisticsRoute',
    'AuditLog',
]

