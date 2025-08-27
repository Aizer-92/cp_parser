#!/usr/bin/env python3
"""
Анализ реальных данных из базы Planfix
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json

def analyze_real_data():
    """Анализ реальных данных из БД"""
    db_path = "output/planfix_tasks_correct.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Проверяем структуру таблицы
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        print("📋 Структура таблицы tasks:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        print()
        
        # Получаем общую статистику
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        print(f"📊 Общее количество задач: {total_tasks}")
        
        # Статистика по статусам
        cursor.execute("SELECT status_name, COUNT(*) FROM tasks GROUP BY status_name ORDER BY COUNT(*) DESC")
        status_stats = cursor.fetchall()
        print("\n📈 Статистика по статусам:")
        for status, count in status_stats:
            percentage = (count / total_tasks) * 100
            print(f"   {status}: {count} ({percentage:.1f}%)")
        
        # Статистика по постановщикам
        cursor.execute("SELECT assigner, COUNT(*) FROM tasks WHERE assigner IS NOT NULL GROUP BY assigner ORDER BY COUNT(*) DESC LIMIT 10")
        assigner_stats = cursor.fetchall()
        print("\n👨‍💼 Топ-10 постановщиков:")
        for assigner, count in assigner_stats:
            percentage = (count / total_tasks) * 100
            print(f"   {assigner}: {count} ({percentage:.1f}%)")
        
        # Статистика по исполнителям
        cursor.execute("SELECT assignees, COUNT(*) FROM tasks WHERE assignees IS NOT NULL GROUP BY assignees ORDER BY COUNT(*) DESC LIMIT 10")
        assignee_stats = cursor.fetchall()
        print("\n👨‍💻 Топ-10 исполнителей:")
        for assignee, count in assignee_stats:
            percentage = (count / total_tasks) * 100
            print(f"   {assignee}: {count} ({percentage:.1f}%)")
        
        # Анализ дат
        cursor.execute("SELECT start_date_time FROM tasks WHERE start_date_time IS NOT NULL ORDER BY start_date_time")
        dates = cursor.fetchall()
        
        if dates:
            print(f"\n📅 Анализ дат:")
            print(f"   Первая задача: {dates[0][0]}")
            print(f"   Последняя задача: {dates[-1][0]}")
            
            # Конвертируем в datetime для анализа
            date_objects = []
            for date_str in [d[0] for d in dates]:
                try:
                    date_obj = pd.to_datetime(date_str)
                    date_objects.append(date_obj)
                except:
                    continue
            
            if date_objects:
                df_dates = pd.DataFrame(date_objects, columns=['date'])
                print(f"   Всего дат: {len(df_dates)}")
                print(f"   Период: {df_dates['date'].min()} - {df_dates['date'].max()}")
                
                # Анализ по месяцам
                monthly_stats = df_dates.groupby(df_dates['date'].dt.to_period('M')).size()
                print(f"\n📊 Задачи по месяцам:")
                for month, count in monthly_stats.items():
                    print(f"   {month}: {count}")
        
        # Анализ описаний
        cursor.execute("SELECT LENGTH(description) as desc_length FROM tasks WHERE description IS NOT NULL")
        desc_lengths = cursor.fetchall()
        if desc_lengths:
            lengths = [l[0] for l in desc_lengths]
            print(f"\n📝 Анализ описаний:")
            print(f"   Средняя длина: {sum(lengths)/len(lengths):.1f} символов")
            print(f"   Минимальная длина: {min(lengths)} символов")
            print(f"   Максимальная длина: {max(lengths)} символов")
        
        # Примеры задач
        cursor.execute("SELECT id, name, status_name, assigner, assignees, start_date_time FROM tasks ORDER BY start_date_time DESC LIMIT 5")
        recent_tasks = cursor.fetchall()
        print(f"\n🆕 Последние 5 задач:")
        for task in recent_tasks:
            print(f"   ID: {task[0]}, Название: {task[1][:50]}..., Статус: {task[2]}, Постановщик: {task[3]}, Исполнитель: {task[4]}, Дата: {task[5]}")
        
        conn.close()
        
        print(f"\n✅ Анализ завершен успешно!")
        print(f"🎯 Рекомендации:")
        print(f"   - Используйте итоговый дашборд для визуализации")
        print(f"   - Кастомные поля будут сгенерированы для демонстрации")
        print(f"   - Реальные данные будут обогащены аналитическими полями")
        
    except Exception as e:
        print(f"❌ Ошибка анализа данных: {e}")

if __name__ == "__main__":
    analyze_real_data()
