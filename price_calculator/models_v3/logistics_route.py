"""
LogisticsRoute Model - Маршрут логистики с рассчитанными ценами
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class LogisticsRoute(Base):
    """
    Маршрут логистики - конкретный маршрут доставки для расчёта
    
    Для каждого расчёта может быть несколько маршрутов (Highway ЖД, Авиа, Contract и т.д.).
    Хранит кастомные параметры и рассчитанные цены для каждого маршрута.
    """
    
    __tablename__ = 'logistics_routes'
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    calculation_id = Column(
        Integer,
        ForeignKey('calculations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="ID расчёта"
    )
    
    # Название маршрута
    route_name = Column(
        String(50),
        nullable=False,
        comment="Название маршрута: highway_rail, highway_air, highway_contract, prologix, sea_container"
    )
    
    # Кастомные параметры логистики
    custom_rate = Column(
        DECIMAL(10, 2),
        comment="Кастомная ставка логистики ($/кг)"
    )
    duty_rate = Column(
        DECIMAL(5, 2),
        comment="Кастомная ставка пошлины (%)"
    )
    vat_rate = Column(
        DECIMAL(5, 2),
        comment="Кастомная ставка НДС (%)"
    )
    specific_rate = Column(
        DECIMAL(10, 2),
        comment="Специфическая ставка (если применимо)"
    )
    
    # 💰 Рассчитанные цены (за единицу товара)
    cost_price_rub = Column(
        DECIMAL(10, 2),
        comment="Себестоимость за единицу (₽)"
    )
    cost_price_usd = Column(
        DECIMAL(10, 2),
        comment="Себестоимость за единицу ($)"
    )
    sale_price_rub = Column(
        DECIMAL(10, 2),
        comment="Продажная цена за единицу (₽)"
    )
    sale_price_usd = Column(
        DECIMAL(10, 2),
        comment="Продажная цена за единицу ($)"
    )
    profit_rub = Column(
        DECIMAL(10, 2),
        comment="Прибыль за единицу (₽)"
    )
    profit_usd = Column(
        DECIMAL(10, 2),
        comment="Прибыль за единицу ($)"
    )
    
    # Общие суммы (на весь тираж)
    total_cost_rub = Column(
        DECIMAL(12, 2),
        comment="Общая себестоимость (₽)"
    )
    total_cost_usd = Column(
        DECIMAL(12, 2),
        comment="Общая себестоимость ($)"
    )
    total_sale_rub = Column(
        DECIMAL(12, 2),
        comment="Общая продажная цена (₽)"
    )
    total_sale_usd = Column(
        DECIMAL(12, 2),
        comment="Общая продажная цена ($)"
    )
    total_profit_rub = Column(
        DECIMAL(12, 2),
        comment="Общая прибыль (₽)"
    )
    total_profit_usd = Column(
        DECIMAL(12, 2),
        comment="Общая прибыль ($)"
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
    calculation = relationship("Calculation", back_populates="logistics_routes")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('calculation_id', 'route_name', name='unique_calc_route'),
    )
    
    def __repr__(self):
        return f"<LogisticsRoute(id={self.id}, calc={self.calculation_id}, route={self.route_name})>"
    
    def to_dict(self):
        """Сериализация для API"""
        return {
            'id': self.id,
            'calculation_id': self.calculation_id,
            'route_name': self.route_name,
            # Кастомные параметры
            'custom_rate': float(self.custom_rate) if self.custom_rate else None,
            'duty_rate': float(self.duty_rate) if self.duty_rate else None,
            'vat_rate': float(self.vat_rate) if self.vat_rate else None,
            'specific_rate': float(self.specific_rate) if self.specific_rate else None,
            # Цены за единицу
            'cost_price_rub': float(self.cost_price_rub) if self.cost_price_rub else None,
            'cost_price_usd': float(self.cost_price_usd) if self.cost_price_usd else None,
            'sale_price_rub': float(self.sale_price_rub) if self.sale_price_rub else None,
            'sale_price_usd': float(self.sale_price_usd) if self.sale_price_usd else None,
            'profit_rub': float(self.profit_rub) if self.profit_rub else None,
            'profit_usd': float(self.profit_usd) if self.profit_usd else None,
            # Общие суммы
            'total_cost_rub': float(self.total_cost_rub) if self.total_cost_rub else None,
            'total_cost_usd': float(self.total_cost_usd) if self.total_cost_usd else None,
            'total_sale_rub': float(self.total_sale_rub) if self.total_sale_rub else None,
            'total_sale_usd': float(self.total_sale_usd) if self.total_sale_usd else None,
            'total_profit_rub': float(self.total_profit_rub) if self.total_profit_rub else None,
            'total_profit_usd': float(self.total_profit_usd) if self.total_profit_usd else None,
            # Метаданные
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }



