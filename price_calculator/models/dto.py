"""
Data Transfer Objects (DTOs) для API v3

Использует Pydantic для валидации и type safety.
Соответствует спецификации DATA_CONTRACT.md v3.0
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime


# ============================================================================
# INPUT DTOs - Входящие данные от клиента
# ============================================================================

class CustomLogisticsDTO(BaseModel):
    """
    Кастомные параметры логистики для переопределения базовых ставок.
    
    Используется когда:
    - Категория "Новая категория" (требует все параметры)
    - Пользователь хочет переопределить стандартные ставки
    """
    
    # Логистические ставки ($/кг)
    highway_rail_rate: Optional[float] = Field(None, ge=0, description="ЖД ставка в $/кг")
    highway_air_rate: Optional[float] = Field(None, ge=0, description="Авиа ставка в $/кг")
    
    # Пошлины и НДС (%)
    duty_rate: Optional[float] = Field(None, ge=0, le=100, description="Адвалорная пошлина %")
    vat_rate: Optional[float] = Field(None, ge=0, le=100, description="НДС %")
    specific_rate: Optional[float] = Field(None, ge=0, description="Специфическая ставка €/кг")
    
    # Тип пошлины
    duty_type: Optional[Literal['percent', 'specific', 'combined']] = Field(
        None, 
        description="Тип пошлины: percent (только %), specific (только €/кг), combined (% ИЛИ €/кг)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "highway_rail_rate": 15.5,
                "highway_air_rate": 18.0,
                "duty_rate": 13.0,
                "vat_rate": 20.0,
                "duty_type": "percent"
            }
        }


class ProductInputDTO(BaseModel):
    """
    Входные данные для расчёта стоимости товара.
    
    Используется в POST /api/v3/calculate/execute
    """
    
    # Обязательные поля
    product_name: str = Field(..., min_length=1, max_length=500, description="Название товара")
    price_yuan: float = Field(..., gt=0, description="Цена за единицу в юанях")
    quantity: int = Field(..., gt=0, description="Количество единиц")
    weight_kg: float = Field(..., gt=0, description="Вес единицы товара в кг")
    markup: float = Field(default=1.7, ge=1.0, description="Наценка (1.7 = 70% наценка)")
    
    # Опциональные поля
    product_url: Optional[str] = Field(None, max_length=1000, description="URL товара")
    
    # Параметры для точного расчёта (packing)
    is_precise_calculation: Optional[bool] = Field(False, description="Флаг точного расчёта")
    packing_units_per_box: Optional[int] = Field(None, gt=0, description="Единиц в коробке")
    packing_box_weight: Optional[float] = Field(None, gt=0, description="Вес коробки в кг")
    packing_box_length: Optional[float] = Field(None, gt=0, description="Длина коробки в см")
    packing_box_width: Optional[float] = Field(None, gt=0, description="Ширина коробки в см")
    packing_box_height: Optional[float] = Field(None, gt=0, description="Высота коробки в см")
    
    # Переопределение категории и параметров
    forced_category: Optional[str] = Field(None, description="Принудительная категория")
    # ВАЖНО: custom_logistics может быть в двух форматах:
    # 1. Dict[str, Dict] - старый формат по маршрутам (V2 совместимость)
    # 2. CustomLogisticsDTO - новый формат (будущее)
    # Пока принимаем оба варианта через Dict для обратной совместимости
    custom_logistics: Optional[Dict[str, Any]] = Field(None, description="Кастомные параметры логистики")
    
    @validator('markup')
    def validate_markup(cls, v):
        """Наценка должна быть >= 1.0 (минимум 100% от себестоимости)"""
        if v < 1.0:
            raise ValueError('Наценка должна быть >= 1.0 (100% от себестоимости)')
        return v
    
    @validator('packing_units_per_box')
    def validate_packing_consistency(cls, v, values):
        """Если указан один параметр упаковки, должны быть указаны все"""
        if v is not None:
            required_fields = ['packing_box_weight', 'packing_box_length', 'packing_box_width', 'packing_box_height']
            for field in required_fields:
                if values.get(field) is None:
                    raise ValueError(f'Для точного расчёта требуются все параметры упаковки: {", ".join(required_fields)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Футболка хлопковая",
                "price_yuan": 50,
                "quantity": 1000,
                "weight_kg": 0.2,
                "markup": 1.7,
                "forced_category": "футболка",
                "custom_logistics": {
                    "highway_rail_rate": 15.5,
                    "duty_rate": 13.0,
                    "vat_rate": 20.0
                }
            }
        }


# ============================================================================
# OUTPUT DTOs - Исходящие данные к клиенту
# ============================================================================

class LogisticsBreakdownDTO(BaseModel):
    """Детальная разбивка логистических затрат"""
    rate_usd_per_kg: float = Field(..., description="Ставка $/кг")
    weight_kg: float = Field(..., description="Вес груза в кг")
    cost_usd: float = Field(..., description="Стоимость логистики в USD")
    cost_rub: float = Field(..., description="Стоимость логистики в RUB")
    surcharge: Optional[float] = Field(None, description="Надбавка за плотность %")


class CustomsBreakdownDTO(BaseModel):
    """Детальная разбивка таможенных платежей"""
    duty_type: Literal['percent', 'specific', 'combined'] = Field(..., description="Тип пошлины")
    duty_rate: Optional[float] = Field(None, description="Адвалорная ставка %")
    specific_rate: Optional[float] = Field(None, description="Специфическая ставка €/кг")
    vat_rate: float = Field(..., description="НДС %")
    
    duty_amount_usd: float = Field(..., description="Сумма пошлины в USD")
    vat_amount_usd: float = Field(..., description="Сумма НДС в USD")
    total_customs_cost_usd: float = Field(..., description="Итого таможня в USD")
    total_customs_cost_rub: float = Field(..., description="Итого таможня в RUB")


class RouteCalculationDTO(BaseModel):
    """
    Результат расчёта по конкретному маршруту.
    
    Поля названы согласно DATA_CONTRACT.md:
    - cost_* = себестоимость
    - sale_* = цена продажи
    - *_per_unit_* = за единицу
    - *_total_* = общая сумма (но здесь не используется total, это в БД)
    """
    
    # Основные цены (за всю партию)
    per_unit: float = Field(..., description="Цена за единицу в рублях (продажная)")
    cost_rub: float = Field(..., description="Общая себестоимость в RUB")
    cost_usd: float = Field(..., description="Общая себестоимость в USD")
    total_cost_rub: float = Field(..., description="Итоговая стоимость с наценкой в RUB")
    
    # Детальная разбивка (за единицу)
    sale_per_unit_rub: float = Field(..., description="Цена продажи за единицу в RUB")
    cost_per_unit_rub: float = Field(..., description="Себестоимость за единицу в RUB")
    
    # Компоненты стоимости (опционально, могут быть None для placeholder)
    logistics: Optional[LogisticsBreakdownDTO] = None
    customs: Optional[CustomsBreakdownDTO] = None
    
    # Флаги состояния
    placeholder: Optional[bool] = Field(False, description="Это заглушка (требует заполнения параметров)")
    needs_params: Optional[bool] = Field(False, description="Требуется заполнить параметры")
    
    # Дополнительная информация
    delivery_time_days: Optional[int] = Field(None, description="Срок доставки в днях")
    recommended: Optional[bool] = Field(False, description="Рекомендуемый маршрут")


class PackingInfoDTO(BaseModel):
    """Информация об упаковке товара"""
    units_per_box: int = Field(..., description="Единиц в коробке")
    box_weight_kg: float = Field(..., description="Вес коробки в кг")
    box_length_cm: float = Field(..., description="Длина коробки в см")
    box_width_cm: float = Field(..., description="Ширина коробки в см")
    box_height_cm: float = Field(..., description="Высота коробки в см")
    
    total_boxes: int = Field(..., description="Всего коробок")
    total_volume_m3: float = Field(..., description="Общий объём в м³")
    total_weight_kg: float = Field(..., description="Общий вес в кг")


class CustomsInfoDTO(BaseModel):
    """Информация о таможенном оформлении"""
    tnved_code: Optional[str] = Field(None, description="Код ТН ВЭД")
    duty_rate: Optional[float] = Field(None, description="Ставка пошлины %")
    vat_rate: Optional[float] = Field(None, description="Ставка НДС %")
    certificates: Optional[List[str]] = Field(None, description="Требуемые сертификаты")
    required_documents: Optional[str] = Field(None, description="Необходимые документы")


class DensityWarningDTO(BaseModel):
    """Предупреждение о плотности груза"""
    message: str = Field(..., description="Текст предупреждения")
    calculated_density: float = Field(..., description="Расчётная плотность кг/м³")
    category_density: Optional[float] = Field(None, description="Типичная плотность категории кг/м³")
    severity: Literal['info', 'warning', 'error'] = Field(..., description="Уровень важности")


class CalculationResultDTO(BaseModel):
    """
    Результат расчёта стоимости товара.
    
    Возвращается из POST /api/v3/calculate/execute
    """
    
    # Базовая информация
    id: Optional[int] = Field(None, description="ID в БД (если сохранён)")
    product_name: str = Field(..., description="Название товара")
    category: str = Field(..., description="Определённая категория")
    unit_price_yuan: float = Field(..., description="Цена за единицу в юанях")
    quantity: int = Field(..., description="Количество")
    weight_kg: float = Field(..., description="Вес единицы в кг")
    markup: float = Field(..., description="Наценка")
    
    # Флаги состояния
    needs_custom_params: Optional[bool] = Field(False, description="Требуются кастомные параметры")
    message: Optional[str] = Field(None, description="Сообщение для пользователя")
    
    # Маршруты логистики
    routes: Dict[str, RouteCalculationDTO] = Field(..., description="Расчёты по маршрутам")
    
    # Дополнительная информация
    packing: Optional[PackingInfoDTO] = Field(None, description="Информация об упаковке")
    customs_info: Optional[CustomsInfoDTO] = Field(None, description="Информация о таможне")
    density_warning: Optional[DensityWarningDTO] = Field(None, description="Предупреждение о плотности")
    
    # Метаданные
    created_at: Optional[str] = Field(None, description="Дата создания (ISO 8601)")
    updated_at: Optional[str] = Field(None, description="Дата обновления (ISO 8601)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "product_name": "Футболка хлопковая",
                "category": "футболка",
                "unit_price_yuan": 50,
                "quantity": 1000,
                "weight_kg": 0.2,
                "markup": 1.7,
                "routes": {
                    "highway_rail": {
                        "per_unit": 450.5,
                        "cost_rub": 300000,
                        "cost_usd": 3200,
                        "total_cost_rub": 510000,
                        "sale_per_unit_rub": 510,
                        "cost_per_unit_rub": 300,
                        "delivery_time_days": 25
                    }
                },
                "created_at": "2025-10-12T15:30:00Z"
            }
        }


# ============================================================================
# CATEGORY DTOs - Для работы с категориями
# ============================================================================

class CategoryRequirementsDTO(BaseModel):
    """Требования к параметрам для категории"""
    requires_logistics_rate: bool = Field(False, description="Требуется ставка логистики")
    requires_duty_rate: bool = Field(False, description="Требуется ставка пошлины")
    requires_vat_rate: bool = Field(False, description="Требуется ставка НДС")
    requires_specific_rate: bool = Field(False, description="Требуется специфическая ставка")


class CategoryDTO(BaseModel):
    """Информация о категории товара"""
    category: str = Field(..., description="Название категории")
    material: Optional[str] = Field(None, description="Материал")
    
    # Базовые ставки логистики ($/кг)
    rail_base: Optional[float] = Field(None, description="Базовая ставка ЖД")
    air_base: Optional[float] = Field(None, description="Базовая ставка Авиа")
    
    # Пошлины и НДС
    duty_rate: Optional[float] = Field(None, description="Пошлина %")
    vat_rate: Optional[float] = Field(None, description="НДС %")
    specific_rate: Optional[float] = Field(None, description="Специфическая ставка €/кг")
    
    # Метаданные
    tnved_code: Optional[str] = Field(None, description="Код ТН ВЭД")
    keywords: Optional[List[str]] = Field(None, description="Ключевые слова для поиска")
    description: Optional[str] = Field(None, description="Описание категории")
    
    # Требования
    requirements: Optional[CategoryRequirementsDTO] = Field(None, description="Требования к параметрам")
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "футболка",
                "material": "хлопок",
                "rail_base": 9.5,
                "air_base": 11.6,
                "duty_rate": 13,
                "vat_rate": 20,
                "tnved_code": "6109100000",
                "keywords": ["футболка", "tshirt", "майка"],
                "requirements": {
                    "requires_logistics_rate": False,
                    "requires_duty_rate": False,
                    "requires_vat_rate": False,
                    "requires_specific_rate": False
                }
            }
        }


class CategoriesResponseDTO(BaseModel):
    """Ответ со списком категорий из GET /api/v3/categories"""
    total: int = Field(..., description="Общее количество категорий")
    version: str = Field(..., description="Версия API")
    source: str = Field(..., description="Источник данных")
    categories: List[CategoryDTO] = Field(..., description="Список категорий")

