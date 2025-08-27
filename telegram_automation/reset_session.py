#!/usr/bin/env python3
"""
Reset Telegram Session
Сброс сессии и повторная настройка
"""

import os
import json

def reset_session():
    """Сброс сессии Telegram"""
    print("🔄 СБРОС СЕССИИ TELEGRAM")
    print("=" * 40)
    print()
    
    # Удаляем файлы сессии
    session_files = [
        "personal_account.session",
        "personal_account.session-journal"
    ]
    
    for session_file in session_files:
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                print(f"✅ Удален файл: {session_file}")
            except Exception as e:
                print(f"❌ Ошибка удаления {session_file}: {e}")
        else:
            print(f"ℹ️  Файл не найден: {session_file}")
    
    print()
    print("✅ Сессия сброшена!")
    print()
    print("💡 Теперь можете:")
    print("   1. Запустить тест подключения: python3 test_connection.py")
    print("   2. Или запустить автоматизацию: python3 easy_automation.py")
    print()
    print("⚠️  При следующем запуске потребуется:")
    print("   • Код подтверждения из Telegram")
    print("   • Пароль двухфакторной аутентификации (если включен)")

if __name__ == "__main__":
    reset_session()
