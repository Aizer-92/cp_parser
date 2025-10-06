"""
📚 HISTORY API ROUTER
Эндпоинты для работы с историей расчетов
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from database import get_calculation_history, save_calculation_to_db, update_calculation

router = APIRouter(prefix="/api", tags=["history"])

class CalculationHistoryItem(BaseModel):
    id: int
    product_name: str
    unit_price_yuan: float
    weight_per_unit_kg: float
    quantity: int
    cost_per_unit_rub: float
    sale_price_per_unit_rub: float
    profit_per_unit_rub: float
    total_cost_rub: float
    total_sale_price_rub: float
    total_profit_rub: float
    delivery_type: str
    markup: float
    is_precise_calculation: bool
    created_at: str
    category: Optional[str] = None
    tnved_code: Optional[str] = None
    duty_rate: Optional[str] = None
    vat_rate: Optional[str] = None

@router.get("/history", response_model=List[CalculationHistoryItem])
async def get_history():
    """
    Получить историю расчетов
    """
    try:
        history = get_calculation_history()
        return history
    except Exception as e:
        print(f"❌ Ошибка получения истории: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории: {str(e)}")

@router.delete("/history/{calculation_id}")
async def delete_calculation(calculation_id: int):
    """
    Удалить расчет из истории
    """
    try:
        # Импортируем функцию удаления
        from database import get_database_connection
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        if db_type == "postgresql":
            cursor.execute("DELETE FROM calculations WHERE id = %s", (calculation_id,))
        else:
            cursor.execute("DELETE FROM calculations WHERE id = ?", (calculation_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "message": "Расчет удален"}
    except Exception as e:
        print(f"❌ Ошибка удаления расчета: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")

@router.put("/history/{calculation_id}")
async def update_calculation_endpoint(calculation_id: int, data: Dict[str, Any]):
    """
    Обновить расчет в истории
    """
    try:
        update_calculation(calculation_id, data)
        return {"success": True, "message": "Расчет обновлен"}
    except Exception as e:
        print(f"❌ Ошибка обновления расчета: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {str(e)}")
