"""
API endpoints для работы с позициями товаров
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models_v3 import get_db
from services_v3 import PositionService
from .schemas import PositionCreate, PositionUpdate, PositionResponse

router = APIRouter(prefix="/api/v3/positions", tags=["Positions V3"])


@router.get("/", response_model=List[PositionResponse])
def get_positions(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество результатов"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех позиций с пагинацией и фильтрацией
    """
    service = PositionService(db)
    
    if category:
        positions = service.get_by_category(category, skip=skip, limit=limit)
    else:
        positions = service.get_all(skip=skip, limit=limit)
    
    return positions


@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """
    Получить список всех уникальных категорий
    """
    service = PositionService(db)
    categories = service.get_categories()
    return categories


@router.get("/search", response_model=List[PositionResponse])
def search_positions(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Поиск позиций по названию или описанию
    """
    service = PositionService(db)
    positions = service.search(q, category=category, limit=limit)
    return positions


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить позицию по ID
    """
    service = PositionService(db)
    position = service.get_by_id(position_id)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
    return position


@router.get("/{position_id}/with-calculations")
def get_position_with_calculations(
    position_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить позицию со всеми расчётами
    
    Возвращает позицию с массивом calculations
    """
    service = PositionService(db)
    position = service.get_with_calculations(position_id)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
    
    return {
        "id": position.id,
        "name": position.name,
        "description": position.description,
        "category": position.category,
        "design_files_urls": position.design_files_urls,
        "custom_fields": position.custom_fields,
        "created_at": position.created_at,
        "updated_at": position.updated_at,
        "calculations": [
            {
                "id": calc.id,
                "quantity": calc.quantity,
                "price_yuan": float(calc.price_yuan),
                "calculation_type": calc.calculation_type,
                "factory_id": calc.factory_id,
                "factory_custom_name": calc.factory_custom_name,
                "created_at": calc.created_at,
            }
            for calc in position.calculations
        ]
    }


@router.post("/", response_model=PositionResponse, status_code=201)
def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новую позицию
    """
    service = PositionService(db)
    new_position = service.create(position.model_dump())
    return new_position


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: int,
    position: PositionUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить позицию
    """
    service = PositionService(db)
    
    # Проверяем существование
    existing = service.get_by_id(position_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
    
    # Обновляем только переданные поля
    update_data = position.model_dump(exclude_unset=True)
    updated_position = service.update(position_id, update_data)
    return updated_position


@router.delete("/{position_id}", status_code=204)
def delete_position(
    position_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить позицию
    
    Note: Все связанные расчёты также будут удалены (CASCADE)
    """
    service = PositionService(db)
    success = service.delete(position_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
    return None

