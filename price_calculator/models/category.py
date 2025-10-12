"""
Category models for Price Calculator
Defines category structure and requirements
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CategoryRequirements:
    """
    Требования категории к параметрам.
    Определяет какие параметры должен ввести пользователь.
    """
    requires_logistics_rate: bool = False
    requires_duty_rate: bool = False
    requires_vat_rate: bool = False
    requires_specific_rate: bool = False
    
    def is_complete(self, provided_params: Dict[str, Any]) -> bool:
        """
        Проверяет все ли требуемые параметры предоставлены
        
        Args:
            provided_params: Словарь предоставленных параметров
            
        Returns:
            bool: True если все требуемые параметры есть
        """
        # Обработка None
        if provided_params is None:
            return False
        
        checks = []
        
        if self.requires_logistics_rate:
            # Проверяем что есть custom_rate в любом маршруте
            has_rate = False
            for route_params in provided_params.values():
                if isinstance(route_params, dict) and 'custom_rate' in route_params:
                    has_rate = True
                    break
            checks.append(has_rate)
            
        if self.requires_duty_rate:
            has_duty = False
            for route_params in provided_params.values():
                if isinstance(route_params, dict) and 'duty_rate' in route_params:
                    has_duty = True
                    break
            checks.append(has_duty)
            
        if self.requires_vat_rate:
            has_vat = False
            for route_params in provided_params.values():
                if isinstance(route_params, dict) and 'vat_rate' in route_params:
                    has_vat = True
                    break
            checks.append(has_vat)
            
        if self.requires_specific_rate:
            has_specific = False
            for route_params in provided_params.values():
                if isinstance(route_params, dict) and 'specific_rate' in route_params:
                    has_specific = True
                    break
            checks.append(has_specific)
        
        # Если нет требований - считаем что всё заполнено
        if not checks:
            return True
            
        return all(checks)
    
    def get_missing_params(self, provided_params: Dict[str, Any]) -> List[str]:
        """
        Получить список отсутствующих параметров
        
        Args:
            provided_params: Словарь предоставленных параметров
            
        Returns:
            List[str]: Список названий отсутствующих параметров
        """
        # Обработка None
        if provided_params is None:
            missing = []
            if self.requires_logistics_rate:
                missing.append('custom_rate')
            if self.requires_duty_rate:
                missing.append('duty_rate')
            if self.requires_vat_rate:
                missing.append('vat_rate')
            if self.requires_specific_rate:
                missing.append('specific_rate')
            return missing
        
        missing = []
        
        if self.requires_logistics_rate:
            has_rate = any(
                isinstance(p, dict) and 'custom_rate' in p 
                for p in provided_params.values()
            )
            if not has_rate:
                missing.append('custom_rate')
        
        if self.requires_duty_rate:
            has_duty = any(
                isinstance(p, dict) and 'duty_rate' in p 
                for p in provided_params.values()
            )
            if not has_duty:
                missing.append('duty_rate')
        
        if self.requires_vat_rate:
            has_vat = any(
                isinstance(p, dict) and 'vat_rate' in p 
                for p in provided_params.values()
            )
            if not has_vat:
                missing.append('vat_rate')
        
        if self.requires_specific_rate:
            has_specific = any(
                isinstance(p, dict) and 'specific_rate' in p 
                for p in provided_params.values()
            )
            if not has_specific:
                missing.append('specific_rate')
        
        return missing


@dataclass
class Category:
    """
    Модель категории товара.
    Содержит все данные о категории и логику определения требований.
    """
    name: str
    material: str = ""
    
    # Базовые ставки (None = не определены, требуют ввода)
    rail_base: Optional[float] = None
    air_base: Optional[float] = None
    contract_base: Optional[float] = None
    
    # Пошлины и НДС
    duty_rate: Optional[float] = None
    vat_rate: Optional[float] = None
    specific_rate: Optional[float] = None
    
    # Требования к параметрам
    requirements: CategoryRequirements = field(default_factory=CategoryRequirements)
    
    # Метаданные
    keywords: List[str] = field(default_factory=list)
    description: str = ""
    tnved_code: str = ""
    certificates: List[str] = field(default_factory=list)
    
    def needs_custom_params(self) -> bool:
        """
        Определяет нужны ли кастомные параметры для этой категории.
        
        Returns:
            bool: True если требуются кастомные параметры
        """
        # ВАЖНО: Если категория "Новая категория" - всегда требуем параметры
        if self.name == "Новая категория":
            return True
        
        # Если базовые ставки не определены или равны 0
        if self.rail_base is None or self.rail_base == 0:
            return True
        if self.air_base is None or self.air_base == 0:
            return True
        
        # Или есть явные требования
        return (self.requirements.requires_logistics_rate or
                self.requirements.requires_duty_rate or
                self.requirements.requires_vat_rate or
                self.requirements.requires_specific_rate)
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Валидирует предоставленные параметры для этой категории.
        
        Args:
            params: Словарь параметров для валидации
            
        Returns:
            tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Если категория не требует параметров - всё ОК
        if not self.needs_custom_params():
            return True, []
        
        # Проверяем через requirements
        if not self.requirements.is_complete(params):
            missing = self.requirements.get_missing_params(params)
            for param in missing:
                errors.append(f"Отсутствует параметр: {param}")
        
        return len(errors) == 0, errors
    
    def get_required_params_names(self) -> List[str]:
        """
        Получить список названий требуемых параметров.
        
        Returns:
            List[str]: Список названий параметров
        """
        params = []
        
        if self.requirements.requires_logistics_rate:
            params.append('custom_rate (логистическая ставка)')
        if self.requirements.requires_duty_rate:
            params.append('duty_rate (пошлина)')
        if self.requirements.requires_vat_rate:
            params.append('vat_rate (НДС)')
        if self.requirements.requires_specific_rate:
            params.append('specific_rate (весовая пошлина)')
        
        # Если базовые ставки не определены
        if self.rail_base is None or self.rail_base == 0:
            if 'custom_rate (логистическая ставка)' not in params:
                params.append('rail_rate (ставка ЖД)')
        if self.air_base is None or self.air_base == 0:
            if 'custom_rate (логистическая ставка)' not in params:
                params.append('air_rate (ставка Авиа)')
        
        return params
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """
        Создаёт Category из словаря (например из БД или YAML).
        
        Args:
            data: Словарь с данными категории
            
        Returns:
            Category: Экземпляр категории
        """
        # Извлекаем базовые поля
        name = data.get('category', '')
        material = data.get('material', '')
        
        # Извлекаем ставки (из rates если есть, или напрямую)
        rates = data.get('rates', {})
        rail_base = rates.get('rail_base') if rates else data.get('rail_base')
        air_base = rates.get('air_base') if rates else data.get('air_base')
        contract_base = rates.get('contract_base') if rates else data.get('contract_base')
        
        # Извлекаем пошлины
        duty_rate = data.get('duty_rate')
        if isinstance(duty_rate, str) and duty_rate.endswith('%'):
            duty_rate = float(duty_rate.rstrip('%'))
        
        vat_rate = data.get('vat_rate')
        if isinstance(vat_rate, str) and vat_rate.endswith('%'):
            vat_rate = float(vat_rate.rstrip('%'))
        
        # Создаём requirements (проверяем вложенный объект requirements)
        req_data = data.get('requirements', {})
        requirements = CategoryRequirements(
            requires_logistics_rate=req_data.get('requires_logistics_rate', data.get('requires_logistics_rate', False)),
            requires_duty_rate=req_data.get('requires_duty_rate', data.get('requires_duty_rate', False)),
            requires_vat_rate=req_data.get('requires_vat_rate', data.get('requires_vat_rate', False)),
            requires_specific_rate=req_data.get('requires_specific_rate', data.get('requires_specific_rate', False))
        )
        
        # Если это "Новая категория" или ставки = 0, автоматически требуем параметры
        if name == "Новая категория" or (rail_base == 0 and air_base == 0):
            requirements.requires_logistics_rate = True
        
        return cls(
            name=name,
            material=material,
            rail_base=rail_base,
            air_base=air_base,
            contract_base=contract_base,
            duty_rate=duty_rate,
            vat_rate=vat_rate,
            requirements=requirements,
            keywords=data.get('keywords', []),
            description=data.get('description', ''),
            tnved_code=data.get('tnved_code', ''),
            certificates=data.get('certificates', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертирует Category в словарь для сериализации.
        
        Returns:
            Dict[str, Any]: Словарь с данными категории
        """
        return {
            'category': self.name,
            'material': self.material,
            'rates': {
                'rail_base': self.rail_base,
                'air_base': self.air_base,
                'contract_base': self.contract_base
            },
            'duty_rate': self.duty_rate,
            'vat_rate': self.vat_rate,
            'specific_rate': self.specific_rate,
            'requirements': {
                'requires_logistics_rate': self.requirements.requires_logistics_rate,
                'requires_duty_rate': self.requirements.requires_duty_rate,
                'requires_vat_rate': self.requirements.requires_vat_rate,
                'requires_specific_rate': self.requirements.requires_specific_rate
            },
            'keywords': self.keywords,
            'description': self.description,
            'tnved_code': self.tnved_code,
            'certificates': self.certificates,
            'needs_custom_params': self.needs_custom_params()
        }

