#!/usr/bin/env python3
"""
Telegram User Account Automation Script
Автоматизация с использованием пользовательского аккаунта (Telethon)
⚠️ ВНИМАНИЕ: Использование может нарушать ToS Telegram
"""

import json
import asyncio
import time
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from loguru import logger
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class TelegramUserAutomation:
    def __init__(self, config_path="config/user_config.json"):
        """Инициализация клиента с пользовательским аккаунтом"""
        self.config = self.load_config(config_path)
        self.client = None
        self.message_count = 0
        self.last_action_time = None
        
        # Настройка логирования
        logger.add("output/logs/user_automation.log", rotation="1 day", retention="7 days")
        
        # Счетчики для безопасности
        self.daily_message_count = 0
        self.last_reset_date = datetime.now().date()
    
    def load_config(self, config_path):
        """Загрузка конфигурации из JSON файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Конфигурационный файл не найден: {config_path}")
            return {}
    
    async def connect(self):
        """Подключение к Telegram"""
        try:
            self.client = TelegramClient(
                self.config.get('session_name', 'my_account'),
                self.config.get('api_id'),
                self.config.get('api_hash')
            )
            
            await self.client.start(phone=self.config.get('phone'))
            logger.info("Успешное подключение к Telegram")
            
            # Проверяем, нужен ли пароль двухфакторной аутентификации
            if not await self.client.is_user_authorized():
                logger.error("Не удалось авторизоваться. Проверьте API ключи и номер телефона.")
                return False
            
            return True
            
        except SessionPasswordNeededError:
            logger.error("Требуется пароль двухфакторной аутентификации")
            return False
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            return False
    
    def check_safety_limits(self):
        """Проверка лимитов безопасности"""
        current_date = datetime.now().date()
        
        # Сброс счетчика в новый день
        if current_date != self.last_reset_date:
            self.daily_message_count = 0
            self.last_reset_date = current_date
        
        # Проверка лимитов
        max_daily = self.config.get('safety', {}).get('max_messages_per_day', 50)
        if self.daily_message_count >= max_daily:
            logger.warning(f"Достигнут дневной лимит сообщений: {max_daily}")
            return False
        
        # Проверка времени между действиями
        if self.last_action_time:
            cooldown_minutes = self.config.get('safety', {}).get('cooldown_minutes', 30)
            time_since_last = datetime.now() - self.last_action_time
            if time_since_last.total_seconds() < cooldown_minutes * 60:
                logger.warning(f"Слишком мало времени с последнего действия: {cooldown_minutes} мин")
                return False
        
        return True
    
    async def send_message(self, chat_id, message):
        """Отправка сообщения с проверкой безопасности"""
        if not self.check_safety_limits():
            logger.warning("Отправка сообщения заблокирована из-за лимитов безопасности")
            return False
        
        try:
            await self.client.send_message(chat_id, message)
            self.daily_message_count += 1
            self.last_action_time = datetime.now()
            logger.info(f"Сообщение отправлено в чат {chat_id}")
            return True
        except FloodWaitError as e:
            logger.error(f"FloodWaitError: нужно подождать {e.seconds} секунд")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    async def monitor_messages(self):
        """Мониторинг входящих сообщений"""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                # Получаем информацию о сообщении
                sender = await event.get_sender()
                chat = await event.get_chat()
                message_text = event.message.text
                
                logger.info(f"Новое сообщение от {sender.first_name if sender else 'Unknown'}: {message_text[:50]}...")
                
                # Проверяем ключевые слова
                keywords = self.config.get('monitoring', {}).get('keywords', [])
                for keyword in keywords:
                    if keyword.lower() in message_text.lower():
                        logger.info(f"Найдено ключевое слово: {keyword}")
                        # Здесь можно добавить автоматические действия
                        break
                
                # Автоответ (если включен)
                if self.config.get('settings', {}).get('auto_reply', False):
                    await self.handle_auto_reply(event, message_text)
                
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def handle_auto_reply(self, event, message_text):
        """Обработка автоответов"""
        message_lower = message_text.lower()
        
        # Простые автоответы
        if 'привет' in message_lower or 'hello' in message_lower:
            reply = "Привет! Это автоматический ответ."
            await self.send_message(event.chat_id, reply)
        
        elif 'помощь' in message_lower or 'help' in message_lower:
            reply = "Доступные команды:\n• Статус\n• Помощь\n• Информация"
            await self.send_message(event.chat_id, reply)
    
    async def archive_chat(self, chat_id):
        """Архивирование чата"""
        if not self.config.get('automation', {}).get('auto_archive', False):
            return
        
        try:
            await self.client.edit_folder_peers(chat_id, folder=1)  # 1 = архив
            logger.info(f"Чат {chat_id} архивирован")
        except Exception as e:
            logger.error(f"Ошибка архивирования чата: {e}")
    
    async def save_media(self, message):
        """Сохранение медиафайлов"""
        if not self.config.get('automation', {}).get('save_media', False):
            return
        
        try:
            if message.media:
                # Создаем директорию для медиафайлов
                media_dir = "output/media"
                os.makedirs(media_dir, exist_ok=True)
                
                # Сохраняем файл
                filename = f"{media_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{message.id}"
                await message.download_media(filename)
                logger.info(f"Медиафайл сохранен: {filename}")
        except Exception as e:
            logger.error(f"Ошибка сохранения медиафайла: {e}")
    
    async def get_chat_info(self, chat_id):
        """Получение информации о чате"""
        try:
            chat = await self.client.get_entity(chat_id)
            return {
                'id': chat.id,
                'title': getattr(chat, 'title', ''),
                'username': getattr(chat, 'username', ''),
                'participants_count': getattr(chat, 'participants_count', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о чате: {e}")
            return None
    
    async def search_messages(self, chat_id, query, limit=10):
        """Поиск сообщений в чате"""
        try:
            messages = await self.client.get_messages(chat_id, search=query, limit=limit)
            return messages
        except Exception as e:
            logger.error(f"Ошибка поиска сообщений: {e}")
            return []
    
    async def get_recent_messages(self, chat_id, limit=20):
        """Получение последних сообщений"""
        try:
            messages = await self.client.get_messages(chat_id, limit=limit)
            return messages
        except Exception as e:
            logger.error(f"Ошибка получения сообщений: {e}")
            return []
    
    async def start_monitoring(self):
        """Запуск мониторинга"""
        if not self.config.get('settings', {}).get('monitoring_enabled', False):
            logger.info("Мониторинг отключен в конфигурации")
            return
        
        logger.info("Запуск мониторинга сообщений...")
        await self.monitor_messages()
        
        # Запускаем клиент
        await self.client.run_until_disconnected()
    
    async def emergency_stop(self):
        """Экстренная остановка"""
        logger.warning("ЭКСТРЕННАЯ ОСТАНОВКА АВТОМАТИЗАЦИИ")
        if self.client:
            await self.client.disconnect()
    
    async def get_status(self):
        """Получение статуса автоматизации"""
        status = {
            'connected': self.client and self.client.is_connected(),
            'daily_messages': self.daily_message_count,
            'last_action': self.last_action_time.isoformat() if self.last_action_time else None,
            'monitoring_enabled': self.config.get('settings', {}).get('monitoring_enabled', False),
            'auto_reply_enabled': self.config.get('settings', {}).get('auto_reply', False)
        }
        return status

async def main():
    """Главная функция"""
    automation = TelegramUserAutomation()
    
    try:
        # Подключение
        if not await automation.connect():
            logger.error("Не удалось подключиться к Telegram")
            return
        
        # Запуск мониторинга
        await automation.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка работы автоматизации: {e}")
    finally:
        if automation.client:
            await automation.client.disconnect()

if __name__ == "__main__":
    # Создаем директории
    os.makedirs("output/logs", exist_ok=True)
    os.makedirs("output/media", exist_ok=True)
    
    # Запускаем автоматизацию
    asyncio.run(main())
