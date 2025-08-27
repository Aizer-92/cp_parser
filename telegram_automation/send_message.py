#!/usr/bin/env python3
"""
Send Message to Self
Простая отправка сообщения самому себе
"""

import asyncio
import json
import getpass
from telethon import TelegramClient

class MessageSender:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def code_callback(self):
        """Обработчик для кода подтверждения"""
        print("\n📱 Введите код подтверждения из Telegram:")
        code = input("Код: ").strip()
        return code
    
    def password_callback(self):
        """Обработчик для пароля двухфакторной аутентификации"""
        print("\n🔐 Введите пароль двухфакторной аутентификации:")
        print("💡 Пароль не будет отображаться при вводе")
        password = getpass.getpass("Пароль: ")
        return password
    
    async def send_message(self, message):
        """Отправка сообщения"""
        try:
            print("🔗 Подключение к Telegram...")
            
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            # Подключение с обработчиками
            await self.client.start(
                phone=self.config['phone'],
                code_callback=self.code_callback,
                password_callback=self.password_callback
            )
            
            # Получаем информацию о пользователе
            me = await self.client.get_me()
            print(f"👤 Подключен как: {me.first_name}")
            
            # Отправляем сообщение
            print("📤 Отправка сообщения...")
            await self.client.send_message(me.id, message)
            print("✅ Сообщение отправлено!")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
        finally:
            if self.client:
                await self.client.disconnect()

async def main():
    print("📤 ОТПРАВКА СООБЩЕНИЯ В TELEGRAM")
    print("=" * 40)
    print()
    
    # Получаем сообщение от пользователя
    message = input("Введите сообщение для отправки: ").strip()
    
    if not message:
        message = "🤖 Тест автоматизации Telegram\n✅ Подключение работает!"
        print(f"📝 Используется тестовое сообщение: {message}")
    
    sender = MessageSender()
    success = await sender.send_message(message)
    
    if success:
        print("\n🎉 Сообщение отправлено успешно!")
        print("✅ Подключение к Telegram работает")
    else:
        print("\n❌ Не удалось отправить сообщение")

if __name__ == "__main__":
    asyncio.run(main())
