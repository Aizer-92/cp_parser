"""
Загрузчик конфигурации для Price Calculator
Часть ФАЗЫ 1 рефакторинга: централизованная загрузка настроек
"""

import yaml
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CurrencyRates:
    """Курсы валют"""
    yuan_to_usd: float
    usd_to_rub: float
    yuan_to_rub: float

@dataclass  
class AuthConfig:
    """Настройки аутентификации"""
    username: str
    password: str
    session_secret: str

@dataclass
class FormulaConfig:
    """Настройки формулы расчета"""
    toni_commission_percent: float
    transfer_percent: float
    local_delivery_rate_yuan_per_kg: float
    msk_pickup_total_rub: float
    other_costs_percent: float


@dataclass
class AppConfig:
    """Основные настройки приложения"""
    currencies: CurrencyRates
    auth: AuthConfig
    categories: List[Dict[str, Any]]
    formula: FormulaConfig
    
class ConfigLoader:
    """Загрузчик всех конфигураций приложения"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            self.config_dir = Path(__file__).parent
        else:
            self.config_dir = Path(config_dir)
    
    def load_categories(self) -> List[Dict[str, Any]]:
        """Загрузка категорий из YAML файла"""
        categories_file = self.config_dir / "categories.yaml"
        
        if not categories_file.exists():
            print(f"⚠️  YAML файл категорий не найден: {categories_file}")
            return self._get_fallback_categories()
        
        try:
            with open(categories_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            categories = data.get('categories', [])
            print(f"Загружено {len(categories)} категорий из YAML")
            return categories
            
        except Exception as e:
            print(f"Ошибка загрузки YAML: {e}")
            return self._get_fallback_categories()
    
    def _get_fallback_categories(self) -> List[Dict[str, Any]]:
        """Fallback к старому способу загрузки"""
        try:
            # Пытаемся импортировать из categories_data.py  
            import sys
            parent_dir = str(self.config_dir.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                
            from categories_data import CATEGORIES_DATA
            print(f"Fallback: загружено {len(CATEGORIES_DATA)} категорий из categories_data.py")
            return CATEGORIES_DATA
            
        except ImportError:
            print("Не удалось загрузить категории ни из YAML, ни из Python")
            return []
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Сохранение настроек в файлы конфигурации"""
        try:
            print(f"Сохраняем настройки: {settings}")
            
            # Сохраняем настройки формулы в calculation_settings.yaml
            if 'formula' in settings:
                formula_settings = settings['formula']
                settings_file = self.config_dir / "calculation_settings.yaml"
                
                # Подготавливаем структуру для YAML
                yaml_data = {
                    'formula': {
                        'toni_commission_percent': float(formula_settings.get('toni_commission_percent', 5.0)),
                        'transfer_percent': float(formula_settings.get('transfer_percent', 18.0)),
                        'local_delivery_rate_yuan_per_kg': float(formula_settings.get('local_delivery_rate_yuan_per_kg', 2.0)),
                        'msk_pickup_total_rub': float(formula_settings.get('msk_pickup_total_rub', 1000.0)),
                        'other_costs_percent': float(formula_settings.get('other_costs_percent', 2.5))
                    }
                }
                
                # Сохраняем в YAML файл
                with open(settings_file, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
                
                print(f"✅ Настройки формулы сохранены в {settings_file}")
            
            # Сохраняем курсы валют в environment variables файл (или отдельный файл)
            if 'currencies' in settings:
                currencies = settings['currencies']
                currencies_file = self.config_dir / "currencies.yaml"
                
                yaml_data = {
                    'currencies': {
                        'yuan_to_usd': float(currencies.get('yuan_to_usd', 0.139)),
                        'usd_to_rub': float(currencies.get('usd_to_rub', 84.0))
                        # yuan_to_rub вычисляется автоматически
                    }
                }
                
                with open(currencies_file, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
                
                print(f"✅ Курсы валют сохранены в {currencies_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_currency_rates(self) -> CurrencyRates:
        """Загрузка курсов валют из файла или переменных окружения"""
        # Сначала пытаемся загрузить из файла currencies.yaml
        currencies_file = self.config_dir / "currencies.yaml"
        
        yuan_to_usd = 0.139  # Default: 1/7.2
        usd_to_rub = 84.0    # Default
        
        if currencies_file.exists():
            try:
                with open(currencies_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                
                currencies = data.get('currencies', {})
                yuan_to_usd = float(currencies.get('yuan_to_usd', yuan_to_usd))
                usd_to_rub = float(currencies.get('usd_to_rub', usd_to_rub))
                print(f"✅ Курсы валют загружены из файла: {currencies_file}")
                
            except Exception as e:
                print(f"❌ Ошибка загрузки currencies.yaml: {e}")
                print("Используем значения по умолчанию")
        else:
            print("Файл currencies.yaml не найден, используем значения по умолчанию")
        
        # Позволяем переопределить через переменные окружения
        yuan_to_usd = float(os.environ.get('YUAN_TO_USD', str(yuan_to_usd)))
        usd_to_rub = float(os.environ.get('USD_TO_RUB', str(usd_to_rub)))
        yuan_to_rub = usd_to_rub * yuan_to_usd  # Вычисляем автоматически
        
        print(f"Курсы валют: 1 yuan = ${yuan_to_usd:.3f} = {yuan_to_rub:.2f} rub")
        
        return CurrencyRates(
            yuan_to_usd=yuan_to_usd,
            usd_to_rub=usd_to_rub,  
            yuan_to_rub=yuan_to_rub
        )
    
    def load_formula_config(self) -> FormulaConfig:
        """Загрузка параметров формулы из YAML либо из переменных окружения"""
        settings_file = self.config_dir / "calculation_settings.yaml"

        defaults = {
            'toni_commission_percent': 5.0,
            'transfer_percent': 18.0,
            'local_delivery_rate_yuan_per_kg': 2.0,
            'msk_pickup_total_rub': 1000.0,
            'other_costs_percent': 2.5,
        }

        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                formula = data.get('formula', {})
                defaults.update({
                    key: float(formula.get(key, defaults[key]))
                    for key in defaults
                })
                print("✅ Параметры формулы загружены из YAML")
            except Exception as e:
                print("Не удалось загрузить calculation_settings.yaml: {}. Используем значения по умолчанию".format(e))
        else:
            print("Файл calculation_settings.yaml не найден, используются значения по умолчанию")

        # Позволяем переопределить через ENV
        defaults['toni_commission_percent'] = float(os.environ.get('FORMULA_TONI_PERCENT', defaults['toni_commission_percent']))
        defaults['transfer_percent'] = float(os.environ.get('FORMULA_TRANSFER_PERCENT', defaults['transfer_percent']))
        defaults['local_delivery_rate_yuan_per_kg'] = float(os.environ.get('FORMULA_LOCAL_DELIVERY_RATE', defaults['local_delivery_rate_yuan_per_kg']))
        defaults['msk_pickup_total_rub'] = float(os.environ.get('FORMULA_MSK_PICKUP_RUB', defaults['msk_pickup_total_rub']))
        defaults['other_costs_percent'] = float(os.environ.get('FORMULA_OTHER_COSTS_PERCENT', defaults['other_costs_percent']))

        return FormulaConfig(**defaults)

    def load_auth_config(self) -> AuthConfig:
        """Загрузка настроек аутентификации из переменных окружения"""
        username = os.environ.get('AUTH_USERNAME', 'admin')
        password = os.environ.get('AUTH_PASSWORD', 'admin123')  
        session_secret = os.environ.get('SESSION_SECRET', 'development-secret-key')
        
        # В продакшене должны быть обязательно установлены
        if session_secret == 'development-secret-key':
            print("Используется дефолтный session secret - установите SESSION_SECRET env var")
        
        return AuthConfig(
            username=username,
            password=password,
            session_secret=session_secret
        )
    
    def load_full_config(self) -> AppConfig:
        """Загрузка всех настроек приложения"""
        print("Загрузка конфигурации Price Calculator...")
        
        currencies = self.load_currency_rates()
        auth = self.load_auth_config()  
        categories = self.load_categories()
        formula = self.load_formula_config()
        
        print(f"Конфигурация загружена: {len(categories)} категорий")
        
        return AppConfig(
            currencies=currencies,
            auth=auth,
            categories=categories,
            formula=formula
        )

# Глобальный экземпляр для переиспользования
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Получить глобальный экземпляр ConfigLoader"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def get_app_config() -> AppConfig:
    """Быстрый доступ к полной конфигурации приложения"""
    return get_config_loader().load_full_config()

if __name__ == "__main__":
    # Тест загрузки конфигурации
    print("🧪 Тестирование загрузчика конфигурации...")
    
    config = get_app_config()
    print(f"📊 Результат теста:")
    print(f"   Категорий: {len(config.categories)}")  
    print(f"   Юань → USD: {config.currencies.yuan_to_usd}")
    print(f"   USD → RUB: {config.currencies.usd_to_rub}")
    print(f"   Auth пользователь: {config.auth.username}")

