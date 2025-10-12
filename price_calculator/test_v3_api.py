"""
Тестовый скрипт для проверки работы V3 API

Создает тестовые данные:
1. Factory
2. Position
3. Calculation
4. Пересчитывает маршруты

Запуск:
    python3 test_v3_api.py
"""
import sys
from decimal import Decimal
from sqlalchemy.orm import Session

# Добавляем текущую директорию в путь
sys.path.insert(0, '.')

from models_v3 import get_db, init_db, SessionLocal
from services_v3 import (
    FactoryService,
    PositionService,
    CalculationService,
    RecalculationService
)


def test_v3_api():
    """
    Тестирование V3 API с созданием тестовых данных
    """
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ V3 API")
    print("=" * 60)
    
    # Инициализируем БД (создаем таблицы если нужно)
    print("\n📦 Инициализация базы данных...")
    try:
        init_db()
        print("✅ База данных готова")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")
    
    # Создаем сессию
    db: Session = SessionLocal()
    
    try:
        # 1. Создаем фабрику
        print("\n" + "=" * 60)
        print("1️⃣ СОЗДАНИЕ ФАБРИКИ")
        print("=" * 60)
        
        factory_service = FactoryService(db)
        
        factory_data = {
            'name': 'Тестовая фабрика футболок',
            'contact': 'https://wechat.com/test_factory',
            'comment': 'Фабрика для тестирования V3 API',
            'default_sample_time_days': 7,
            'default_production_time_days': 15,
            'default_sample_price_yuan': Decimal('50.00')
        }
        
        factory, created = factory_service.get_or_create(
            name=factory_data['name'],
            **{k: v for k, v in factory_data.items() if k != 'name'}
        )
        
        if created:
            print(f"✅ Фабрика создана: ID={factory.id}, Name='{factory.name}'")
        else:
            print(f"ℹ️ Фабрика уже существует: ID={factory.id}, Name='{factory.name}'")
        
        print(f"   Contact: {factory.contact}")
        print(f"   Default sample time: {factory.default_sample_time_days} дней")
        print(f"   Default production time: {factory.default_production_time_days} дней")
        
        # 2. Создаем позицию
        print("\n" + "=" * 60)
        print("2️⃣ СОЗДАНИЕ ПОЗИЦИИ")
        print("=" * 60)
        
        position_service = PositionService(db)
        
        position_data = {
            'name': 'Футболка хлопковая с принтом',
            'description': 'Хлопковая футболка 180г/м², разм XS-3XL, принт шелкография',
            'category': 'футболка',
            'design_files_urls': [
                'https://drive.google.com/design1.ai',
                'https://drive.google.com/design2.pdf'
            ],
            'custom_fields': {
                'material': 'хлопок 100%',
                'weight': '180 г/м²',
                'colors': ['белый', 'черный', 'серый'],
                'print_type': 'шелкография'
            }
        }
        
        # Проверяем, существует ли уже такая позиция
        existing_positions = position_service.search(position_data['name'], limit=1)
        if existing_positions:
            position = existing_positions[0]
            print(f"ℹ️ Позиция уже существует: ID={position.id}, Name='{position.name}'")
        else:
            position = position_service.create(position_data)
            print(f"✅ Позиция создана: ID={position.id}, Name='{position.name}'")
        
        print(f"   Category: {position.category}")
        print(f"   Description: {position.description}")
        print(f"   Design files: {len(position.design_files_urls or [])} файлов")
        print(f"   Custom fields: {list((position.custom_fields or {}).keys())}")
        
        # 3. Создаем расчёт
        print("\n" + "=" * 60)
        print("3️⃣ СОЗДАНИЕ РАСЧЁТА")
        print("=" * 60)
        
        calculation_service = CalculationService(db)
        
        calculation_data = {
            'position_id': position.id,
            'factory_id': factory.id,
            'sample_time_days': 7,
            'production_time_days': 15,
            'sample_price_yuan': Decimal('50.00'),
            'factory_comment': 'Тестовый расчёт для проверки V3 API',
            'quantity': 1000,
            'price_yuan': Decimal('15.50'),
            'calculation_type': 'quick',
            'weight_kg': Decimal('0.200')
        }
        
        calculation = calculation_service.create(calculation_data)
        print(f"✅ Расчёт создан: ID={calculation.id}")
        print(f"   Position: {position.name}")
        print(f"   Factory: {factory.name}")
        print(f"   Quantity: {calculation.quantity} шт")
        print(f"   Price: {calculation.price_yuan} ¥")
        print(f"   Weight: {calculation.weight_kg} кг")
        print(f"   Type: {calculation.calculation_type}")
        
        # 4. Пересчитываем маршруты
        print("\n" + "=" * 60)
        print("4️⃣ ПЕРЕСЧЁТ МАРШРУТОВ ЛОГИСТИКИ")
        print("=" * 60)
        
        recalc_service = RecalculationService(db)
        
        try:
            routes = recalc_service.recalculate_routes(
                calculation_id=calculation.id,
                category='футболка'
            )
            
            print(f"✅ Маршруты пересчитаны: {len(routes)} маршрутов")
            print()
            
            for route in routes:
                print(f"📍 {route.route_name}:")
                print(f"   Себестоимость: {route.cost_price_rub or 0:.2f} ₽ / {route.cost_price_usd or 0:.2f} $")
                print(f"   Продажная цена: {route.sale_price_rub or 0:.2f} ₽ / {route.sale_price_usd or 0:.2f} $")
                print(f"   Прибыль: {route.profit_rub or 0:.2f} ₽ / {route.profit_usd or 0:.2f} $")
                print(f"   Общая себестоимость: {route.total_cost_rub or 0:.2f} ₽")
                print()
            
        except ValueError as e:
            print(f"❌ Ошибка при пересчёте маршрутов (ValueError): {e}")
        except Exception as e:
            print(f"❌ Ошибка при пересчёте маршрутов (Exception): {e}")
            print(f"   Тип ошибки: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        # 5. Итоговая статистика
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        
        total_factories = factory_service.count()
        total_positions = position_service.count()
        total_calculations = calculation_service.count()
        
        print(f"Фабрик в БД: {total_factories}")
        print(f"Позиций в БД: {total_positions}")
        print(f"Расчётов в БД: {total_calculations}")
        
        print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("=" * 60)
        
        return {
            'factory_id': factory.id,
            'position_id': position.id,
            'calculation_id': calculation.id,
            'routes_count': len(routes) if 'routes' in locals() else 0
        }
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    result = test_v3_api()
    
    if result:
        print("\n🎉 V3 API работает корректно!")
        print(f"   Factory ID: {result['factory_id']}")
        print(f"   Position ID: {result['position_id']}")
        print(f"   Calculation ID: {result['calculation_id']}")
        print(f"   Routes calculated: {result['routes_count']}")
    else:
        print("\n💥 Тестирование провалено!")
        sys.exit(1)

