"""
Unit tests for Calculation State Machine
"""

import unittest
from models.calculation_state import CalculationState, CalculationStateMachine, StateTransitionError


class TestCalculationState(unittest.TestCase):
    """Tests for CalculationState enum"""
    
    def test_state_values(self):
        """Проверка значений состояний"""
        self.assertEqual(CalculationState.DRAFT.value, "draft")
        self.assertEqual(CalculationState.PENDING_PARAMS.value, "pending_params")
        self.assertEqual(CalculationState.READY.value, "ready")
        self.assertEqual(CalculationState.CALCULATED.value, "calculated")
        self.assertEqual(CalculationState.SAVED.value, "saved")
        self.assertEqual(CalculationState.ERROR.value, "error")


class TestCalculationStateMachine(unittest.TestCase):
    """Tests for CalculationStateMachine"""
    
    def setUp(self):
        """Создаём новый state machine перед каждым тестом"""
        self.machine = CalculationStateMachine()
    
    def test_initial_state(self):
        """Начальное состояние должно быть DRAFT"""
        self.assertEqual(self.machine.state, CalculationState.DRAFT)
        self.assertEqual(len(self.machine.history), 1)
    
    def test_valid_transition_draft_to_ready(self):
        """Валидный переход DRAFT → READY"""
        self.assertTrue(self.machine.can_transition_to(CalculationState.READY))
        success = self.machine.transition_to(CalculationState.READY)
        
        self.assertTrue(success)
        self.assertEqual(self.machine.state, CalculationState.READY)
        self.assertEqual(len(self.machine.history), 2)
    
    def test_valid_transition_draft_to_pending_params(self):
        """Валидный переход DRAFT → PENDING_PARAMS"""
        self.assertTrue(self.machine.can_transition_to(CalculationState.PENDING_PARAMS))
        success = self.machine.transition_to(CalculationState.PENDING_PARAMS)
        
        self.assertTrue(success)
        self.assertEqual(self.machine.state, CalculationState.PENDING_PARAMS)
    
    def test_invalid_transition(self):
        """Невалидный переход должен вызывать исключение"""
        # DRAFT → CALCULATED напрямую невозможен
        self.assertFalse(self.machine.can_transition_to(CalculationState.CALCULATED))
        
        with self.assertRaises(StateTransitionError):
            self.machine.transition_to(CalculationState.CALCULATED)
    
    def test_full_happy_path(self):
        """Полный успешный путь: DRAFT → READY → CALCULATED → SAVED"""
        # DRAFT → READY
        self.machine.transition_to(CalculationState.READY)
        self.assertEqual(self.machine.state, CalculationState.READY)
        
        # READY → CALCULATED
        self.machine.transition_to(CalculationState.CALCULATED)
        self.assertEqual(self.machine.state, CalculationState.CALCULATED)
        
        # CALCULATED → SAVED
        self.machine.transition_to(CalculationState.SAVED)
        self.assertEqual(self.machine.state, CalculationState.SAVED)
        
        # История должна содержать 4 записи (initial + 3 перехода)
        self.assertEqual(len(self.machine.history), 4)
    
    def test_custom_params_path(self):
        """Путь с кастомными параметрами: DRAFT → PENDING_PARAMS → READY → CALCULATED"""
        # DRAFT → PENDING_PARAMS
        self.machine.transition_to(CalculationState.PENDING_PARAMS)
        self.assertEqual(self.machine.state, CalculationState.PENDING_PARAMS)
        
        # PENDING_PARAMS → READY
        self.machine.transition_to(CalculationState.READY)
        self.assertEqual(self.machine.state, CalculationState.READY)
        
        # READY → CALCULATED
        self.machine.transition_to(CalculationState.CALCULATED)
        self.assertEqual(self.machine.state, CalculationState.CALCULATED)
    
    def test_edit_after_save(self):
        """Редактирование после сохранения: SAVED → DRAFT"""
        # Доводим до SAVED
        self.machine.transition_to(CalculationState.READY)
        self.machine.transition_to(CalculationState.CALCULATED)
        self.machine.transition_to(CalculationState.SAVED)
        
        # SAVED → DRAFT для редактирования
        self.assertTrue(self.machine.can_transition_to(CalculationState.DRAFT))
        self.machine.transition_to(CalculationState.DRAFT)
        self.assertEqual(self.machine.state, CalculationState.DRAFT)
    
    def test_context_in_transitions(self):
        """Передача контекста при переходах"""
        context = {'category': 'Новая категория'}
        self.machine.transition_to(CalculationState.PENDING_PARAMS, context=context)
        
        last_transition = self.machine.get_last_transition()
        self.assertIsNotNone(last_transition)
        self.assertEqual(last_transition['context']['category'], 'Новая категория')
    
    def test_get_allowed_transitions(self):
        """Получение списка разрешённых переходов"""
        allowed = self.machine.get_allowed_transitions()
        
        self.assertIn(CalculationState.PENDING_PARAMS, allowed)
        self.assertIn(CalculationState.READY, allowed)
        self.assertNotIn(CalculationState.SAVED, allowed)
    
    def test_state_name(self):
        """Получение человекочитаемого названия состояния"""
        self.assertEqual(self.machine.get_state_name(), "Черновик")
        
        self.machine.transition_to(CalculationState.READY)
        self.assertEqual(self.machine.get_state_name(), "Готов к расчёту")
    
    def test_reset(self):
        """Сброс state machine"""
        # Делаем несколько переходов
        self.machine.transition_to(CalculationState.READY)
        self.machine.transition_to(CalculationState.CALCULATED)
        
        # Сбрасываем
        self.machine.reset()
        
        self.assertEqual(self.machine.state, CalculationState.DRAFT)
        self.assertEqual(len(self.machine.history), 1)
    
    def test_serialization(self):
        """Сериализация и десериализация"""
        # Делаем переходы
        self.machine.transition_to(CalculationState.PENDING_PARAMS, 
                                   context={'category': 'Test'})
        self.machine.transition_to(CalculationState.READY)
        
        # Сериализуем
        data = self.machine.to_dict()
        
        self.assertEqual(data['current_state'], 'ready')
        self.assertIn('history', data)
        self.assertGreater(len(data['history']), 0)
        
        # Десериализуем
        restored = CalculationStateMachine.from_dict(data)
        
        self.assertEqual(restored.state, CalculationState.READY)
        self.assertEqual(len(restored.history), len(self.machine.history))
    
    def test_error_state(self):
        """Переход в состояние ERROR"""
        error_context = {'error': 'Test error message'}
        
        # Из любого состояния можем перейти в ERROR
        self.assertTrue(self.machine.can_transition_to(CalculationState.ERROR))
        self.machine.transition_to(CalculationState.ERROR, context=error_context)
        
        self.assertEqual(self.machine.state, CalculationState.ERROR)
        
        # Из ERROR можем вернуться в DRAFT
        self.assertTrue(self.machine.can_transition_to(CalculationState.DRAFT))
        self.machine.transition_to(CalculationState.DRAFT)
        self.assertEqual(self.machine.state, CalculationState.DRAFT)
    
    def test_hook_registration(self):
        """Регистрация и вызов хуков"""
        hook_called = []
        
        def on_ready_hook(machine, context):
            hook_called.append('ready')
        
        # Регистрируем хук
        self.machine.register_hook('on_enter', CalculationState.READY, on_ready_hook)
        
        # Переходим в READY
        self.machine.transition_to(CalculationState.READY)
        
        # Хук должен был вызваться
        self.assertIn('ready', hook_called)


if __name__ == '__main__':
    unittest.main()



