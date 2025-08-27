#!/usr/bin/env python3
"""
Скрипт для обновления данных из Planfix API
"""

from final_dashboard import FinalDashboard

def main():
    print("🔄 Обновление данных из Planfix...")
    
    dashboard = FinalDashboard()
    
    try:
        result = dashboard.fetch_fresh_data()
        print("✅ Данные успешно обновлены!")
        print(f"Результат: {result}")
    except Exception as e:
        print(f"❌ Ошибка при обновлении данных: {e}")

if __name__ == "__main__":
    main()
