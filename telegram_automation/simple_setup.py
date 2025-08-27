#!/usr/bin/env python3
"""
Simple Telegram Setup
Простая настройка для личного аккаунта
"""

import json
import os

def main():
    print("🤖 ПРОСТАЯ НАСТРОЙКА TELEGRAM АВТОМАТИЗАЦИИ")
    print("=" * 50)
    print()
    
    print("📋 Для получения API ключей:")
    print("1. Перейдите на https://my.telegram.org")
    print("2. Войдите в свой аккаунт")
    print("3. Перейдите в 'API development tools'")
    print("4. Создайте приложение:")
    print("   - App title: Personal Automation")
    print("   - Short name: personal_auto")
    print("   - Platform: Desktop")
    print()
    
    # Получаем данные от пользователя
    print("🔑 Введите данные:")
    print("-" * 30)
    
    api_id = input("API ID (число): ").strip()
    api_hash = input("API Hash (строка): ").strip()
    phone = input("Номер телефона (+7XXXXXXXXXX): ").strip()
    
    # Проверяем данные
    if not api_id or not api_hash or not phone:
        print("❌ Все поля должны быть заполнены!")
        return
    
    # Создаем конфигурацию
    config = {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone,
        "session_name": "personal_account",
        "settings": {
            "auto_reply": False,
            "monitoring_enabled": True,
            "max_actions_per_hour": 5,
            "delay_between_actions": 10
        },
        "monitoring": {
            "target_chats": [],
            "keywords": [
                "важно",
                "срочно", 
                "внимание",
                "напоминание",
                "задача"
            ],
            "auto_save_important": True
        },
        "automation": {
            "auto_archive_old": True,
            "save_media": True,
            "backup_messages": True,
            "daily_summary": True
        },
        "safety": {
            "max_messages_per_day": 20,
            "cooldown_minutes": 60,
            "emergency_stop": False,
            "working_hours": {
                "start": "09:00",
                "end": "21:00"
            }
        },
        "notifications": {
            "daily_reminder": "09:00",
            "weekly_summary": "monday 10:00",
            "important_alerts": True
        },
        "enabled_features": [
            "daily_reminders",
            "message_monitoring",
            "keyword_alerts"
        ]
    }
    
    # Создаем директорию config
    os.makedirs("config", exist_ok=True)
    
    # Сохраняем конфигурацию
    config_file = "config/personal_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Конфигурация сохранена в {config_file}")
    print()
    
    # Создаем простой скрипт запуска
    startup_script = '''#!/usr/bin/env python3
"""
Simple Personal Telegram Automation
Простая автоматизация для личного аккаунта
"""

import asyncio
import json
from telethon import TelegramClient, events
from loguru import logger
import os

class SimpleTelegramAutomation:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/personal_automation.log", rotation="1 day", retention="7 days")
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def connect(self):
        try:
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            await self.client.start(phone=self.config['phone'])
            logger.info("✅ Подключение к Telegram установлено")
            
            # Получаем информацию о пользователе
            me = await self.client.get_me()
            print(f"👤 Подключен как: {me.first_name} {me.last_name or ''}")
            print(f"📱 Номер: {me.phone}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            print(f"❌ Ошибка: {e}")
            return False
    
    async def send_message_to_self(self, message):
        """Отправка сообщения самому себе"""
        try:
            me = await self.client.get_me()
            await self.client.send_message(me.id, message)
            logger.info("✅ Сообщение отправлено самому себе")
            print("✅ Сообщение отправлено!")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            print(f"❌ Ошибка отправки: {e}")
    
    async def monitor_messages(self):
        """Мониторинг важных сообщений"""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                sender = await event.get_sender()
                message_text = event.message.text
                
                # Проверяем ключевые слова
                keywords = self.config['monitoring']['keywords']
                for keyword in keywords:
                    if keyword.lower() in message_text.lower():
                        alert = f"🚨 ВАЖНОЕ СООБЩЕНИЕ!\\n"
                        alert += f"От: {sender.first_name if sender else 'Unknown'}\\n"
                        alert += f"Текст: {message_text[:100]}..."
                        
                        await self.send_message_to_self(alert)
                        logger.info(f"🔍 Найдено ключевое слово: {keyword}")
                        break
                        
            except Exception as e:
                logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    async def start_automation(self):
        """Запуск автоматизации"""
        logger.info("🚀 Запуск персональной автоматизации")
        print("🚀 Автоматизация запущена!")
        print("📋 Функции:")
        print("   • Мониторинг важных сообщений")
        print("   • Уведомления по ключевым словам")
        print("   • Отправка сообщений самому себе")
        print()
        print("💡 Для остановки нажмите Ctrl+C")
        print("-" * 50)
        
        # Настройка мониторинга
        await self.monitor_messages()
        
        # Запуск клиента
        await self.client.run_until_disconnected()

async def main():
    automation = SimpleTelegramAutomation()
    
    if await automation.connect():
        await automation.start_automation()
    else:
        print("❌ Не удалось подключиться к Telegram")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open("simple_automation.py", 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("📁 Созданные файлы:")
    print(f"   • {config_file} - конфигурация")
    print(f"   • simple_automation.py - скрипт автоматизации")
    print()
    
    print("🚀 Для запуска автоматизации:")
    print("   python3 simple_automation.py")
    print()
    
    print("⚠️  ВАЖНО:")
    print("   • Используйте только для личных целей")
    print("   • Соблюдайте лимиты безопасности")
    print("   • Не делитесь API ключами")

if __name__ == "__main__":
    main()
