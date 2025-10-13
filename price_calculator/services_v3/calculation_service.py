"""
Calculation Service - управление расчётами
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from models_v3 import Calculation, Position, Factory
from .base_service import BaseService


class CalculationService(BaseService[Calculation]):
    """
    Сервис для работы с расчётами
    
    Дополнительные методы:
    - get_by_position: получить все расчёты для позиции
    - get_by_factory: получить все расчёты от фабрики
    - get_with_routes: получить расчёт со всеми маршрутами
    - get_latest: получить последние расчёты
    """
    
    def __init__(self, db: Session):
        super().__init__(Calculation, db)
    
    def get_by_position(self, position_id: int, skip: int = 0, limit: int = 100) -> List[Calculation]:
        """
        Получить все расчёты для определённой позиции
        
        Args:
            position_id: ID позиции
            skip: Пропустить N записей
            limit: Максимальное количество результатов
            
        Returns:
            Список расчётов
        """
        return self.db.query(Calculation).filter(
            Calculation.position_id == position_id
        ).order_by(desc(Calculation.created_at)).offset(skip).limit(limit).all()
    
    def get_by_factory(self, factory_id: int, skip: int = 0, limit: int = 100) -> List[Calculation]:
        """
        Получить все расчёты от определённой фабрики
        
        Args:
            factory_id: ID фабрики
            skip: Пропустить N записей
            limit: Максимальное количество результатов
            
        Returns:
            Список расчётов
        """
        return self.db.query(Calculation).filter(
            Calculation.factory_id == factory_id
        ).order_by(desc(Calculation.created_at)).offset(skip).limit(limit).all()
    
    def get_with_routes(self, id: int) -> Optional[Calculation]:
        """
        Получить расчёт со всеми связанными маршрутами
        
        Args:
            id: ID расчёта
            
        Returns:
            Calculation с загруженными logistics_routes или None
        """
        return self.db.query(Calculation).options(
            joinedload(Calculation.logistics_routes)
        ).filter(Calculation.id == id).first()
    
    def get_with_full_details(self, id: int) -> Optional[Calculation]:
        """
        Получить расчёт со всеми связанными данными (позиция, фабрика, маршруты)
        
        Args:
            id: ID расчёта
            
        Returns:
            Calculation с загруженными relationships или None
        """
        return self.db.query(Calculation).options(
            joinedload(Calculation.position),
            joinedload(Calculation.factory),
            joinedload(Calculation.logistics_routes)
        ).filter(Calculation.id == id).first()
    
    def get_latest(self, limit: int = 50) -> List[Calculation]:
        """
        Получить последние расчёты
        
        Args:
            limit: Максимальное количество результатов
            
        Returns:
            Список последних расчётов
        """
        return self.db.query(Calculation).order_by(
            desc(Calculation.created_at)
        ).limit(limit).all()
    
    def get_by_quantity_range(
        self, 
        position_id: int, 
        min_qty: int, 
        max_qty: int
    ) -> List[Calculation]:
        """
        Получить расчёты для позиции в диапазоне тиражей
        
        Args:
            position_id: ID позиции
            min_qty: Минимальный тираж
            max_qty: Максимальный тираж
            
        Returns:
            Список расчётов
        """
        return self.db.query(Calculation).filter(
            Calculation.position_id == position_id,
            Calculation.quantity >= min_qty,
            Calculation.quantity <= max_qty
        ).order_by(Calculation.quantity).all()


