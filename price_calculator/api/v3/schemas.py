"""
Pydantic schemas для V3 API
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ Factory Schemas ============

class FactoryBase(BaseModel):
    """Базовые поля фабрики"""
    name: str = Field(..., description="Название фабрики")
    contact: Optional[str] = Field(None, description="URL/WeChat/Email для связи")
    comment: Optional[str] = Field(None, description="Общий комментарий о фабрике")
    default_sample_time_days: Optional[int] = Field(None, description="Типичный срок изготовления образца (дней)")
    default_production_time_days: Optional[int] = Field(None, description="Типичный срок изготовления тиража (дней)")
    default_sample_price_yuan: Optional[Decimal] = Field(None, description="Типичная цена образца (юаней)")


class FactoryCreate(FactoryBase):
    """Схема для создания фабрики"""
    pass


class FactoryUpdate(BaseModel):
    """Схема для обновления фабрики"""
    name: Optional[str] = None
    contact: Optional[str] = None
    comment: Optional[str] = None
    default_sample_time_days: Optional[int] = None
    default_production_time_days: Optional[int] = None
    default_sample_price_yuan: Optional[Decimal] = None


class FactoryResponse(FactoryBase):
    """Схема ответа с фабрикой"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Position Schemas ============

class PositionBase(BaseModel):
    """Базовые поля позиции"""
    name: str = Field(..., description="Название позиции")
    description: Optional[str] = Field(None, description="Описание товара")
    category: Optional[str] = Field(None, description="Категория товара")
    design_files_urls: Optional[List[str]] = Field(None, description="Массив URL на файлы дизайна в облаке")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Дополнительные пользовательские поля")


class PositionCreate(PositionBase):
    """Схема для создания позиции"""
    pass


class PositionUpdate(BaseModel):
    """Схема для обновления позиции"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    design_files_urls: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class PositionResponse(PositionBase):
    """Схема ответа с позицией"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Calculation Schemas ============

class CalculationBase(BaseModel):
    """Базовые поля расчёта"""
    position_id: int = Field(..., description="ID позиции")
    factory_id: Optional[int] = Field(None, description="ID фабрики из справочника")
    factory_custom_name: Optional[str] = Field(None, description="Название фабрики (если не из справочника)")
    factory_custom_url: Optional[str] = Field(None, description="Ссылка/WeChat фабрики")
    sample_time_days: Optional[int] = Field(None, description="Срок изготовления образца (дней)")
    production_time_days: Optional[int] = Field(None, description="Срок изготовления тиража (дней)")
    sample_price_yuan: Optional[Decimal] = Field(None, description="Цена образца (юаней)")
    factory_comment: Optional[str] = Field(None, description="Комментарий по этому расчёту")
    quantity: int = Field(..., description="Тираж (количество единиц)")
    price_yuan: Decimal = Field(..., description="Цена за единицу в юанях")
    calculation_type: str = Field(..., description="Тип расчёта: quick или precise")
    weight_kg: Optional[Decimal] = Field(None, description="Вес единицы товара (кг) для quick расчёта")
    # Packing fields
    packing_units_per_box: Optional[int] = None
    packing_box_weight: Optional[Decimal] = None
    packing_box_length: Optional[Decimal] = None
    packing_box_width: Optional[Decimal] = None
    packing_box_height: Optional[Decimal] = None
    packing_total_boxes: Optional[int] = None
    packing_total_volume: Optional[Decimal] = None
    packing_total_weight: Optional[Decimal] = None


class CalculationCreate(CalculationBase):
    """Схема для создания расчёта"""
    pass


class CalculationUpdate(BaseModel):
    """Схема для обновления расчёта"""
    factory_id: Optional[int] = None
    factory_custom_name: Optional[str] = None
    factory_custom_url: Optional[str] = None
    sample_time_days: Optional[int] = None
    production_time_days: Optional[int] = None
    sample_price_yuan: Optional[Decimal] = None
    factory_comment: Optional[str] = None
    quantity: Optional[int] = None
    price_yuan: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    packing_units_per_box: Optional[int] = None
    packing_box_weight: Optional[Decimal] = None
    packing_box_length: Optional[Decimal] = None
    packing_box_width: Optional[Decimal] = None
    packing_box_height: Optional[Decimal] = None


class CalculationResponse(CalculationBase):
    """Схема ответа с расчётом"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ LogisticsRoute Schemas ============

class LogisticsRouteResponse(BaseModel):
    """Схема ответа с маршрутом логистики"""
    id: int
    calculation_id: int
    route_name: str
    custom_rate: Optional[Decimal] = None
    duty_rate: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    specific_rate: Optional[Decimal] = None
    cost_price_rub: Optional[Decimal] = None
    cost_price_usd: Optional[Decimal] = None
    sale_price_rub: Optional[Decimal] = None
    sale_price_usd: Optional[Decimal] = None
    profit_rub: Optional[Decimal] = None
    profit_usd: Optional[Decimal] = None
    total_cost_rub: Optional[Decimal] = None
    total_cost_usd: Optional[Decimal] = None
    total_sale_rub: Optional[Decimal] = None
    total_sale_usd: Optional[Decimal] = None
    total_profit_rub: Optional[Decimal] = None
    total_profit_usd: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Calculation with Routes ============

class CalculationWithRoutesResponse(CalculationResponse):
    """Расчёт со всеми маршрутами"""
    routes: List[LogisticsRouteResponse] = []


# ============ Recalculation Request ============

class RecalculationRequest(BaseModel):
    """Запрос на пересчёт маршрутов"""
    category: Optional[str] = Field(None, description="Категория товара (если None, берется из Position)")
    custom_logistics: Optional[Dict[str, Any]] = Field(None, description="Кастомные ставки логистики")


# ============ Pagination ============

class PaginatedResponse(BaseModel):
    """Шаблон для пагинированного ответа"""
    total: int
    skip: int
    limit: int
    items: List[Any]

