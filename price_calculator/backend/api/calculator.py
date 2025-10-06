"""
🧮 CALCULATOR API ROUTER
Эндпоинты для работы с калькулятором
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from price_calculator import PriceCalculator

router = APIRouter(prefix="/api", tags=["calculator"])

# Глобальный экземпляр калькулятора
calculator = None

def get_calculator():
    """Получить экземпляр калькулятора"""
    global calculator
    if calculator is None:
        try:
            calculator = PriceCalculator()
            print("✅ Калькулятор инициализирован")
        except Exception as e:
            print(f"❌ Ошибка инициализации калькулятора: {e}")
            raise HTTPException(status_code=500, detail="Калькулятор недоступен")
    return calculator

# Pydantic модели
class CalculationRequest(BaseModel):
    product_name: str
    product_url: Optional[str] = ""
    price_yuan: float
    weight_kg: Optional[float] = None
    quantity: int
    custom_rate: Optional[float] = None
    delivery_type: str = "rail"
    markup: float = 1.7
    is_precise_calculation: bool = False
    # Поля для точного расчета
    packing_units_per_box: Optional[int] = None
    packing_box_weight: Optional[float] = None
    packing_box_length: Optional[float] = None
    packing_box_width: Optional[float] = None
    packing_box_height: Optional[float] = None

class CalculationResponse(BaseModel):
    product_name: str
    category: str
    quantity: int
    unit_price_yuan: float
    total_price: Dict[str, float]
    weight: Dict[str, float]
    costs: Dict[str, Any]
    sale_price: Dict[str, Any]
    profit: Dict[str, Any]
    delivery_type: str
    logistics: Dict[str, Any]
    local_delivery: Dict[str, Any]
    other_costs: Dict[str, Any]
    msk_pickup: Dict[str, Any]
    currencies: Dict[str, float]
    contract_cost: Optional[Dict[str, Any]] = None
    cost_difference: Optional[Dict[str, Any]] = None
    customs_info: Optional[Dict[str, Any]] = None

@router.post("/calculate", response_model=CalculationResponse)
async def calculate_price(request: CalculationRequest):
    """
    Расчет цены товара
    """
    try:
        calc = get_calculator()
        
        # Выполняем расчет
        result = calc.calculate_cost(
            product_name=request.product_name,
            price_yuan=request.price_yuan,
            weight_kg=request.weight_kg,
            quantity=request.quantity,
            custom_rate=request.custom_rate,
            delivery_type=request.delivery_type,
            markup=request.markup,
            product_url=request.product_url,
            is_precise_calculation=request.is_precise_calculation,
            packing_units_per_box=request.packing_units_per_box,
            packing_box_weight=request.packing_box_weight,
            packing_box_length=request.packing_box_length,
            packing_box_width=request.packing_box_width,
            packing_box_height=request.packing_box_height
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Ошибка расчета: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@router.get("/categories")
async def get_categories():
    """
    Получить список всех категорий товаров
    """
    try:
        calc = get_calculator()
        categories = calc.categories if hasattr(calc, 'categories') else []
        return categories
    except Exception as e:
        print(f"❌ Ошибка получения категорий: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения категорий")

@router.get("/category/{product_name}")
async def get_category(product_name: str):
    """
    Определить категорию товара по названию
    """
    try:
        calc = get_calculator()
        category = calc.find_category_by_name(product_name)
        
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        return category
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка определения категории: {e}")
        raise HTTPException(status_code=500, detail="Ошибка определения категории")

@router.post("/reload-calculator")
async def reload_calculator():
    """
    Перезагрузить калькулятор (обновить данные)
    """
    global calculator
    try:
        calculator = None
        calc = get_calculator()
        return {"success": True, "message": "Калькулятор перезагружен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка перезагрузки: {str(e)}")
