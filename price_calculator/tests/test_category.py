"""
Unit tests for Category models
"""

import unittest
from models.category import Category, CategoryRequirements


class TestCategoryRequirements(unittest.TestCase):
    """Tests for CategoryRequirements"""
    
    def test_no_requirements_is_complete(self):
        """Категория без требований всегда заполнена"""
        req = CategoryRequirements()
        self.assertTrue(req.is_complete({}))
        self.assertEqual(req.get_missing_params({}), [])
    
    def test_requires_logistics_rate(self):
        """Проверка требования логистической ставки"""
        req = CategoryRequirements(requires_logistics_rate=True)
        
        # Не заполнено
        self.assertFalse(req.is_complete({}))
        self.assertIn('custom_rate', req.get_missing_params({}))
        
        # Заполнено
        params = {'highway_rail': {'custom_rate': 5.0}}
        self.assertTrue(req.is_complete(params))
        self.assertEqual(req.get_missing_params(params), [])
    
    def test_multiple_requirements(self):
        """Проверка множественных требований"""
        req = CategoryRequirements(
            requires_logistics_rate=True,
            requires_duty_rate=True
        )
        
        # Ничего не заполнено
        self.assertFalse(req.is_complete({}))
        missing = req.get_missing_params({})
        self.assertIn('custom_rate', missing)
        self.assertIn('duty_rate', missing)
        
        # Частично заполнено
        params = {'highway_rail': {'custom_rate': 5.0}}
        self.assertFalse(req.is_complete(params))
        
        # Полностью заполнено
        params = {'highway_rail': {'custom_rate': 5.0, 'duty_rate': 10.0}}
        self.assertTrue(req.is_complete(params))


class TestCategory(unittest.TestCase):
    """Tests for Category"""
    
    def test_standard_category_no_custom_params(self):
        """Стандартная категория не требует кастомных параметров"""
        cat = Category(
            name="Футболки",
            material="хлопок",
            rail_base=5.0,
            air_base=7.1
        )
        
        self.assertFalse(cat.needs_custom_params())
        is_valid, errors = cat.validate_params({})
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_new_category_needs_params(self):
        """Новая категория требует параметров"""
        cat = Category(
            name="Новая категория",
            rail_base=0,
            air_base=0,
            requirements=CategoryRequirements(requires_logistics_rate=True)
        )
        
        self.assertTrue(cat.needs_custom_params())
        is_valid, errors = cat.validate_params({})
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_from_dict_standard_category(self):
        """Создание Category из словаря"""
        data = {
            'category': 'Футболки',
            'material': 'хлопок',
            'rates': {
                'rail_base': 5.0,
                'air_base': 7.1
            },
            'duty_rate': '10%',
            'vat_rate': '20%'
        }
        
        cat = Category.from_dict(data)
        
        self.assertEqual(cat.name, 'Футболки')
        self.assertEqual(cat.material, 'хлопок')
        self.assertEqual(cat.rail_base, 5.0)
        self.assertEqual(cat.air_base, 7.1)
        self.assertEqual(cat.duty_rate, 10.0)
        self.assertEqual(cat.vat_rate, 20.0)
    
    def test_from_dict_new_category(self):
        """Создание 'Новая категория' автоматически устанавливает requires_logistics_rate"""
        data = {
            'category': 'Новая категория',
            'material': '',
            'rates': {
                'rail_base': 0,
                'air_base': 0
            }
        }
        
        cat = Category.from_dict(data)
        
        self.assertEqual(cat.name, 'Новая категория')
        self.assertTrue(cat.needs_custom_params())
        self.assertTrue(cat.requirements.requires_logistics_rate)
    
    def test_to_dict_serialization(self):
        """Сериализация Category в словарь"""
        cat = Category(
            name="Тестовая категория",
            material="материал",
            rail_base=5.0,
            air_base=7.1
        )
        
        data = cat.to_dict()
        
        self.assertEqual(data['category'], 'Тестовая категория')
        self.assertEqual(data['material'], 'материал')
        self.assertEqual(data['rates']['rail_base'], 5.0)
        self.assertEqual(data['rates']['air_base'], 7.1)
        self.assertIn('needs_custom_params', data)
    
    def test_get_required_params_names(self):
        """Получение списка требуемых параметров"""
        cat = Category(
            name="Новая категория",
            rail_base=0,
            air_base=0,
            requirements=CategoryRequirements(
                requires_logistics_rate=True,
                requires_duty_rate=True
            )
        )
        
        params = cat.get_required_params_names()
        
        self.assertGreater(len(params), 0)
        # Должны быть упоминания о ставках
        params_str = ' '.join(params)
        self.assertTrue('custom_rate' in params_str or 'rail_rate' in params_str or 'ставка' in params_str)


if __name__ == '__main__':
    unittest.main()

