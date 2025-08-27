#!/usr/bin/env python3
"""
Telegram Automation Setup Guide
Руководство по настройке автоматизации Telegram
"""

import json
import os
from datetime import datetime

def print_header():
    """Вывод заголовка"""
    print("=" * 60)
    print("🤖 TELEGRAM AUTOMATION SETUP GUIDE")
    print("=" * 60)
    print()

def print_section(title):
    """Вывод заголовка секции"""
    print(f"\n📋 {title}")
    print("-" * 40)

def setup_bot_automation():
    """Настройка автоматизации бота"""
    print_section("НАСТРОЙКА TELEGRAM BOT")
    
    print("1. Создание бота:")
    print("   • Откройте @BotFather в Telegram")
    print("   • Отправьте команду /newbot")
    print("   • Следуйте инструкциям для создания бота")
    print("   • Сохраните полученный токен")
    print()
    
    print("2. Получение Chat ID:")
    print("   • Добавьте бота в нужный чат")
    print("   • Отправьте сообщение в чат")
    print("   • Перейдите по ссылке: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
    print("   • Найдите 'chat' -> 'id' в ответе")
    print()
    
    print("3. Настройка конфигурации:")
    config = {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "chat_id": "YOUR_CHAT_ID_HERE",
        "admin_users": ["YOUR_USER_ID_HERE"],
        "settings": {
            "auto_reply": True,
            "daily_notifications": True,
            "monitoring_enabled": True,
            "max_messages_per_hour": 20
        },
        "notifications": {
            "morning_time": "09:00",
            "evening_time": "21:00",
            "timezone": "Europe/Moscow"
        },
        "auto_replies": {
            "hello": "Привет! Я автоматический бот.",
            "help": "Доступные команды:\n/start - Начать\n/help - Помощь\n/status - Статус"
        }
    }
    
    print("   Отредактируйте файл config/bot_config.json:")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print()

def setup_user_automation():
    """Настройка автоматизации пользовательского аккаунта"""
    print_section("НАСТРОЙКА ПОЛЬЗОВАТЕЛЬСКОГО АККАУНТА")
    
    print("⚠️  ВНИМАНИЕ: Использование может нарушать ToS Telegram!")
    print("   Используйте только для личных целей и с осторожностью.")
    print()
    
    print("1. Получение API ключей:")
    print("   • Перейдите на https://my.telegram.org")
    print("   • Войдите в свой аккаунт Telegram")
    print("   • Перейдите в 'API development tools'")
    print("   • Создайте новое приложение")
    print("   • Сохраните API ID и API Hash")
    print()
    
    print("2. Настройка конфигурации:")
    config = {
        "api_id": "YOUR_API_ID_HERE",
        "api_hash": "YOUR_API_HASH_HERE",
        "phone": "YOUR_PHONE_NUMBER_HERE",
        "session_name": "my_account",
        "settings": {
            "auto_reply": False,
            "monitoring_enabled": True,
            "max_actions_per_hour": 10,
            "delay_between_actions": 5
        },
        "monitoring": {
            "target_chats": ["CHAT_ID_1", "CHAT_ID_2"],
            "keywords": ["важно", "срочно", "внимание"]
        },
        "automation": {
            "auto_archive": True,
            "auto_mute": False,
            "save_media": True
        },
        "safety": {
            "max_messages_per_day": 50,
            "cooldown_minutes": 30,
            "emergency_stop": False
        }
    }
    
    print("   Отредактируйте файл config/user_config.json:")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print()

def setup_environment():
    """Настройка окружения"""
    print_section("НАСТРОЙКА ОКРУЖЕНИЯ")
    
    print("1. Установка зависимостей:")
    print("   pip install -r requirements.txt")
    print()
    
    print("2. Создание .env файла:")
    env_content = """# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here

# Telegram User Account Configuration
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE=your_phone_number_here

# Safety Settings
MAX_MESSAGES_PER_DAY=50
COOLDOWN_MINUTES=30
"""
    print("   Создайте файл .env в корне проекта:")
    print(env_content)
    print()

def create_example_scripts():
    """Создание примеров скриптов"""
    print_section("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ")
    
    # Пример для бота
    bot_example = '''# Пример использования бота
import asyncio
from scripts.bot_automation import TelegramBotAutomation

async def example():
    bot = TelegramBotAutomation()
    await bot.send_notification("Тестовое сообщение")
    await bot.stop()

asyncio.run(example())
'''
    
    print("1. Пример использования бота:")
    print(bot_example)
    
    # Пример для пользовательского аккаунта
    user_example = '''# Пример использования пользовательского аккаунта
import asyncio
from scripts.user_automation import TelegramUserAutomation

async def example():
    automation = TelegramUserAutomation()
    if await automation.connect():
        await automation.send_message("chat_id", "Тестовое сообщение")
        await automation.client.disconnect()

asyncio.run(example())
'''
    
    print("2. Пример использования пользовательского аккаунта:")
    print(user_example)

def safety_guidelines():
    """Руководство по безопасности"""
    print_section("РУКОВОДСТВО ПО БЕЗОПАСНОСТИ")
    
    guidelines = [
        "🔒 Никогда не делитесь API ключами",
        "⏰ Соблюдайте лимиты на количество сообщений",
        "🛑 Используйте экстренную остановку при необходимости",
        "📊 Регулярно проверяйте логи активности",
        "🚫 Не используйте для спама или массовой рассылки",
        "🔄 Делайте перерывы между действиями",
        "📱 Используйте отдельный номер для тестирования",
        "💾 Регулярно создавайте резервные копии данных"
    ]
    
    for guideline in guidelines:
        print(f"   {guideline}")
    print()

def troubleshooting():
    """Решение проблем"""
    print_section("РЕШЕНИЕ ПРОБЛЕМ")
    
    problems = {
        "Ошибка авторизации": [
            "Проверьте правильность API ID и API Hash",
            "Убедитесь, что номер телефона указан корректно",
            "Проверьте, что двухфакторная аутентификация настроена правильно"
        ],
        "FloodWaitError": [
            "Слишком много запросов - увеличьте задержки",
            "Проверьте настройки лимитов в конфигурации",
            "Используйте экстренную остановку"
        ],
        "Бот не отвечает": [
            "Проверьте правильность токена бота",
            "Убедитесь, что бот добавлен в чат",
            "Проверьте права бота в чате"
        ],
        "Ошибки подключения": [
            "Проверьте интернет-соединение",
            "Убедитесь, что Telegram доступен",
            "Попробуйте использовать VPN"
        ]
    }
    
    for problem, solutions in problems.items():
        print(f"❓ {problem}:")
        for solution in solutions:
            print(f"   • {solution}")
        print()

def main():
    """Главная функция"""
    print_header()
    
    print("Выберите тип автоматизации:")
    print("1. Telegram Bot (рекомендуется)")
    print("2. Пользовательский аккаунт (осторожно!)")
    print("3. Полное руководство")
    print("4. Выход")
    
    while True:
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == "1":
            setup_bot_automation()
            break
        elif choice == "2":
            setup_user_automation()
            break
        elif choice == "3":
            setup_bot_automation()
            setup_user_automation()
            setup_environment()
            create_example_scripts()
            safety_guidelines()
            troubleshooting()
            break
        elif choice == "4":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")
    
    print("\n" + "=" * 60)
    print("✅ Настройка завершена!")
    print("📖 Дополнительная информация в README.md")
    print("🚀 Готово к использованию!")

if __name__ == "__main__":
    main()
