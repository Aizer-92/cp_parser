"""
Position Model - Позиция (что мы считаем)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Position(Base):
    """
    Позиция - абстрактный товар без привязки к фабрике/тиражу
    
    Пример: "Бутылка с логотипом" - это позиция.
    Для неё может быть несколько расчётов от разных фабрик и с разными тиражами.
    """
    
    __tablename__ = 'positions'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Основная информация
    name = Column(String(255), nullable=False, index=True, comment="Название позиции")
    description = Column(Text, comment="Описание товара")
    category = Column(String(100), index=True, comment="Категория товара")
    
    # Дизайн файлы (ссылки на облако)
    design_files_urls = Column(
        JSONB,
        comment="Массив URL на файлы дизайна в облаке"
    )
    
    # Дополнительные поля
    custom_fields = Column(
        JSONB,
        comment="Дополнительные пользовательские поля (материал, цвет и т.д.)"
    )
    
    # Метаданные
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    calculations = relationship(
        "Calculation",
        back_populates="position",
        cascade="all, delete-orphan",
        order_by="Calculation.quantity"  # Сортировка по тиражу
    )
    
    def __repr__(self):
        return f"<Position(id={self.id}, name='{self.name}')>"
    
    def to_dict(self, include_calculations=False):
        """Сериализация для API"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'design_files_urls': self.design_files_urls or [],
            'custom_fields': self.custom_fields or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_calculations:
            data['calculations'] = [calc.to_dict() for calc in self.calculations]
            data['calculations_count'] = len(self.calculations)
            
            # Добавляем сводную статистику
            if self.calculations:
                quantities = list(set(calc.quantity for calc in self.calculations))
                factories_count = len(set(
                    calc.factory_id or calc.factory_custom_name 
                    for calc in self.calculations
                ))
                
                data['summary'] = {
                    'quantities': sorted(quantities),
                    'factories_count': factories_count,
                }
        
        return data

