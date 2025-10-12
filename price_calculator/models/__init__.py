"""
Models package for Price Calculator
Contains data models and business logic entities
"""

from .category import Category, CategoryRequirements
from .calculation_state import CalculationState, CalculationStateMachine
from .dto import (
    # Input DTOs
    ProductInputDTO,
    CustomLogisticsDTO,
    
    # Output DTOs
    CalculationResultDTO,
    RouteCalculationDTO,
    LogisticsBreakdownDTO,
    CustomsBreakdownDTO,
    PackingInfoDTO,
    CustomsInfoDTO,
    DensityWarningDTO,
    
    # Category DTOs
    CategoryDTO,
    CategoryRequirementsDTO,
    CategoriesResponseDTO,
)

__all__ = [
    # Legacy models
    'Category',
    'CategoryRequirements',
    'CalculationState',
    'CalculationStateMachine',
    
    # Input DTOs
    'ProductInputDTO',
    'CustomLogisticsDTO',
    
    # Output DTOs
    'CalculationResultDTO',
    'RouteCalculationDTO',
    'LogisticsBreakdownDTO',
    'CustomsBreakdownDTO',
    'PackingInfoDTO',
    'CustomsInfoDTO',
    'DensityWarningDTO',
    
    # Category DTOs
    'CategoryDTO',
    'CategoryRequirementsDTO',
    'CategoriesResponseDTO',
]



