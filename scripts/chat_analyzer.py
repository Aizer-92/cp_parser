#!/usr/bin/env python3
"""
Анализатор чатов для автоматической категоризации диалогов из ChatGPT/Perplexity

Использование:
    python scripts/chat_analyzer.py "текст чата"
    python scripts/chat_analyzer.py --file "путь_к_файлу.txt"
"""

import argparse
import re
import json
from datetime import datetime
from pathlib import Path

# Ключевые слова для категоризации
CATEGORY_KEYWORDS = {
    'Business': [
        'startup', 'business', 'предпринимательство', 'бизнес', 'компания', 'стратегия',
        'маркетинг', 'продажи', 'клиенты', 'revenue', 'profit', 'конкуренты',
        'scaling', 'growth', 'venture', 'investment round', 'pitch', 'business plan'
    ],
    'Health': [
        'здоровье', 'health', 'медицина', 'nutrition', 'питание', 'диета', 'fitness',
        'тренировка', 'exercise', 'weight', 'вес', 'болезнь', 'симптомы', 'врач',
        'лечение', 'препарат', 'витамины', 'wellness', 'mental health', 'анализы',
        'тестостерон', 'testosterone', 'гормоны', 'hormones', 'эстрадиол', 'estradiol',
        'фсг', 'fsh', 'лг', 'lh', 'гспг', 'shbg', 'эндокринология', 'endocrinology'
    ],
    'Finance': [
        'финансы', 'finance', 'инвестиции', 'investment', 'акции', 'stocks', 'crypto',
        'криптовалюта', 'portfolio', 'портфель', 'budget', 'бюджет', 'savings',
        'накопления', 'debt', 'долг', 'pension', 'пенсия', 'tax', 'налоги'
    ],
    'Technology': [
        'программирование', 'programming', 'python', 'javascript', 'code', 'код',
        'algorithm', 'алгоритм', 'API', 'database', 'frontend', 'backend',
        'AI', 'artificial intelligence', 'machine learning', 'data science'
    ],
    'Learning': [
        'обучение', 'learning', 'education', 'курс', 'course', 'study', 'изучение',
        'навык', 'skill', 'сертификация', 'certification', 'университет', 'university',
        'книга', 'book', 'tutorial', 'урок', 'lesson', 'knowledge'
    ],
    'Home': [
        'дом', 'home', 'ремонт', 'renovation', 'design', 'дизайн', 'мебель', 'furniture',
        'кухня', 'kitchen', 'ванная', 'bathroom', 'garden', 'сад', 'smart home',
        'умный дом', 'проект', 'project', 'DIY'
    ],
    'Work': [
        'работа', 'work', 'карьера', 'career', 'job', 'должность', 'position',
        'resume', 'резюме', 'interview', 'собеседование', 'salary', 'зарплата',
        'promotion', 'повышение', 'team', 'команда', 'manager', 'менеджер'
    ]
}

# Теги для автоматического извлечения
COMMON_TAGS = {
    'startup', 'ai', 'python', 'javascript', 'react', 'health', 'fitness',
    'investment', 'crypto', 'marketing', 'design', 'productivity', 'learning',
    'testosterone', 'hormones', 'endocrinology', 'blood_test', 'medical'
}

def analyze_text_category(text):
    """Анализирует текст и определяет наиболее подходящую категорию"""
    text_lower = text.lower()
    category_scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Подсчитываем количество упоминаний ключевого слова
            score += len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower))
        category_scores[category] = score
    
    # Возвращаем категорию с наивысшим счетом
    if max(category_scores.values()) > 0:
        return max(category_scores, key=category_scores.get)
    else:
        return 'Personal'  # По умолчанию

def extract_tags(text):
    """Извлекает релевантные теги из текста"""
    text_lower = text.lower()
    found_tags = []
    
    for tag in COMMON_TAGS:
        if tag in text_lower:
            found_tags.append(f'#{tag}')
    
    return found_tags[:5]  # Максимум 5 тегов

