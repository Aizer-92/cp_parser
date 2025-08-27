#!/usr/bin/env python3
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
                        alert = f"🚨 ВАЖНОЕ СООБЩЕНИЕ!\n"
                        alert += f"От: {sender.first_name if sender else 'Unknown'}\n"
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
