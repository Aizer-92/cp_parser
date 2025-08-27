#!/usr/bin/env python3
"""
Plan/Fact Message Loader for Main mega ТОП
Загрузчик сообщений с планами и фактами
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from loguru import logger
import pandas as pd
import os

class PlanFactMessageLoader:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        self.target_chat_name = "Main mega ТОП"
        self.target_chat_id = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/plan_fact_loader.log", rotation="1 day", retention="7 days")
        
    def load_config(self):
        with open("config/personal_config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def connect(self):
        """Подключение к Telegram"""
        try:
            self.client = TelegramClient(
                self.config['session_name'],
                self.config['api_id'],
                self.config['api_hash']
            )
            
            await self.client.start()
            
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                print(f"👤 Подключен как: {me.first_name}")
                return True
            else:
                print("❌ Не удалось авторизоваться")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def find_target_chat(self):
        """Поиск целевого чата"""
        try:
            print(f"🔍 Поиск чата '{self.target_chat_name}'...")
            
            dialogs = await self.client.get_dialogs()
            
            for dialog in dialogs:
                if self.target_chat_name.lower() in dialog.name.lower():
                    self.target_chat_id = dialog.id
                    print(f"✅ Найден чат: {dialog.name} (ID: {dialog.id})")
                    return True
            
            print(f"❌ Чат '{self.target_chat_name}' не найден")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска чата: {e}")
            return False
    
    async def get_plan_fact_messages(self, weeks_back=12):
        """Получение сообщений с планами и фактами за последние недели"""
        try:
            print(f"📥 Загрузка сообщений с планами/фактами за последние {weeks_back} недель...")
            
            # Вычисляем дату начала
            today = datetime.now()
            start_date = today - timedelta(weeks=weeks_back)
            
            # Получаем сообщения
            messages = await self.client.get_messages(
                self.target_chat_id,
                offset_date=start_date,
                limit=5000  # Большой лимит для поиска
            )
            
            print(f"✅ Получено {len(messages)} сообщений")
            
            # Фильтруем сообщения с планами и фактами
            plan_fact_messages = []
            
            for msg in messages:
                if msg.text and len(msg.text.strip()) > 5:
                    text = msg.text.lower()
                    
                    # Проверяем наличие планов и фактов
                    has_plan = re.search(r'план[:\s]*(\d+(?:\.\d+)?)', text)
                    has_fact = re.search(r'факт[:\s]*(\d+(?:\.\d+)?)', text)
                    has_pf = re.search(r'п/ф[:\s]*(\d+(?:\.\d+)?)', text)
                    has_numbers = re.search(r'(\d+(?:\.\d+)?)[/\-]\s*(\d+(?:\.\d+)?)', text)
                    has_brackets = re.search(r'\((\d+(?:\.\d+)?)[^\d]*(\d+(?:\.\d+)?)\)', text)
                    
                    if has_plan or has_fact or has_pf or has_numbers or has_brackets:
                        sender_name = await self.get_sender_name(msg)
                        plan_fact_messages.append({
                            'id': msg.id,
                            'date': msg.date,
                            'text': msg.text.strip(),
                            'sender': sender_name,
                            'has_plan': bool(has_plan),
                            'has_fact': bool(has_fact),
                            'has_pf': bool(has_pf),
                            'has_numbers': bool(has_numbers),
                            'has_brackets': bool(has_brackets),
                            'patterns': []
                        })
                        
                        # Заполняем паттерны
                        if has_plan:
                            plan_fact_messages[-1]['patterns'].append('план')
                        if has_fact:
                            plan_fact_messages[-1]['patterns'].append('факт')
                        if has_pf:
                            plan_fact_messages[-1]['patterns'].append('п/ф')
                        if has_numbers:
                            plan_fact_messages[-1]['patterns'].append('числа')
                        if has_brackets:
                            plan_fact_messages[-1]['patterns'].append('скобки')
            
            print(f"📊 Найдено {len(plan_fact_messages)} сообщений с планами/фактами")
            return plan_fact_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений: {e}")
            return []
    
    async def get_sender_name(self, message):
        """Получение имени отправителя"""
        try:
            sender = await message.get_sender()
            if sender:
                return f"{sender.first_name} {sender.last_name or ''}".strip()
            return "Unknown"
        except:
            return "Unknown"
    
    def analyze_message_content(self, messages):
        """Детальный анализ содержимого сообщений"""
        try:
            print("🔍 Детальный анализ содержимого сообщений...")
            
            analysis = {
                'total_messages': len(messages),
                'senders': {},
                'patterns_usage': {},
                'message_structure': {},
                'sample_structures': []
            }
            
            for msg in messages:
                sender = msg['sender']
                text = msg['text']
                patterns = msg['patterns']
                
                # Статистика по отправителям
                if sender not in analysis['senders']:
                    analysis['senders'][sender] = {
                        'count': 0,
                        'patterns': set(),
                        'sample_texts': []
                    }
                analysis['senders'][sender]['count'] += 1
                analysis['senders'][sender]['patterns'].update(patterns)
                
                if len(analysis['senders'][sender]['sample_texts']) < 3:
                    analysis['senders'][sender]['sample_texts'].append(text[:200])
                
                # Статистика по паттернам
                for pattern in patterns:
                    if pattern not in analysis['patterns_usage']:
                        analysis['patterns_usage'][pattern] = 0
                    analysis['patterns_usage'][pattern] += 1
                
                # Анализ структуры сообщения
                structure = self.analyze_message_structure(text)
                if structure not in analysis['message_structure']:
                    analysis['message_structure'][structure] = 0
                analysis['message_structure'][structure] += 1
                
                # Сохраняем образцы структур
                if len(analysis['sample_structures']) < 10:
                    analysis['sample_structures'].append({
                        'sender': sender,
                        'date': msg['date'].strftime('%Y-%m-%d'),
                        'structure': structure,
                        'text': text[:300],
                        'patterns': patterns
                    })
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа содержимого: {e}")
            return {}
    
    def analyze_message_structure(self, text):
        """Анализ структуры отдельного сообщения"""
        try:
            lines = text.split('\n')
            structure_parts = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Определяем тип строки
                if re.match(r'^\d+[\.\)]', line):
                    structure_parts.append('нумерованный_список')
                elif re.match(r'^[-•]', line):
                    structure_parts.append('маркированный_список')
                elif re.search(r'план[:\s]*\d+', line.lower()):
                    structure_parts.append('строка_с_планом')
                elif re.search(r'факт[:\s]*\d+', line.lower()):
                    structure_parts.append('строка_с_фактом')
                elif re.search(r'\d+/\d+', line):
                    structure_parts.append('числа_через_слеш')
                elif re.search(r'\(\d+[^\d]*\d+\)', line):
                    structure_parts.append('числа_в_скобках')
                elif len(line) < 50:
                    structure_parts.append('короткая_строка')
                else:
                    structure_parts.append('обычная_строка')
            
            return ' -> '.join(structure_parts) if structure_parts else 'пустое_сообщение'
            
        except Exception as e:
            return 'ошибка_анализа'
    
    def create_detailed_report(self, messages, analysis, filename=None):
        """Создание детального отчета"""
        try:
            if not filename:
                filename = f"output/plan_fact_messages_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            os.makedirs("output", exist_ok=True)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Лист 1: Все сообщения с планами/фактами
                if messages:
                    messages_data = []
                    for msg in messages:
                        messages_data.append({
                            'ID': msg['id'],
                            'Дата': msg['date'].strftime('%Y-%m-%d %H:%M'),
                            'Отправитель': msg['sender'],
                            'Текст': msg['text'],
                            'Паттерны': ', '.join(msg['patterns']),
                            'Есть план': 'Да' if msg['has_plan'] else 'Нет',
                            'Есть факт': 'Да' if msg['has_fact'] else 'Нет',
                            'Есть П/Ф': 'Да' if msg['has_pf'] else 'Нет',
                            'Есть числа': 'Да' if msg['has_numbers'] else 'Нет',
                            'Есть скобки': 'Да' if msg['has_brackets'] else 'Нет'
                        })
                    
                    df_messages = pd.DataFrame(messages_data)
                    df_messages = df_messages.sort_values(['Отправитель', 'Дата'], ascending=[True, False])
                    df_messages.to_excel(writer, sheet_name='Все сообщения', index=False)
                
                # Лист 2: Анализ по отправителям
                if analysis.get('senders'):
                    sender_data = []
                    for sender, data in analysis['senders'].items():
                        sender_data.append({
                            'Отправитель': sender,
                            'Количество сообщений': data['count'],
                            'Используемые паттерны': ', '.join(sorted(data['patterns'])),
                            'Образец 1': data['sample_texts'][0] if data['sample_texts'] else '',
                            'Образец 2': data['sample_texts'][1] if len(data['sample_texts']) > 1 else '',
                            'Образец 3': data['sample_texts'][2] if len(data['sample_texts']) > 2 else ''
                        })
                    
                    df_senders = pd.DataFrame(sender_data)
                    df_senders = df_senders.sort_values('Количество сообщений', ascending=False)
                    df_senders.to_excel(writer, sheet_name='Анализ по отправителям', index=False)
                
                # Лист 3: Использование паттернов
                if analysis.get('patterns_usage'):
                    pattern_data = []
                    for pattern, count in analysis['patterns_usage'].items():
                        pattern_data.append({
                            'Паттерн': pattern,
                            'Количество использований': count,
                            'Процент от общего': round(count / len(messages) * 100, 2)
                        })
                    
                    df_patterns = pd.DataFrame(pattern_data)
                    df_patterns = df_patterns.sort_values('Количество использований', ascending=False)
                    df_patterns.to_excel(writer, sheet_name='Использование паттернов', index=False)
                
                # Лист 4: Структуры сообщений
                if analysis.get('message_structure'):
                    structure_data = []
                    for structure, count in analysis['message_structure'].items():
                        structure_data.append({
                            'Структура': structure,
                            'Количество': count,
                            'Процент': round(count / len(messages) * 100, 2)
                        })
                    
                    df_structures = pd.DataFrame(structure_data)
                    df_structures = df_structures.sort_values('Количество', ascending=False)
                    df_structures.to_excel(writer, sheet_name='Структуры сообщений', index=False)
                
                # Лист 5: Образцы структур
                if analysis.get('sample_structures'):
                    df_samples = pd.DataFrame(analysis['sample_structures'])
                    df_samples.to_excel(writer, sheet_name='Образцы структур', index=False)
            
            print(f"✅ Детальный отчет создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета: {e}")
            return None
    
    async def run_loader(self):
        """Запуск загрузчика"""
        try:
            print("🚀 ЗАПУСК ЗАГРУЗЧИКА СООБЩЕНИЙ С ПЛАНАМИ И ФАКТАМИ")
            print("=" * 70)
            
            # Подключение
            if not await self.connect():
                return
            
            # Поиск целевого чата
            if not await self.find_target_chat():
                return
            
            # Получение сообщений
            messages = await self.get_plan_fact_messages(weeks_back=12)
            
            if not messages:
                print("❌ Не найдено сообщений с планами/фактами")
                return
            
            # Анализ содержимого
            analysis = self.analyze_message_content(messages)
            
            # Создание отчета
            report_file = self.create_detailed_report(messages, analysis)
            
            if report_file:
                print(f"\n🎉 Загрузка и анализ завершены!")
                print(f"📁 Отчет сохранен: {report_file}")
                
                # Выводим краткую сводку
                print(f"\n📊 КРАТКАЯ СВОДКА:")
                print(f"Всего сообщений с планами/фактами: {len(messages)}")
                print(f"Уникальных отправителей: {len(analysis.get('senders', {}))}")
                print(f"Период анализа: 12 недель")
                
                # Показываем топ отправителей
                if analysis.get('senders'):
                    print(f"\n👥 ТОП ОТПРАВИТЕЛЕЙ:")
                    top_senders = sorted(analysis['senders'].items(), key=lambda x: x[1]['count'], reverse=True)[:5]
                    for sender, data in top_senders:
                        print(f"  {sender}: {data['count']} сообщений")
                
                # Показываем популярные паттерны
                if analysis.get('patterns_usage'):
                    print(f"\n🔍 ПОПУЛЯРНЫЕ ПАТТЕРНЫ:")
                    top_patterns = sorted(analysis['patterns_usage'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for pattern, count in top_patterns:
                        print(f"  {pattern}: {count} раз")
                
                # Показываем образцы структур
                if analysis.get('sample_structures'):
                    print(f"\n📝 ОБРАЗЦЫ СТРУКТУР:")
                    for i, sample in enumerate(analysis['sample_structures'][:3]):
                        print(f"\n  {i+1}. {sample['sender']} ({sample['date']})")
                        print(f"     Структура: {sample['structure']}")
                        print(f"     Паттерны: {', '.join(sample['patterns'])}")
                        print(f"     Текст: {sample['text'][:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            print(f"❌ Ошибка: {e}")

async def main():
    loader = PlanFactMessageLoader()
    await loader.run_loader()

if __name__ == "__main__":
    asyncio.run(main())
