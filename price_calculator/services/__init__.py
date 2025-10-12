"""
Сервисный слой приложения

Содержит бизнес-логику, отделённую от API endpoints
"""

from .calculation_service import CalculationService, get_calculation_service

__all__ = ['CalculationService', 'get_calculation_service']




