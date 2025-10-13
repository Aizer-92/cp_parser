"""
Factory Service - управление справочником фабрик
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models_v3 import Factory
from .base_service import BaseService


class FactoryService(BaseService[Factory]):
    """
    Сервис для работы с фабриками
    
    Дополнительные методы:
    - search: поиск фабрик по названию/контакту
    - get_by_name: получить фабрику по точному названию
    """
    
    def __init__(self, db: Session):
        super().__init__(Factory, db)
    
    def search(self, query: str, limit: int = 20) -> List[Factory]:
        """
        Поиск фабрик по названию или контакту
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных фабрик
        """
        search = f"%{query}%"
        return self.db.query(Factory).filter(
            or_(
                Factory.name.ilike(search),
                Factory.contact.ilike(search)
            )
        ).limit(limit).all()
    
    def get_by_name(self, name: str) -> Optional[Factory]:
        """
        Получить фабрику по точному названию
        
        Args:
            name: Название фабрики
            
        Returns:
            Factory или None
        """
        return self.db.query(Factory).filter(Factory.name == name).first()
    
    def get_or_create(self, name: str, **defaults) -> tuple[Factory, bool]:
        """
        Получить существующую фабрику или создать новую
        
        Args:
            name: Название фабрики
            **defaults: Дополнительные поля при создании
            
        Returns:
            (Factory, created: bool)
        """
        factory = self.get_by_name(name)
        if factory:
            return factory, False
        
        factory_data = {'name': name, **defaults}
        factory = self.create(factory_data)
        return factory, True