def extract_key_insights(text):
    """Извлекает ключевые инсайты из текста чата"""
    insights = []
    
    # Ищем фразы, которые указывают на выводы или рекомендации
    patterns = [
        r'рекомендую[^.]*[.]',
        r'важно[^.]*[.]',
        r'ключевой[^.]*[.]',
        r'главное[^.]*[.]',
        r'вывод[^.]*[.]',
        r'recommend[^.]*[.]',
        r'important[^.]*[.]',
        r'key[^.]*[.]',
        r'conclusion[^.]*[.]'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        insights.extend(matches[:3])  # Максимум 3 инсайта на паттерн
    
    return insights[:5]  # Максимум 5 инсайтов

def suggest_filename(text, category):
    """Предлагает имя файла на основе содержимого"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Пытаемся извлечь ключевую тему из первых 200 символов
    first_part = text[:200].lower()
    
    # Простые правила для определения темы
    topic_keywords = {
        'план': 'Plan',
        'стратегия': 'Strategy', 
        'анализ': 'Analysis',
        'создание': 'Creation',
        'разработка': 'Development',
        'изучение': 'Learning',
        'сравнение': 'Comparison',
        'план': 'Planning'
    }
    
    topic = "Discussion"
    for keyword, english in topic_keywords.items():
        if keyword in first_part:
            topic = english
            break
    
    return f"{today}_{category}_{topic}"

def create_markdown_template(text, category, tags, insights, filename):
    """Создает markdown-шаблон для чата"""
    
    template = f"""# {filename.replace('_', ' ').replace('-', '.')}

**Дата:** {datetime.now().strftime("%d.%m.%Y")}  
**Источник:** [ChatGPT/Perplexity]  
**Категория:** {category}  
**Теги:** {' '.join(tags) if tags else '#новый_чат'}

## 🎯 О чем диалог
[Опишите суть и цель разговора]

## 💡 Ключевые выводы
"""
    
    if insights:
        for insight in insights:
            template += f"- {insight.strip()}\n"
    else:
        template += "- [Ключевой вывод 1]\n- [Ключевой вывод 2]\n- [Ключевой вывод 3]\n"
    
    template += """
## ✅ Что применить
- [ ] [Конкретное действие 1]
- [ ] [Конкретное действие 2]
- [ ] [Конкретное действие 3]

---

## 💬 Диалог

"""
    
    # Добавляем сам текст чата
    template += text
    
    template += """

---

## 🔗 Связанные материалы
- [Ссылки на связанные файлы в вашей системе]

## 📝 Мои заметки
[Ваши мысли после диалога, дополнительные идеи]
"""
    
    return template

def main():
    parser = argparse.ArgumentParser(description='Анализ и категоризация ИИ-чатов')
    parser.add_argument('text', nargs='?', help='Текст чата для анализа')
    parser.add_argument('--file', help='Путь к файлу с текстом чата')
    parser.add_argument('--output', help='Папка для сохранения результата')
    
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"❌ Файл {args.file} не найден")
            return
    elif args.text:
        text = args.text
    else:
        print("❌ Укажите текст чата или путь к файлу")
        print("Использование: python chat_analyzer.py 'текст' или --file file.txt")
        return
    
    # Анализируем текст
    print("🔍 Анализирую чат...")
    category = analyze_text_category(text)
    tags = extract_tags(text)
    insights = extract_key_insights(text)
    filename = suggest_filename(text, category)
    
    # Выводим результаты
    print(f"\n📊 Результаты анализа:")
    print(f"📁 Категория: {category}")
    print(f"🏷️  Теги: {', '.join(tags) if tags else 'Не найдено'}")
    print(f"💡 Инсайтов найдено: {len(insights)}")
    print(f"📝 Предложенное имя файла: {filename}.md")
    
    # Создаем шаблон
    markdown_content = create_markdown_template(text, category, tags, insights, filename)
    
    # Сохраняем файл если указана папка вывода
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{filename}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Файл сохранен: {output_file}")
    else:
        print(f"\n📄 Markdown шаблон:")
        print("=" * 50)
        print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)

if __name__ == "__main__":
    main()
