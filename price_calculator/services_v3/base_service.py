"""
Base CRUD Service - абстрактный класс для всех сервисов
"""
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import select

from models_v3.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """
    Базовый CRUD сервис с типизацией
    
    Предоставляет стандартные операции:
    - get_by_id
    - get_all
    - create
    - update
    - delete
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Args:
            model: SQLAlchemy модель
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Получить объект по ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Получить все объекты с пагинацией"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, obj_in: dict) -> ModelType:
        """
        Создать новый объект
        
        Args:
            obj_in: Словарь с данными для создания
            
        Returns:
            Созданный объект
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """
        Обновить объект
        
        Args:
            id: ID объекта
            obj_in: Словарь с данными для обновления
            
        Returns:
            Обновленный объект или None если не найден
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
        
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """
        Удалить объект
        
        Args:
            id: ID объекта
            
        Returns:
            True если удален, False если не найден
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """Получить общее количество объектов"""
        return self.db.query(self.model).count()


