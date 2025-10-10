"""
Unit tests for Calculation Strategies
"""

import unittest
from models.category import Category, CategoryRequirements
from strategies import StandardCategoryStrategy, CustomCategoryStrategy


class TestStandardCategoryStrategy(unittest.TestCase):
    """Tests for StandardCategoryStrategy"""
    
    def setUp(self):
        """Создаём стратегию и стандартную категорию"""
        self.strategy = StandardCategoryStrategy()
        self.category = Category(
            name="Футболки",
            material="хлопок",
            rail_base=5.0,
            air_base=7.1
        )
    
    def test_no_user_input_required(self):
        """Стандартная категория не требует ввода пользователя"""
        self.assertFalse(self.strategy.requires_user_input(self.category))
    
    def test_no_required_params(self):
        """Стандартная категория не требует дополнительных параметров"""
        params = self.strategy.get_required_params(self.category)
        self.assertEqual(params, [])
    
    def test_validation_always_passes(self):
        """Валидация всегда успешна для стандартной категории"""
        is_valid, errors = self.strategy.validate_params(self.category, {})
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_prepare_calculation_params(self):
        """Подготовка параметров для расчёта"""
        base_params = {
            'quantity': 100,
            'weight_kg': 0.5,
            'unit_price_yuan': 50,
            'markup': 1.7
        }
        
        calc_params = self.strategy.prepare_calculation_params(
            self.category,
            base_params
        )
        
        # Должна быть категория
        self.assertIn('forced_category', calc_params)
        self.assertEqual(calc_params['forced_category'], 'Футболки')
        
        # Базовые параметры сохранены
        self.assertEqual(calc_params['quantity'], 100)
        self.assertEqual(calc_params['weight_kg'], 0.5)
    
    def test_custom_logistics_ignored(self):
        """Кастомные параметры игнорируются для стандартной категории"""
        base_params = {'quantity': 100}
        custom_logistics = {'highway_rail': {'custom_rate': 10.0}}
        
        calc_params = self.strategy.prepare_calculation_params(
            self.category,
            base_params,
            custom_logistics
        )
        
        # custom_logistics не должно быть в результате
        self.assertNotIn('custom_logistics_params', calc_params)
    
    def test_strategy_name(self):
        """Проверка названия стратегии"""
        self.assertEqual(self.strategy.get_strategy_name(), "StandardCategory")


class TestCustomCategoryStrategy(unittest.TestCase):
    """Tests for CustomCategoryStrategy"""
    
    def setUp(self):
        """Создаём стратегию и кастомную категорию"""
        self.strategy = CustomCategoryStrategy()
        self.category = Category(
            name="Новая категория",
            rail_base=0,
            air_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
    
    def test_user_input_required(self):
        """Кастомная категория требует ввода пользователя"""
        self.assertTrue(self.strategy.requires_user_input(self.category))
    
    def test_has_required_params(self):
        """Кастомная категория имеет список требуемых параметров"""
        params = self.strategy.get_required_params(self.category)
        self.assertGreater(len(params), 0)
    
    def test_validation_fails_without_params(self):
        """Валидация не проходит без параметров"""
        is_valid, errors = self.strategy.validate_params(self.category, {})
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validation_fails_with_empty_params(self):
        """Валидация не проходит с пустыми параметрами"""
        is_valid, errors = self.strategy.validate_params(self.category, None)
        self.assertFalse(is_valid)
        self.assertIn("Не предоставлены кастомные параметры", errors)
    
    def test_validation_passes_with_valid_params(self):
        """Валидация проходит с валидными параметрами"""
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0,
                'vat_rate': 20.0
            }
        }
        
        is_valid, errors = self.strategy.validate_params(self.category, custom_logistics)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_prepare_calculation_params_without_custom_logistics(self):
        """Подготовка без custom_logistics вызывает ошибку"""
        base_params = {'quantity': 100}
        
        with self.assertRaises(ValueError) as cm:
            self.strategy.prepare_calculation_params(
                self.category,
                base_params,
                None
            )
        
        self.assertIn("Кастомные параметры обязательны", str(cm.exception))
    
    def test_prepare_calculation_params_with_invalid_params(self):
        """Подготовка с невалидными параметрами вызывает ошибку"""
        base_params = {'quantity': 100}
        custom_logistics = {}  # Пустые параметры
        
        with self.assertRaises(ValueError) as cm:
            self.strategy.prepare_calculation_params(
                self.category,
                base_params,
                custom_logistics
            )
        
        # Может быть либо "Невалидные параметры", либо "Кастомные параметры обязательны"
        error_msg = str(cm.exception)
        self.assertTrue(
            "Невалидные параметры" in error_msg or "обязательны" in error_msg,
            f"Unexpected error message: {error_msg}"
        )
    
    def test_prepare_calculation_params_success(self):
        """Успешная подготовка параметров с custom_logistics"""
        base_params = {
            'quantity': 100,
            'weight_kg': 0.5,
            'unit_price_yuan': 50,
            'markup': 1.7
        }
        
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0,
                'vat_rate': 20.0
            }
        }
        
        calc_params = self.strategy.prepare_calculation_params(
            self.category,
            base_params,
            custom_logistics
        )
        
        # Должна быть категория
        self.assertIn('forced_category', calc_params)
        self.assertEqual(calc_params['forced_category'], 'Новая категория')
        
        # Должны быть custom_logistics
        self.assertIn('custom_logistics_params', calc_params)
        self.assertEqual(
            calc_params['custom_logistics_params']['highway_rail']['custom_rate'],
            8.5
        )
        
        # Базовые параметры сохранены
        self.assertEqual(calc_params['quantity'], 100)
    
    def test_strategy_name(self):
        """Проверка названия стратегии"""
        self.assertEqual(self.strategy.get_strategy_name(), "CustomCategory")


class TestStrategySelection(unittest.TestCase):
    """Tests for automatic strategy selection based on category"""
    
    def test_standard_category_uses_standard_strategy(self):
        """Стандартная категория должна использовать StandardStrategy"""
        category = Category(
            name="Стандартная",
            rail_base=5.0,
            air_base=7.1
        )
        
        # Определяем стратегию
        if category.needs_custom_params():
            strategy = CustomCategoryStrategy()
        else:
            strategy = StandardCategoryStrategy()
        
        self.assertIsInstance(strategy, StandardCategoryStrategy)
        self.assertFalse(strategy.requires_user_input(category))
    
    def test_custom_category_uses_custom_strategy(self):
        """Кастомная категория должна использовать CustomStrategy"""
        category = Category(
            name="Новая категория",
            rail_base=0,
            air_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        
        # Определяем стратегию
        if category.needs_custom_params():
            strategy = CustomCategoryStrategy()
        else:
            strategy = StandardCategoryStrategy()
        
        self.assertIsInstance(strategy, CustomCategoryStrategy)
        self.assertTrue(strategy.requires_user_input(category))


if __name__ == '__main__':
    unittest.main()

