"""
Unit tests for CalculationContext
"""

import unittest
from models.category import Category, CategoryRequirements
from models.calculation_state import CalculationState
from services.calculation_context import CalculationContext
from strategies import StandardCategoryStrategy, CustomCategoryStrategy


class TestCalculationContext(unittest.TestCase):
    """Tests for CalculationContext"""
    
    def test_initial_state(self):
        """Начальное состояние контекста"""
        context = CalculationContext()
        
        self.assertIsNone(context.category)
        self.assertIsNone(context.strategy)
        self.assertEqual(context.state_machine.state, CalculationState.DRAFT)
        self.assertEqual(context.base_params, {})
        self.assertEqual(context.custom_logistics, {})
    
    def test_set_standard_category(self):
        """Установка стандартной категории"""
        context = CalculationContext()
        
        category = Category(
            name="Футболки",
            rail_base=5.0,
            air_base=7.1
        )
        
        base_params = {
            'quantity': 100,
            'weight_kg': 0.5,
            'unit_price_yuan': 50,
            'markup': 1.7
        }
        
        context.set_category(category, base_params)
        
        # Проверяем категорию
        self.assertEqual(context.category.name, "Футболки")
        
        # Проверяем стратегию
        self.assertIsInstance(context.strategy, StandardCategoryStrategy)
        
        # Проверяем состояние (должно быть READY)
        self.assertEqual(context.state_machine.state, CalculationState.READY)
        
        # Проверяем параметры
        self.assertEqual(context.base_params['quantity'], 100)
    
    def test_set_custom_category(self):
        """Установка кастомной категории"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            air_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        
        base_params = {'quantity': 100}
        
        context.set_category(category, base_params)
        
        # Проверяем стратегию
        self.assertIsInstance(context.strategy, CustomCategoryStrategy)
        
        # Проверяем состояние (должно быть PENDING_PARAMS)
        self.assertEqual(context.state_machine.state, CalculationState.PENDING_PARAMS)
    
    def test_needs_user_input_standard(self):
        """Стандартная категория не требует ввода"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        context.set_category(category, {'quantity': 100})
        
        self.assertFalse(context.needs_user_input())
    
    def test_needs_user_input_custom(self):
        """Кастомная категория требует ввода"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        context.set_category(category, {'quantity': 100})
        
        self.assertTrue(context.needs_user_input())
    
    def test_get_required_params(self):
        """Получение списка требуемых параметров"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        context.set_category(category, {'quantity': 100})
        
        params = context.get_required_params()
        self.assertGreater(len(params), 0)
    
    def test_provide_custom_logistics_invalid(self):
        """Предоставление невалидных кастомных параметров"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        context.set_category(category, {'quantity': 100})
        
        # Пустые параметры
        is_valid, errors = context.provide_custom_logistics({})
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Состояние не должно измениться
        self.assertEqual(context.state_machine.state, CalculationState.PENDING_PARAMS)
    
    def test_provide_custom_logistics_valid(self):
        """Предоставление валидных кастомных параметров"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        context.set_category(category, {'quantity': 100})
        
        # Валидные параметры
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0,
                'vat_rate': 20.0
            }
        }
        
        is_valid, errors = context.provide_custom_logistics(custom_logistics)
        
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        # Состояние должно перейти в READY
        self.assertEqual(context.state_machine.state, CalculationState.READY)
        
        # Параметры должны сохраниться
        self.assertEqual(context.custom_logistics['highway_rail']['custom_rate'], 8.5)
    
    def test_can_calculate_not_ready(self):
        """Проверка возможности расчёта - неготов"""
        context = CalculationContext()
        
        can_calc, reason = context.can_calculate()
        
        self.assertFalse(can_calc)
        self.assertIn("состояние", reason.lower())
    
    def test_can_calculate_standard_ready(self):
        """Проверка возможности расчёта - стандартная категория готова"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        base_params = {
            'quantity': 100,
            'weight_kg': 0.5,
            'unit_price_yuan': 50,
            'markup': 1.7
        }
        
        context.set_category(category, base_params)
        
        can_calc, reason = context.can_calculate()
        
        self.assertTrue(can_calc)
        self.assertEqual(reason, "OK")
    
    def test_can_calculate_custom_without_params(self):
        """Проверка возможности расчёта - кастомная категория без параметров"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        context.set_category(category, {'quantity': 100})
        
        can_calc, reason = context.can_calculate()
        
        self.assertFalse(can_calc)
        self.assertIn("состояние", reason.lower())  # Состояние PENDING_PARAMS
    
    def test_can_calculate_custom_with_params(self):
        """Проверка возможности расчёта - кастомная категория с параметрами"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        context.set_category(category, {'quantity': 100})
        
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0,
                'vat_rate': 20.0
            }
        }
        context.provide_custom_logistics(custom_logistics)
        
        can_calc, reason = context.can_calculate()
        
        self.assertTrue(can_calc)
        self.assertEqual(reason, "OK")
    
    def test_prepare_calculation_params_standard(self):
        """Подготовка параметров для стандартной категории"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        base_params = {
            'quantity': 100,
            'weight_kg': 0.5,
            'unit_price_yuan': 50,
            'markup': 1.7
        }
        
        context.set_category(category, base_params)
        
        calc_params = context.prepare_calculation_params()
        
        # Проверяем наличие forced_category
        self.assertIn('forced_category', calc_params)
        self.assertEqual(calc_params['forced_category'], 'Футболки')
        
        # Проверяем базовые параметры
        self.assertEqual(calc_params['quantity'], 100)
        
        # custom_logistics_params не должно быть
        self.assertNotIn('custom_logistics_params', calc_params)
    
    def test_prepare_calculation_params_custom(self):
        """Подготовка параметров для кастомной категории"""
        context = CalculationContext()
        
        category = Category(
            name="Новая категория",
            rail_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        base_params = {'quantity': 100}
        
        context.set_category(category, base_params)
        
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0
            }
        }
        context.provide_custom_logistics(custom_logistics)
        
        calc_params = context.prepare_calculation_params()
        
        # Проверяем наличие forced_category
        self.assertIn('forced_category', calc_params)
        
        # Проверяем custom_logistics_params
        self.assertIn('custom_logistics_params', calc_params)
        self.assertEqual(
            calc_params['custom_logistics_params']['highway_rail']['custom_rate'],
            8.5
        )
    
    def test_prepare_calculation_params_not_ready(self):
        """Подготовка параметров когда не готов - ошибка"""
        context = CalculationContext()
        
        with self.assertRaises(ValueError) as cm:
            context.prepare_calculation_params()
        
        self.assertIn("Невозможно подготовить параметры", str(cm.exception))
    
    def test_mark_calculated(self):
        """Пометка расчёта как выполненного"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        context.set_category(category, {'quantity': 100})
        
        result = {
            'cost_price': {
                'total': {
                    'rub': 50000,
                    'usd': 500
                }
            }
        }
        
        context.mark_calculated(result)
        
        self.assertEqual(context.state_machine.state, CalculationState.CALCULATED)
        self.assertIsNotNone(context.result)
        self.assertEqual(context.result['cost_price']['total']['rub'], 50000)
    
    def test_mark_saved(self):
        """Пометка расчёта как сохранённого"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        context.set_category(category, {'quantity': 100})
        
        result = {'cost_price': {'total': {'rub': 50000}}}
        context.mark_calculated(result)
        
        context.mark_saved(123)
        
        self.assertEqual(context.state_machine.state, CalculationState.SAVED)
    
    def test_mark_error(self):
        """Пометка расчёта как завершившегося с ошибкой"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        context.set_category(category, {'quantity': 100})
        
        context.mark_error("Test error")
        
        self.assertEqual(context.state_machine.state, CalculationState.ERROR)
    
    def test_reset(self):
        """Сброс контекста"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        context.set_category(category, {'quantity': 100})
        
        context.reset()
        
        self.assertIsNone(context.category)
        self.assertIsNone(context.strategy)
        self.assertEqual(context.base_params, {})
        self.assertEqual(context.custom_logistics, {})
        self.assertIsNone(context.result)
        self.assertEqual(context.state_machine.state, CalculationState.DRAFT)
    
    def test_to_dict(self):
        """Сериализация контекста"""
        context = CalculationContext()
        
        category = Category(name="Футболки", rail_base=5.0, air_base=7.1)
        context.set_category(category, {'quantity': 100})
        
        context_dict = context.to_dict()
        
        # Проверяем наличие всех ключей
        self.assertIn('category', context_dict)
        self.assertIn('state', context_dict)
        self.assertIn('strategy', context_dict)
        self.assertIn('needs_user_input', context_dict)
        self.assertIn('can_calculate', context_dict)
        
        # Проверяем значения
        self.assertEqual(context_dict['category']['category'], 'Футболки')  # Поле называется 'category', а не 'name'
        self.assertEqual(context_dict['strategy'], 'StandardCategory')
        self.assertFalse(context_dict['needs_user_input'])
        self.assertTrue(context_dict['can_calculate'])


if __name__ == '__main__':
    unittest.main()

