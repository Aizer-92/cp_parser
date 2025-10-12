"""
API endpoints для работы с фабриками
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models_v3 import get_db
from services_v3 import FactoryService
from .schemas import FactoryCreate, FactoryUpdate, FactoryResponse

router = APIRouter(prefix="/api/v3/factories", tags=["Factories V3"], redirect_slashes=False)


@router.get("/", response_model=List[FactoryResponse])
def get_factories(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех фабрик с пагинацией
    """
    service = FactoryService(db)
    factories = service.get_all(skip=skip, limit=limit)
    return factories


@router.get("/search", response_model=List[FactoryResponse])
def search_factories(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество результатов"),
    db: Session = Depends(get_db)
):
    """
    Поиск фабрик по названию или контакту
    """
    service = FactoryService(db)
    factories = service.search(q, limit=limit)
    return factories


@router.get("/{factory_id}", response_model=FactoryResponse)
def get_factory(
    factory_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить фабрику по ID
    """
    service = FactoryService(db)
    factory = service.get_by_id(factory_id)
    if not factory:
        raise HTTPException(status_code=404, detail=f"Factory {factory_id} not found")
    return factory


@router.post("/", response_model=FactoryResponse, status_code=201)
def create_factory(
    factory: FactoryCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новую фабрику
    """
    service = FactoryService(db)
    
    # Проверяем, что фабрика с таким именем не существует
    existing = service.get_by_name(factory.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Factory with name '{factory.name}' already exists"
        )
    
    new_factory = service.create(factory.model_dump())
    return new_factory


@router.put("/{factory_id}", response_model=FactoryResponse)
def update_factory(
    factory_id: int,
    factory: FactoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить фабрику
    """
    service = FactoryService(db)
    
    # Проверяем существование
    existing = service.get_by_id(factory_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Factory {factory_id} not found")
    
    # Если меняется имя, проверяем уникальность
    if factory.name and factory.name != existing.name:
        name_conflict = service.get_by_name(factory.name)
        if name_conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Factory with name '{factory.name}' already exists"
            )
    
    # Обновляем только переданные поля
    update_data = factory.model_dump(exclude_unset=True)
    updated_factory = service.update(factory_id, update_data)
    return updated_factory


@router.delete("/{factory_id}", status_code=204)
def delete_factory(
    factory_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить фабрику
    
    Note: Если у фабрики есть связанные расчёты, они будут сохранены (factory_id станет NULL)
    """
    service = FactoryService(db)
    success = service.delete(factory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Factory {factory_id} not found")
    return None

