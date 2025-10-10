"""
Unit tests for CalculationOrchestrator
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from models.calculation_state import CalculationState
from services.calculation_orchestrator import CalculationOrchestrator


class TestCalculationOrchestrator(unittest.TestCase):
    """Tests for CalculationOrchestrator"""
    
    @patch('services.calculation_orchestrator.PriceCalculator')
    def setUp(self, mock_price_calculator_class):
        """Создаём оркестратор с тестовыми категориями"""
        # Мокаем PriceCalculator
        self.mock_calculator = Mock()
        mock_price_calculator_class.return_value = self.mock_calculator
        
        self.categories = {
            'Футболки': {
                'category': 'Футболки',
                'rail_base': 5.0,
                'air_base': 7.1,
                'keywords': ['футболка', 'tshirt', 't-shirt']
            },
            'Новая категория': {
                'category': 'Новая категория',
                'rail_base': 0,
                'air_base': 0,
                'requirements': {
                    'requires_logistics_rate': True,
                    'requires_duty_rate': True,
                    'requires_vat_rate': True
                }
            }
        }
        
        self.orchestrator = CalculationOrchestrator(self.categories)
    
    def test_initial_state(self):
        """Начальное состояние оркестратора"""
        self.assertIsNone(self.orchestrator.context)
        self.assertEqual(len(self.orchestrator.categories), 2)
    
    def test_start_calculation_standard_category(self):
        """Начало расчёта для стандартной категории"""
        response = self.orchestrator.start_calculation(
            product_name="Футболка хлопок",
            quantity=100,
            weight_kg=0.2,
            unit_price_yuan=30,
            markup=1.7
        )
        
        # Проверяем ответ
        self.assertEqual(response['category'], 'Футболки')
        self.assertEqual(response['state'], 'Готов к расчёту')
        self.assertFalse(response['needs_user_input'])
        self.assertEqual(response['required_params'], [])
        
        # Проверяем контекст
        self.assertIsNotNone(self.orchestrator.context)
        self.assertEqual(
            self.orchestrator.context.get_current_state(),
            CalculationState.READY
        )
    
    def test_start_calculation_custom_category(self):
        """Начало расчёта для кастомной категории"""
        response = self.orchestrator.start_calculation(
            product_name="Неизвестный товар",
            quantity=50,
            weight_kg=1.0,
            unit_price_yuan=100,
            markup=1.5
        )
        
        # Проверяем ответ
        self.assertEqual(response['category'], 'Новая категория')
        self.assertEqual(response['state'], 'Ожидание параметров')
        self.assertTrue(response['needs_user_input'])
        self.assertGreater(len(response['required_params']), 0)
        
        # Проверяем контекст
        self.assertEqual(
            self.orchestrator.context.get_current_state(),
            CalculationState.PENDING_PARAMS
        )
    
    def test_start_calculation_forced_category(self):
        """Начало расчёта с принудительной категорией"""
        response = self.orchestrator.start_calculation(
            product_name="Что-то",
            quantity=10,
            weight_kg=0.5,
            unit_price_yuan=50,
            markup=1.7,
            forced_category="Футболки"
        )
        
        # Должна использоваться принудительная категория
        self.assertEqual(response['category'], 'Футболки')
    
    def test_provide_custom_params_without_init(self):
        """Предоставление параметров без инициализации контекста"""
        with self.assertRaises(ValueError) as cm:
            self.orchestrator.provide_custom_params({})
        
        self.assertIn("не инициализирован", str(cm.exception))
    
    def test_provide_custom_params_invalid(self):
        """Предоставление невалидных кастомных параметров"""
        # Инициализируем с кастомной категорией
        self.orchestrator.start_calculation(
            product_name="Неизвестный товар",
            quantity=50,
            weight_kg=1.0,
            unit_price_yuan=100,
            markup=1.5
        )
        
        # Предоставляем невалидные параметры
        result = self.orchestrator.provide_custom_params({})
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertFalse(result['can_calculate'])
    
    def test_provide_custom_params_valid(self):
        """Предоставление валидных кастомных параметров"""
        # Инициализируем с кастомной категорией
        self.orchestrator.start_calculation(
            product_name="Неизвестный товар",
            quantity=50,
            weight_kg=1.0,
            unit_price_yuan=100,
            markup=1.5
        )
        
        # Предоставляем валидные параметры
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0,
                'vat_rate': 20.0
            }
        }
        
        result = self.orchestrator.provide_custom_params(custom_logistics)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], [])
        self.assertTrue(result['can_calculate'])
        self.assertEqual(result['state'], 'Готов к расчёту')
    
    def test_calculate_without_init(self):
        """Расчёт без инициализации контекста"""
        with self.assertRaises(ValueError) as cm:
            self.orchestrator.calculate()
        
        self.assertIn("не инициализирован", str(cm.exception))
    
    def test_calculate_not_ready(self):
        """Расчёт когда не готов"""
        # Инициализируем с кастомной категорией (PENDING_PARAMS)
        self.orchestrator.start_calculation(
            product_name="Неизвестный товар",
            quantity=50,
            weight_kg=1.0,
            unit_price_yuan=100,
            markup=1.5
        )
        
        # Пытаемся рассчитать без параметров
        result = self.orchestrator.calculate()
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Невозможно выполнить расчёт', result['error'])
    
    def test_calculate_success_standard(self):
        """Успешный расчёт для стандартной категории"""
        # Мокаем результат расчёта
        mock_result = {
            'cost_price': {
                'total': {
                    'rub': 50000,
                    'usd': 500
                }
            }
        }
        self.orchestrator.calculator.calculate_routes.return_value = mock_result
        
        # Инициализируем со стандартной категорией
        self.orchestrator.start_calculation(
            product_name="Футболка",
            quantity=100,
            weight_kg=0.2,
            unit_price_yuan=30,
            markup=1.7
        )
        
        # Выполняем расчёт
        result = self.orchestrator.calculate()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], mock_result)
        self.assertEqual(result['state'], 'Рассчитан')
        
        # Проверяем что calculate_routes был вызван
        self.orchestrator.calculator.calculate_routes.assert_called_once()
    
    def test_calculate_success_custom(self):
        """Успешный расчёт для кастомной категории"""
        # Мокаем результат расчёта
        mock_result = {'cost_price': {'total': {'rub': 60000}}}
        self.orchestrator.calculator.calculate_routes.return_value = mock_result
        
        # Инициализируем с кастомной категорией
        self.orchestrator.start_calculation(
            product_name="Неизвестный товар",
            quantity=50,
            weight_kg=1.0,
            unit_price_yuan=100,
            markup=1.5
        )
        
        # Предоставляем параметры
        custom_logistics = {
            'highway_rail': {
                'custom_rate': 8.5,
                'duty_rate': 10.0,
                'vat_rate': 20.0
            }
        }
        self.orchestrator.provide_custom_params(custom_logistics)
        
        # Выполняем расчёт
        result = self.orchestrator.calculate()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], mock_result)
    
    def test_calculate_error(self):
        """Расчёт с ошибкой"""
        # Мокаем ошибку
        self.orchestrator.calculator.calculate_routes.side_effect = Exception("Test calculation error")
        
        # Инициализируем со стандартной категорией
        self.orchestrator.start_calculation(
            product_name="Футболка",
            quantity=100,
            weight_kg=0.2,
            unit_price_yuan=30,
            markup=1.7
        )
        
        # Выполняем расчёт
        result = self.orchestrator.calculate()
        
        self.assertFalse(result['success'])
        self.assertIn('Test calculation error', result['error'])
        
        # Контекст должен перейти в ERROR
        self.assertEqual(
            self.orchestrator.context.get_current_state(),
            CalculationState.ERROR
        )
    
    def test_get_context_info_without_init(self):
        """Получение инфо о контексте без инициализации"""
        with self.assertRaises(ValueError):
            self.orchestrator.get_context_info()
    
    def test_get_context_info(self):
        """Получение информации о контексте"""
        self.orchestrator.start_calculation(
            product_name="Футболка",
            quantity=100,
            weight_kg=0.2,
            unit_price_yuan=30,
            markup=1.7
        )
        
        info = self.orchestrator.get_context_info()
        
        self.assertIn('category', info)
        self.assertIn('state', info)
        self.assertIn('strategy', info)
        self.assertEqual(info['category']['category'], 'Футболки')
    
    def test_mark_saved_without_init(self):
        """Пометка как сохранённого без инициализации"""
        with self.assertRaises(ValueError):
            self.orchestrator.mark_saved(123)
    
    def test_mark_saved(self):
        """Пометка расчёта как сохранённого"""
        self.orchestrator.calculator.calculate_routes.return_value = {'cost_price': {'total': {'rub': 50000}}}
        
        # Выполняем расчёт
        self.orchestrator.start_calculation(
            product_name="Футболка",
            quantity=100,
            weight_kg=0.2,
            unit_price_yuan=30,
            markup=1.7
        )
        self.orchestrator.calculate()
        
        # Помечаем как сохранённый
        self.orchestrator.mark_saved(456)
        
        self.assertEqual(
            self.orchestrator.context.get_current_state(),
            CalculationState.SAVED
        )
    
    def test_reset(self):
        """Сброс оркестратора"""
        self.orchestrator.start_calculation(
            product_name="Футболка",
            quantity=100,
            weight_kg=0.2,
            unit_price_yuan=30,
            markup=1.7
        )
        
        self.assertIsNotNone(self.orchestrator.context)
        
        self.orchestrator.reset()
        
        self.assertIsNone(self.orchestrator.context)
    
    def test_category_detection(self):
        """Определение категории по ключевым словам"""
        # Должна найти "Футболки"
        result = self.orchestrator._detect_category("Красная футболка")
        self.assertEqual(result, 'Футболки')
        
        # Должна вернуть "Новая категория"
        result = self.orchestrator._detect_category("Совершенно неизвестный товар")
        self.assertEqual(result, 'Новая категория')


if __name__ == '__main__':
    unittest.main()

