"""
Factory Model - Справочник фабрик для селектора
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Factory(Base):
    """
    Фабрика/Поставщик
    
    Справочник фабрик, которые можно выбирать в селекторе при создании расчёта.
    Хранит типичные условия работы с фабрикой (сроки, цены образцов).
    """
    
    __tablename__ = 'v3_factories'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Основная информация
    name = Column(String(255), nullable=False, comment="Название фабрики")
    contact = Column(Text, comment="URL/WeChat/Email для связи")
    comment = Column(Text, comment="Общий комментарий о фабрике")
    
    # Типичные условия (дефолты для новых расчётов)
    default_sample_time_days = Column(
        Integer,
        comment="Типичный срок изготовления образца (дней)"
    )
    default_production_time_days = Column(
        Integer,
        comment="Типичный срок изготовления тиража (дней)"
    )
    default_sample_price_yuan = Column(
        DECIMAL(10, 2),
        comment="Типичная цена образца (юаней)"
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
        back_populates="factory",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Factory(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'comment': self.comment,
            'default_sample_time_days': self.default_sample_time_days,
            'default_production_time_days': self.default_production_time_days,
            'default_sample_price_yuan': float(self.default_sample_price_yuan) if self.default_sample_price_yuan else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }



