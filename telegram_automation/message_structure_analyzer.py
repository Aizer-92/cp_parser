#!/usr/bin/env python3
"""
Message Structure Analyzer for Main mega ТОП
Анализатор структуры сообщений с планами и фактами
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from loguru import logger
import pandas as pd
import os

class MessageStructureAnalyzer:
    def __init__(self):
        self.config = self.load_config()
        self.client = None
        self.target_chat_name = "Main mega ТОП"
        self.target_chat_id = None
        
        # Настройка логирования
        os.makedirs("output/logs", exist_ok=True)
        logger.add("output/logs/message_structure.log", rotation="1 day", retention="7 days")
        
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
    
    async def get_sample_messages(self, limit=50):
        """Получение образцов сообщений для анализа структуры"""
        try:
            print(f"📥 Загрузка {limit} последних сообщений для анализа структуры...")
            
            messages = await self.client.get_messages(
                self.target_chat_id,
                limit=limit
            )
            
            print(f"✅ Получено {len(messages)} сообщений")
            
            # Фильтруем сообщения с текстом
            text_messages = []
            for msg in messages:
                if msg.text and len(msg.text.strip()) > 10:  # Минимум 10 символов
                    sender_name = await self.get_sender_name(msg)
                    text_messages.append({
                        'id': msg.id,
                        'date': msg.date,
                        'text': msg.text.strip(),
                        'sender': sender_name,
                        'length': len(msg.text.strip())
                    })
            
            print(f"📝 Найдено {len(text_messages)} текстовых сообщений")
            return text_messages
            
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
    
    def analyze_message_structure(self, messages):
        """Анализ структуры сообщений"""
        try:
            print("🔍 Анализ структуры сообщений...")
            
            structure_analysis = {
                'total_messages': len(messages),
                'senders': {},
                'patterns_found': {},
                'message_types': {},
                'sample_messages': []
            }
            
            # Анализируем каждое сообщение
            for msg in messages:
                text = msg['text'].lower()
                sender = msg['sender']
                
                # Подсчитываем отправителей
                if sender not in structure_analysis['senders']:
                    structure_analysis['senders'][sender] = 0
                structure_analysis['senders'][sender] += 1
                
                # Ищем паттерны планов и фактов
                patterns = [
                    ('план', r'план[:\s]*(\d+(?:\.\d+)?)'),
                    ('факт', r'факт[:\s]*(\d+(?:\.\d+)?)'),
                    ('п/ф', r'п/ф[:\s]*(\d+(?:\.\d+)?)'),
                    ('числа_слеш', r'(\d+(?:\.\d+)?)[/\-]\s*(\d+(?:\.\d+)?)'),
                    ('скобки', r'\((\d+(?:\.\d+)?)[^\d]*(\d+(?:\.\d+)?)\)'),
                    ('проценты', r'(\d+(?:\.\d+)?)%'),
                    ('задачи_нумерация', r'(\d+)[\.\)]\s'),
                    ('задачи_маркеры', r'[-•]\s'),
                ]
                
                found_patterns = []
                for pattern_name, pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        found_patterns.append(pattern_name)
                        if pattern_name not in structure_analysis['patterns_found']:
                            structure_analysis['patterns_found'][pattern_name] = 0
                        structure_analysis['patterns_found'][pattern_name] += 1
                
                # Определяем тип сообщения
                message_type = self.classify_message_type(text, found_patterns)
                if message_type not in structure_analysis['message_types']:
                    structure_analysis['message_types'][message_type] = 0
                structure_analysis['message_types'][message_type] += 1
                
                # Сохраняем образцы сообщений
                if len(structure_analysis['sample_messages']) < 20:  # Первые 20 сообщений
                    structure_analysis['sample_messages'].append({
                        'sender': sender,
                        'date': msg['date'].strftime('%Y-%m-%d %H:%M'),
                        'text': msg['text'][:200] + '...' if len(msg['text']) > 200 else msg['text'],
                        'type': message_type,
                        'patterns': found_patterns,
                        'length': msg['length']
                    })
            
            return structure_analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа структуры: {e}")
            return {}
    
    def classify_message_type(self, text, patterns):
        """Классификация типа сообщения"""
        if 'план' in patterns and 'факт' in patterns:
            return 'План/Факт'
        elif 'п/ф' in patterns:
            return 'П/Ф сокращение'
        elif 'числа_слеш' in patterns:
            return 'Числа через слеш'
        elif 'скобки' in patterns:
            return 'Числа в скобках'
        elif 'задачи_нумерация' in patterns or 'задачи_маркеры' in patterns:
            return 'Список задач'
        elif 'проценты' in patterns:
            return 'С процентами'
        elif any(word in text for word in ['план', 'факт', 'выполнено', 'сделано']):
            return 'Содержит ключевые слова'
        else:
            return 'Обычное сообщение'
    
    def find_plan_fact_messages(self, messages):
        """Поиск сообщений с планами и фактами"""
        try:
            print("🔍 Поиск сообщений с планами и фактами...")
            
            plan_fact_messages = []
            
            for msg in messages:
                text = msg['text'].lower()
                
                # Проверяем наличие планов и фактов
                has_plan = re.search(r'план[:\s]*(\d+(?:\.\d+)?)', text)
                has_fact = re.search(r'факт[:\s]*(\d+(?:\.\d+)?)', text)
                has_pf = re.search(r'п/ф[:\s]*(\d+(?:\.\d+)?)', text)
                has_numbers = re.search(r'(\d+(?:\.\d+)?)[/\-]\s*(\d+(?:\.\d+)?)', text)
                
                if has_plan or has_fact or has_pf or has_numbers:
                    plan_fact_messages.append({
                        'id': msg['id'],
                        'date': msg['date'],
                        'sender': msg['sender'],
                        'text': msg['text'],
                        'has_plan': bool(has_plan),
                        'has_fact': bool(has_fact),
                        'has_pf': bool(has_pf),
                        'has_numbers': bool(has_numbers),
                        'patterns': []
                    })
                    
                    # Извлекаем найденные паттерны
                    if has_plan:
                        plan_fact_messages[-1]['patterns'].append('план')
                    if has_fact:
                        plan_fact_messages[-1]['patterns'].append('факт')
                    if has_pf:
                        plan_fact_messages[-1]['patterns'].append('п/ф')
                    if has_numbers:
                        plan_fact_messages[-1]['patterns'].append('числа')
            
            print(f"✅ Найдено {len(plan_fact_messages)} сообщений с планами/фактами")
            return plan_fact_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска планов/фактов: {e}")
            return []
    
    def create_structure_report(self, structure_analysis, plan_fact_messages, filename=None):
        """Создание отчета по структуре сообщений"""
        try:
            if not filename:
                filename = f"output/message_structure_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            os.makedirs("output", exist_ok=True)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # Лист 1: Общая статистика
                stats_data = {
                    'Показатель': [
                        'Всего сообщений',
                        'Уникальных отправителей',
                        'Сообщений с планами/фактами',
                        'Самый активный отправитель',
                        'Средняя длина сообщения'
                    ],
                    'Значение': [
                        structure_analysis.get('total_messages', 0),
                        len(structure_analysis.get('senders', {})),
                        len(plan_fact_messages),
                        max(structure_analysis.get('senders', {}).items(), key=lambda x: x[1])[0] if structure_analysis.get('senders') else 'Нет данных',
                        round(sum(msg['length'] for msg in structure_analysis.get('sample_messages', [])) / len(structure_analysis.get('sample_messages', [1])), 2)
                    ]
                }
                
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Общая статистика', index=False)
                
                # Лист 2: Статистика по отправителям
                if structure_analysis.get('senders'):
                    sender_data = []
                    for sender, count in structure_analysis['senders'].items():
                        sender_data.append({
                            'Отправитель': sender,
                            'Количество сообщений': count
                        })
                    
                    df_senders = pd.DataFrame(sender_data)
                    df_senders = df_senders.sort_values('Количество сообщений', ascending=False)
                    df_senders.to_excel(writer, sheet_name='Статистика по отправителям', index=False)
                
                # Лист 3: Найденные паттерны
                if structure_analysis.get('patterns_found'):
                    pattern_data = []
                    for pattern, count in structure_analysis['patterns_found'].items():
                        pattern_data.append({
                            'Паттерн': pattern,
                            'Количество вхождений': count
                        })
                    
                    df_patterns = pd.DataFrame(pattern_data)
                    df_patterns = df_patterns.sort_values('Количество вхождений', ascending=False)
                    df_patterns.to_excel(writer, sheet_name='Найденные паттерны', index=False)
                
                # Лист 4: Типы сообщений
                if structure_analysis.get('message_types'):
                    type_data = []
                    for msg_type, count in structure_analysis['message_types'].items():
                        type_data.append({
                            'Тип сообщения': msg_type,
                            'Количество': count
                        })
                    
                    df_types = pd.DataFrame(type_data)
                    df_types = df_types.sort_values('Количество', ascending=False)
                    df_types.to_excel(writer, sheet_name='Типы сообщений', index=False)
                
                # Лист 5: Образцы сообщений
                if structure_analysis.get('sample_messages'):
                    df_samples = pd.DataFrame(structure_analysis['sample_messages'])
                    df_samples.to_excel(writer, sheet_name='Образцы сообщений', index=False)
                
                # Лист 6: Сообщения с планами/фактами
                if plan_fact_messages:
                    pf_data = []
                    for msg in plan_fact_messages:
                        pf_data.append({
                            'ID': msg['id'],
                            'Дата': msg['date'].strftime('%Y-%m-%d %H:%M'),
                            'Отправитель': msg['sender'],
                            'Текст': msg['text'][:300] + '...' if len(msg['text']) > 300 else msg['text'],
                            'Есть план': 'Да' if msg['has_plan'] else 'Нет',
                            'Есть факт': 'Да' if msg['has_fact'] else 'Нет',
                            'Есть П/Ф': 'Да' if msg['has_pf'] else 'Нет',
                            'Есть числа': 'Да' if msg['has_numbers'] else 'Нет',
                            'Паттерны': ', '.join(msg['patterns'])
                        })
                    
                    df_pf = pd.DataFrame(pf_data)
                    df_pf.to_excel(writer, sheet_name='Сообщения План Факт', index=False)
            
            print(f"✅ Отчет по структуре создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета: {e}")
            return None
    
    async def run_structure_analysis(self):
        """Запуск анализа структуры сообщений"""
        try:
            print("🚀 ЗАПУСК АНАЛИЗА СТРУКТУРЫ СООБЩЕНИЙ")
            print("=" * 60)
            
            # Подключение
            if not await self.connect():
                return
            
            # Поиск целевого чата
            if not await self.find_target_chat():
                return
            
            # Получение образцов сообщений
            messages = await self.get_sample_messages(limit=100)
            
            if not messages:
                print("❌ Не найдено сообщений для анализа")
                return
            
            # Анализ структуры
            structure_analysis = self.analyze_message_structure(messages)
            
            # Поиск сообщений с планами/фактами
            plan_fact_messages = self.find_plan_fact_messages(messages)
            
            # Создание отчета
            report_file = self.create_structure_report(structure_analysis, plan_fact_messages)
            
            if report_file:
                print(f"\n🎉 Анализ структуры завершен!")
                print(f"📁 Отчет сохранен: {report_file}")
                
                # Выводим краткую сводку
                print(f"\n📊 КРАТКАЯ СВОДКА:")
                print(f"Всего сообщений: {structure_analysis.get('total_messages', 0)}")
                print(f"Уникальных отправителей: {len(structure_analysis.get('senders', {}))}")
                print(f"Сообщений с планами/фактами: {len(plan_fact_messages)}")
                
                # Показываем топ отправителей
                if structure_analysis.get('senders'):
                    print(f"\n👥 ТОП ОТПРАВИТЕЛЕЙ:")
                    top_senders = sorted(structure_analysis['senders'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for sender, count in top_senders:
                        print(f"  {sender}: {count} сообщений")
                
                # Показываем найденные паттерны
                if structure_analysis.get('patterns_found'):
                    print(f"\n🔍 НАЙДЕННЫЕ ПАТТЕРНЫ:")
                    top_patterns = sorted(structure_analysis['patterns_found'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for pattern, count in top_patterns:
                        print(f"  {pattern}: {count} раз")
                
                # Показываем образцы сообщений
                if structure_analysis.get('sample_messages'):
                    print(f"\n📝 ПРИМЕРЫ СООБЩЕНИЙ:")
                    for i, msg in enumerate(structure_analysis['sample_messages'][:3]):
                        print(f"\n  {i+1}. {msg['sender']} ({msg['date']})")
                        print(f"     Тип: {msg['type']}")
                        print(f"     Паттерны: {', '.join(msg['patterns'])}")
                        print(f"     Текст: {msg['text'][:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            print(f"❌ Ошибка: {e}")

async def main():
    analyzer = MessageStructureAnalyzer()
    await analyzer.run_structure_analysis()

if __name__ == "__main__":
    asyncio.run(main())
