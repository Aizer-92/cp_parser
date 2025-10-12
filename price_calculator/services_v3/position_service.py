"""
Position Service - управление позициями товаров
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models_v3 import Position
from .base_service import BaseService


class PositionService(BaseService[Position]):
    """
    Сервис для работы с позициями товаров
    
    Дополнительные методы:
    - search: поиск по названию/описанию
    - get_by_category: получить позиции по категории
    - get_with_calculations: получить позицию со всеми расчётами
    """
    
    def __init__(self, db: Session):
        super().__init__(Position, db)
    
    def search(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[Position]:
        """
        Поиск позиций по названию или описанию
        
        Args:
            query: Поисковый запрос
            category: Фильтр по категории (опционально)
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных позиций
        """
        search = f"%{query}%"
        q = self.db.query(Position).filter(
            or_(
                Position.name.ilike(search),
                Position.description.ilike(search)
            )
        )
        
        if category:
            q = q.filter(Position.category == category)
        
        return q.limit(limit).all()
    
    def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Position]:
        """
        Получить все позиции определенной категории
        
        Args:
            category: Категория товара
            skip: Пропустить N записей
            limit: Максимальное количество результатов
            
        Returns:
            Список позиций
        """
        return self.db.query(Position).filter(
            Position.category == category
        ).offset(skip).limit(limit).all()
    
    def get_with_calculations(self, id: int) -> Optional[Position]:
        """
        Получить позицию со всеми связанными расчётами
        
        Args:
            id: ID позиции
            
        Returns:
            Position с загруженными calculations или None
        """
        from sqlalchemy.orm import joinedload
        return self.db.query(Position).options(
            joinedload(Position.calculations)
        ).filter(Position.id == id).first()
    
    def get_categories(self) -> List[str]:
        """
        Получить список всех уникальных категорий
        
        Returns:
            Список названий категорий
        """
        categories = self.db.query(Position.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]

