"""
Calculation Model - Конкретный расчёт от фабрики для тиража
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Calculation(Base):
    """
    Расчёт - конкретный вариант от фабрики для определённого тиража
    
    Пример: "Бутылка" от "Фабрики А" на тираж 500 шт - это один расчёт.
            "Бутылка" от "Фабрики Б" на тираж 500 шт - это другой расчёт.
            "Бутылка" от "Фабрики А" на тираж 1000 шт - это третий расчёт.
    """
    
    __tablename__ = 'v3_calculations'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    position_id = Column(
        Integer,
        ForeignKey('v3_positions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="ID позиции"
    )
    factory_id = Column(
        Integer,
        ForeignKey('v3_factories.id', ondelete='SET NULL'),
        index=True,
        comment="ID фабрики из справочника (опционально)"
    )
    
    # Кастомная фабрика (если не из справочника)
    factory_custom_name = Column(
        String(255),
        comment="Название фабрики (если не из справочника)"
    )
    factory_custom_url = Column(
        Text,
        comment="Ссылка/WeChat фабрики (если не из справочника)"
    )
    
    # Условия от фабрики (переопределяют дефолты из Factory)
    sample_time_days = Column(
        Integer,
        comment="Срок изготовления образца (дней)"
    )
    production_time_days = Column(
        Integer,
        comment="Срок изготовления тиража (дней)"
    )
    sample_price_yuan = Column(
        DECIMAL(10, 2),
        comment="Цена образца (юаней)"
    )
    factory_comment = Column(
        Text,
        comment="Комментарий по этому конкретному расчёту"
    )
    
    # Параметры расчёта
    quantity = Column(
        Integer,
        nullable=False,
        index=True,
        comment="Тираж (количество единиц)"
    )
    price_yuan = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="Цена за единицу в юанях"
    )
    
    # Весовые данные
    calculation_type = Column(
        String(20),
        nullable=False,
        default='quick',
        comment="Тип расчёта: quick (простой вес) или precise (пакинг)"
    )
    weight_kg = Column(
        DECIMAL(10, 3),
        comment="Вес единицы товара (кг) для quick расчёта"
    )
    
    # 📦 ПАКИНГ (для precise расчёта)
    packing_units_per_box = Column(
        Integer,
        comment="Единиц товара в одной коробке"
    )
    packing_box_weight = Column(
        DECIMAL(10, 3),
        comment="Вес одной коробки (кг)"
    )
    packing_box_length = Column(
        DECIMAL(10, 2),
        comment="Длина коробки (см)"
    )
    packing_box_width = Column(
        DECIMAL(10, 2),
        comment="Ширина коробки (см)"
    )
    packing_box_height = Column(
        DECIMAL(10, 2),
        comment="Высота коробки (см)"
    )
    packing_total_boxes = Column(
        Integer,
        comment="Общее количество коробок"
    )
    packing_total_volume = Column(
        DECIMAL(10, 3),
        comment="Общий объём (м³)"
    )
    packing_total_weight = Column(
        DECIMAL(10, 3),
        comment="Общий вес (кг)"
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
    position = relationship("Position", back_populates="calculations")
    factory = relationship("Factory", back_populates="calculations")
    logistics_routes = relationship(
        "LogisticsRoute",
        back_populates="calculation",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            '(factory_id IS NOT NULL OR factory_custom_name IS NOT NULL)',
            name='factory_required'
        ),
    )
    
    def __repr__(self):
        factory_name = self.factory.name if self.factory else self.factory_custom_name
        return f"<Calculation(id={self.id}, position={self.position.name}, factory={factory_name}, qty={self.quantity})>"
    
    def to_dict(self, include_routes=False):
        """Сериализация для API"""
        data = {
            'id': self.id,
            'position_id': self.position_id,
            'factory_id': self.factory_id,
            'factory_custom_name': self.factory_custom_name,
            'factory_custom_url': self.factory_custom_url,
            'sample_time_days': self.sample_time_days,
            'production_time_days': self.production_time_days,
            'sample_price_yuan': float(self.sample_price_yuan) if self.sample_price_yuan else None,
            'factory_comment': self.factory_comment,
            'quantity': self.quantity,
            'price_yuan': float(self.price_yuan),
            'calculation_type': self.calculation_type,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'packing_units_per_box': self.packing_units_per_box,
            'packing_box_weight': float(self.packing_box_weight) if self.packing_box_weight else None,
            'packing_box_length': float(self.packing_box_length) if self.packing_box_length else None,
            'packing_box_width': float(self.packing_box_width) if self.packing_box_width else None,
            'packing_box_height': float(self.packing_box_height) if self.packing_box_height else None,
            'packing_total_boxes': self.packing_total_boxes,
            'packing_total_volume': float(self.packing_total_volume) if self.packing_total_volume else None,
            'packing_total_weight': float(self.packing_total_weight) if self.packing_total_weight else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Добавляем информацию о фабрике
        if self.factory:
            data['factory_info'] = self.factory.to_dict()
        
        # Добавляем маршруты логистики
        if include_routes:
            data['logistics_routes'] = [route.to_dict() for route in self.logistics_routes]
        
        return data



