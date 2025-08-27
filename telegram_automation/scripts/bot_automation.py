#!/usr/bin/env python3
"""
Telegram Bot Automation Script
Безопасная автоматизация с использованием официального Bot API
"""

import json
import asyncio
import schedule
import time
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class TelegramBotAutomation:
    def __init__(self, config_path="config/bot_config.json"):
        """Инициализация бота с конфигурацией"""
        self.config = self.load_config(config_path)
        self.bot = Bot(token=self.config['bot_token'])
        self.application = Application.builder().token(self.config['bot_token']).build()
        
        # Настройка логирования
        logger.add("output/logs/bot.log", rotation="1 day", retention="7 days")
        
        # Регистрация обработчиков
        self.setup_handlers()
    
    def load_config(self, config_path):
        """Загрузка конфигурации из JSON файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Конфигурационный файл не найден: {config_path}")
            return {}
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("schedule", self.schedule_command))
        
        # Обработка сообщений
        if self.config.get('settings', {}).get('auto_reply', False):
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        welcome_message = f"Привет, {user.first_name}! Я автоматический бот.\n\n"
        welcome_message += "Доступные команды:\n"
        welcome_message += "/help - Показать справку\n"
        welcome_message += "/status - Статус бота\n"
        welcome_message += "/schedule - Настроить расписание"
        
        await update.message.reply_text(welcome_message)
        logger.info(f"Пользователь {user.id} запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = self.config.get('auto_replies', {}).get('help', 'Справка недоступна')
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        status = f"🤖 Статус бота: Активен\n"
        status += f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        status += f"📊 Автоответы: {'Включены' if self.config.get('settings', {}).get('auto_reply') else 'Выключены'}\n"
        status += f"🔔 Уведомления: {'Включены' if self.config.get('settings', {}).get('daily_notifications') else 'Выключены'}"
        
        await update.message.reply_text(status)
    
    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /schedule"""
        schedule_info = "📅 Расписание уведомлений:\n\n"
        notifications = self.config.get('notifications', {})
        
        if notifications.get('morning_time'):
            schedule_info += f"🌅 Утреннее: {notifications['morning_time']}\n"
        if notifications.get('evening_time'):
            schedule_info += f"🌆 Вечернее: {notifications['evening_time']}\n"
        
        await update.message.reply_text(schedule_info)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка входящих сообщений"""
        message_text = update.message.text.lower()
        auto_replies = self.config.get('auto_replies', {})
        
        # Простые автоответы
        if 'привет' in message_text or 'hello' in message_text:
            reply = auto_replies.get('hello', 'Привет!')
            await update.message.reply_text(reply)
            logger.info(f"Автоответ отправлен пользователю {update.effective_user.id}")
    
    async def send_notification(self, message: str, chat_id: str = None):
        """Отправка уведомления"""
        target_chat = chat_id or self.config.get('chat_id')
        if target_chat:
            try:
                await self.bot.send_message(chat_id=target_chat, text=message)
                logger.info(f"Уведомление отправлено в чат {target_chat}")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")
    
    async def send_daily_notification(self):
        """Отправка ежедневного уведомления"""
        current_time = datetime.now().strftime('%H:%M')
        message = f"🌅 Доброе утро! Время: {current_time}\n\n"
        message += "📋 Задачи на сегодня:\n"
        message += "• Проверить сообщения\n"
        message += "• Обновить статус\n"
        message += "• Планирование на завтра"
        
        await self.send_notification(message)
    
    def setup_scheduler(self):
        """Настройка планировщика задач"""
        if self.config.get('settings', {}).get('daily_notifications'):
            morning_time = self.config.get('notifications', {}).get('morning_time', '09:00')
            evening_time = self.config.get('notifications', {}).get('evening_time', '21:00')
            
            schedule.every().day.at(morning_time).do(
                lambda: asyncio.create_task(self.send_daily_notification())
            )
            
            logger.info(f"Планировщик настроен: утренние уведомления в {morning_time}")
    
    async def run_scheduler(self):
        """Запуск планировщика"""
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Проверка каждую минуту
    
    async def start(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        
        # Настройка планировщика
        self.setup_scheduler()
        
        # Запуск планировщика в отдельной задаче
        asyncio.create_task(self.run_scheduler())
        
        # Запуск бота
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
    
    async def stop(self):
        """Остановка бота"""
        logger.info("Остановка Telegram бота...")
        await self.application.stop()
        await self.application.shutdown()

async def main():
    """Главная функция"""
    bot = TelegramBotAutomation()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Создаем директорию для логов
    os.makedirs("output/logs", exist_ok=True)
    
    # Запускаем бота
    asyncio.run(main())
