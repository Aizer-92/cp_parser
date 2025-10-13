"""
Logistics Service - управление маршрутами логистики
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models_v3 import LogisticsRoute
from .base_service import BaseService


class LogisticsService(BaseService[LogisticsRoute]):
    """
    Сервис для работы с маршрутами логистики
    
    Дополнительные методы:
    - get_by_calculation: получить все маршруты для расчёта
    - get_route: получить конкретный маршрут расчёта
    - update_route: обновить или создать маршрут
    - get_cheapest_route: найти самый дешевый маршрут
    """
    
    def __init__(self, db: Session):
        super().__init__(LogisticsRoute, db)
    
    def get_by_calculation(self, calculation_id: int) -> List[LogisticsRoute]:
        """
        Получить все маршруты для определённого расчёта
        
        Args:
            calculation_id: ID расчёта
            
        Returns:
            Список маршрутов
        """
        return self.db.query(LogisticsRoute).filter(
            LogisticsRoute.calculation_id == calculation_id
        ).all()
    
    def get_route(self, calculation_id: int, route_name: str) -> Optional[LogisticsRoute]:
        """
        Получить конкретный маршрут для расчёта
        
        Args:
            calculation_id: ID расчёта
            route_name: Название маршрута (highway_rail, highway_air, etc.)
            
        Returns:
            LogisticsRoute или None
        """
        return self.db.query(LogisticsRoute).filter(
            and_(
                LogisticsRoute.calculation_id == calculation_id,
                LogisticsRoute.route_name == route_name
            )
        ).first()
    
    def update_route(self, calculation_id: int, route_name: str, route_data: dict) -> LogisticsRoute:
        """
        Обновить существующий маршрут или создать новый
        
        Args:
            calculation_id: ID расчёта
            route_name: Название маршрута
            route_data: Данные маршрута
            
        Returns:
            Обновленный или созданный маршрут
        """
        existing = self.get_route(calculation_id, route_name)
        
        if existing:
            # Обновляем существующий
            for field, value in route_data.items():
                setattr(existing, field, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Создаем новый
            route_data['calculation_id'] = calculation_id
            route_data['route_name'] = route_name
            return self.create(route_data)
    
    def get_cheapest_route(self, calculation_id: int) -> Optional[LogisticsRoute]:
        """
        Найти самый дешевый маршрут для расчёта (по себестоимости в рублях)
        
        Args:
            calculation_id: ID расчёта
            
        Returns:
            LogisticsRoute с минимальной cost_price_rub или None
        """
        return self.db.query(LogisticsRoute).filter(
            LogisticsRoute.calculation_id == calculation_id,
            LogisticsRoute.cost_price_rub.isnot(None)
        ).order_by(LogisticsRoute.cost_price_rub).first()
    
    def get_most_profitable_route(self, calculation_id: int) -> Optional[LogisticsRoute]:
        """
        Найти самый прибыльный маршрут для расчёта
        
        Args:
            calculation_id: ID расчёта
            
        Returns:
            LogisticsRoute с максимальной profit_rub или None
        """
        return self.db.query(LogisticsRoute).filter(
            LogisticsRoute.calculation_id == calculation_id,
            LogisticsRoute.profit_rub.isnot(None)
        ).order_by(LogisticsRoute.profit_rub.desc()).first()
    
    def delete_calculation_routes(self, calculation_id: int) -> int:
        """
        Удалить все маршруты для расчёта
        
        Args:
            calculation_id: ID расчёта
            
        Returns:
            Количество удаленных маршрутов
        """
        deleted = self.db.query(LogisticsRoute).filter(
            LogisticsRoute.calculation_id == calculation_id
        ).delete()
        self.db.commit()
        return deleted


