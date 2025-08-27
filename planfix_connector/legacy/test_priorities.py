#!/usr/bin/env python3
"""
Тест правильности расчета приоритетов
"""

def calculate_priority(client_grade, order_percent, calculation_sum):
    """Правильный расчет приоритета по формуле"""
    try:
        client_grade = float(client_grade) if client_grade and client_grade != '' else 3.0
        client_grade = max(1, min(5, client_grade))
        
        order_percent = float(order_percent) if order_percent and order_percent != '' else 50.0
        order_percent = max(0, min(100, order_percent))
        
        calculation_sum = float(calculation_sum) if calculation_sum and calculation_sum != '' else 1000000
        
        # Фактор суммы просчета
        if calculation_sum <= 250000:
            sum_factor = 0.2
        elif calculation_sum <= 1000000:
            sum_factor = 0.4
        elif calculation_sum <= 5000000:
            sum_factor = 0.6
        elif calculation_sum <= 10000000:
            sum_factor = 0.8
        else:
            sum_factor = 1.0
        
        # Расчет приоритета
        priority_score = (
            0.4 * (client_grade / 5) +
            0.4 * sum_factor +
            0.2 * (order_percent / 100)
        )
        
        # Классификация
        if priority_score >= 0.8:
            return "A", priority_score
        elif priority_score >= 0.6:
            return "B", priority_score
        elif priority_score >= 0.4:
            return "C", priority_score
        else:
            return "D", priority_score
            
    except Exception as e:
        return "D", 0.0

def test_priorities():
    """Тестирование различных комбинаций"""
    print("🧪 Тест расчета приоритетов")
    print("=" * 60)
    
    test_cases = [
        # (Грейд, % заказа, Сумма, Ожидаемый приоритет)
        (5, 100, 20000000, "A"),  # Максимальные значения
        (4, 80, 8000000, "A"),    # Высокие значения
        (3, 60, 3000000, "B"),    # Средние значения
        (2, 40, 500000, "C"),     # Низкие значения
        (1, 20, 100000, "D"),     # Минимальные значения
        (5, 50, 1000000, "B"),    # Высокий грейд, средние остальные
        (1, 100, 20000000, "A"),  # Низкий грейд, но высокие остальные
        (5, 20, 100000, "C"),     # Высокий грейд, но низкие остальные
    ]
    
    results = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    
    for i, (grade, percent, sum_val, expected) in enumerate(test_cases, 1):
        priority, score = calculate_priority(grade, percent, sum_val)
        results[priority] += 1
        
        status = "✅" if priority == expected else "❌"
        print(f"{status} Тест {i}: Грейд={grade}, %={percent}, Сумма={sum_val:,}₽")
        print(f"   Результат: {priority} (счет: {score:.3f}), Ожидалось: {expected}")
        print()
    
    print("📊 Итоговая статистика:")
    for priority, count in results.items():
        print(f"   {priority}: {count}")
    
    print("\n🎯 Проверьте дашборд: http://localhost:8055")
    print("   Должно быть правильное распределение A/B/C/D, а не все C!")

if __name__ == "__main__":
    test_priorities()
