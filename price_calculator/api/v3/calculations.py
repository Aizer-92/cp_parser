"""
API endpoints для работы с расчётами
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models_v3 import get_db
from services_v3 import CalculationService, RecalculationService, LogisticsService
from .schemas import (
    CalculationCreate, 
    CalculationUpdate, 
    CalculationResponse,
    CalculationWithRoutesResponse,
    LogisticsRouteResponse,
    RecalculationRequest
)

router = APIRouter(prefix="/api/v3/calculations", tags=["Calculations V3"])


@router.get("/", response_model=List[CalculationResponse])
def get_calculations(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество результатов"),
    position_id: Optional[int] = Query(None, description="Фильтр по позиции"),
    factory_id: Optional[int] = Query(None, description="Фильтр по фабрике"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех расчётов с пагинацией и фильтрацией
    """
    service = CalculationService(db)
    
    if position_id:
        calculations = service.get_by_position(position_id, skip=skip, limit=limit)
    elif factory_id:
        calculations = service.get_by_factory(factory_id, skip=skip, limit=limit)
    else:
        calculations = service.get_latest(limit=limit)
    
    return calculations


@router.get("/latest", response_model=List[CalculationResponse])
def get_latest_calculations(
    limit: int = Query(50, ge=1, le=200, description="Максимальное количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Получить последние расчёты (сортировка по created_at DESC)
    """
    service = CalculationService(db)
    calculations = service.get_latest(limit=limit)
    return calculations


@router.get("/{calculation_id}", response_model=CalculationResponse)
def get_calculation(
    calculation_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить расчёт по ID
    """
    service = CalculationService(db)
    calculation = service.get_by_id(calculation_id)
    if not calculation:
        raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
    return calculation


@router.get("/{calculation_id}/full", response_model=CalculationWithRoutesResponse)
def get_calculation_with_routes(
    calculation_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить расчёт со всеми маршрутами логистики
    """
    service = CalculationService(db)
    calculation = service.get_with_routes(calculation_id)
    if not calculation:
        raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
    
    return {
        **calculation.__dict__,
        "routes": calculation.logistics_routes
    }


@router.get("/{calculation_id}/routes", response_model=List[LogisticsRouteResponse])
def get_calculation_routes(
    calculation_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить все маршруты логистики для расчёта
    """
    logistics_service = LogisticsService(db)
    routes = logistics_service.get_by_calculation(calculation_id)
    return routes


@router.post("/", response_model=CalculationResponse, status_code=201)
def create_calculation(
    calculation: CalculationCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новый расчёт
    
    Note: Маршруты логистики создаются отдельным запросом через POST /{id}/recalculate
    """
    service = CalculationService(db)
    
    # Проверяем, что либо factory_id, либо factory_custom_name указаны
    if not calculation.factory_id and not calculation.factory_custom_name:
        raise HTTPException(
            status_code=400,
            detail="Either factory_id or factory_custom_name must be provided"
        )
    
    new_calculation = service.create(calculation.model_dump())
    return new_calculation


@router.put("/{calculation_id}", response_model=CalculationResponse)
def update_calculation(
    calculation_id: int,
    calculation: CalculationUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить расчёт
    
    Note: Для пересчёта маршрутов используйте POST /{id}/recalculate
    """
    service = CalculationService(db)
    
    # Проверяем существование
    existing = service.get_by_id(calculation_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
    
    # Обновляем только переданные поля
    update_data = calculation.model_dump(exclude_unset=True)
    updated_calculation = service.update(calculation_id, update_data)
    return updated_calculation


@router.post("/{calculation_id}/recalculate", response_model=List[LogisticsRouteResponse])
def recalculate_routes(
    calculation_id: int,
    request: RecalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Пересчитать маршруты логистики для расчёта
    
    Использует старую логику расчёта (price_calculator.py) для вычисления
    себестоимости, продажной цены и прибыли для всех маршрутов.
    
    Args:
        calculation_id: ID расчёта
        request: Параметры для пересчёта (category, custom_logistics)
    
    Returns:
        Список созданных/обновленных маршрутов
    """
    recalc_service = RecalculationService(db)
    
    try:
        routes = recalc_service.recalculate_routes(
            calculation_id=calculation_id,
            category=request.category,
            custom_logistics=request.custom_logistics
        )
        return routes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")


@router.delete("/{calculation_id}", status_code=204)
def delete_calculation(
    calculation_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить расчёт
    
    Note: Все связанные маршруты логистики также будут удалены (CASCADE)
    """
    service = CalculationService(db)
    success = service.delete(calculation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
    return None

