#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СОЗДАНИЕ ЧИСТОГО БИЗНЕС-ОТЧЕТА
Без технических деталей, только бизнес-аналитика
"""

from pathlib import Path
from business_final_analyzer import BusinessFinalAnalyzer

def format_number(value, format_type='number'):
    """Форматирование чисел для отчета"""
    if value is None:
        return 'н/д'
    
    if format_type == 'currency_rub':
        return f"{value:,.0f} ₽"
    elif format_type == 'currency_cny':
        return f"{value:,.1f} ¥"
    elif format_type == 'currency_usd':
        return f"${value:,.1f}"
    elif format_type == 'number':
        return f"{value:,.0f}"
    elif format_type == 'percentage':
        return f"{value:.1f}%"
    elif format_type == 'density':
        return f"{value:,.1f} кг/м³"
    else:
        return f"{value:,.1f}"

def format_gaussian_for_report(ranges, field):
    """Форматирование гауссовского диапазона для отчета"""
    if field not in ranges:
        return 'недостаточно данных'
    
    r = ranges[field]
    
    if field == 'price_rub':
        return f"{r['lower_70']:,.0f} - {r['upper_70']:,.0f} ₽ (медиана {r['median']:,.0f} ₽)"
    elif field == 'price_cny':
        return f"{r['lower_70']:,.1f} - {r['upper_70']:,.1f} ¥ (медиана {r['median']:,.1f} ¥)"
    elif field == 'avg_requested_tirage':
        return f"{r['lower_70']:,.0f} - {r['upper_70']:,.0f} шт (медиана {r['median']:,.0f} шт)"
    elif field == 'cargo_density':
        return f"{r['lower_70']:,.1f} - {r['upper_70']:,.1f} кг/м³ (медиана {r['median']:,.1f} кг/м³)"
    elif field == 'transport_tariff':
        return f"${r['lower_70']:,.1f} - ${r['upper_70']:,.1f}/кг (медиана ${r['median']:,.1f}/кг)"
    else:
        return f"{r['lower_70']:,.1f} - {r['upper_70']:,.1f}"

def create_clean_business_report():
    """Создание чистого бизнес-отчета"""
    
    print("📊 СОЗДАНИЕ ЧИСТОГО БИЗНЕС-ОТЧЕТА")
    print("=" * 50)
    
    # Запуск анализа
    db_path = Path(__file__).parent.parent / "promo_calculator" / "database" / "advanced_merged_products_clean.db"
    analyzer = BusinessFinalAnalyzer(db_path)
    
    try:
        stats, coverage, excluded_count, total_products = analyzer.run_business_analysis()
        
        # Подготовка данных
        main_categories = [stat for stat in stats if stat['тип'] == 'main']
        subcategories = [stat for stat in stats if stat['тип'] == 'sub']
        
        total_categorized = sum(stat['товары'] for stat in stats)
        analyzed_products = total_products - excluded_count
        
        # Топ категории
        top_10 = sorted(main_categories, key=lambda x: x['товары'], reverse=True)[:10]
        
        # Создание отчета
        report_content = f"""# 📊 Анализ Товарного Ассортимента Компании

**Дата анализа:** 23 сентября 2025  
**Охват:** {total_categorized:,} товаров ({coverage:.1f}% от ассортимента)

---

## 🎯 Ключевые Результаты

### 📈 Общие Показатели
- **Всего товаров проанализировано:** {analyzed_products:,}
- **Товаров распределено по категориям:** {total_categorized:,}
- **Покрытие категоризации:** {coverage:.1f}%
- **Основных товарных категорий:** {len(main_categories)}
- **Детальных подкategorий:** {len(subcategories)}

### 🏆 Структура Ассортимента

**ТОП-10 категорий по объему:**

"""

        for i, category in enumerate(top_10, 1):
            percentage = (category['товары'] / analyzed_products) * 100
            report_content += f"{i:2d}. **{category['категория'].title()}** — {category['товары']:,} товаров ({percentage:.1f}% ассортимента)\n"
        
        report_content += f"""
---

## 💰 Ценовая Аналитика

### 🎯 Реальные 70% Диапазоны по Категориям
*Показывают реальные 70% товаров в каждой категории для планирования закупок*

"""

        # Ценовая аналитика по топ категориям
        for category in top_10[:5]:
            report_content += f"#### {category['категория'].title()}\n"
            report_content += f"- **Товаров:** {category['товары']:,}\n"
            
            if category['gaussian_ranges']:
                if 'price_rub' in category['gaussian_ranges']:
                    report_content += f"- **Ценовой диапазон:** {format_gaussian_for_report(category['gaussian_ranges'], 'price_rub')}\n"
                if 'avg_requested_tirage' in category['gaussian_ranges']:
                    report_content += f"- **Тиражи:** {format_gaussian_for_report(category['gaussian_ranges'], 'avg_requested_tirage')}\n"
                if 'transport_tariff' in category['gaussian_ranges']:
                    report_content += f"- **Логистика:** {format_gaussian_for_report(category['gaussian_ranges'], 'transport_tariff')}\n"
            
            report_content += "\n"

        report_content += f"""---

## 📦 Логистическая Аналитика

### 🚚 Характеристики Доставки

"""

        # Логистическая информация
        logistics_categories = []
        for category in main_categories[:10]:
            if category['gaussian_ranges'] and 'transport_tariff' in category['gaussian_ranges'] and 'cargo_density' in category['gaussian_ranges']:
                logistics_categories.append(category)

        for category in logistics_categories[:5]:
            report_content += f"**{category['категория'].title()}**\n"
            if 'cargo_density' in category['gaussian_ranges']:
                report_content += f"- Плотность: {format_gaussian_for_report(category['gaussian_ranges'], 'cargo_density')}\n"
            if 'transport_tariff' in category['gaussian_ranges']:
                report_content += f"- Стоимость доставки: {format_gaussian_for_report(category['gaussian_ranges'], 'transport_tariff')}\n"
            report_content += "\n"

        report_content += f"""---

## 🔍 Детальный Анализ Категорий

### 📋 Полная Структура Ассортимента

"""

        # Полная структура с подкатегориями
        sorted_main = sorted(main_categories, key=lambda x: x['товары'], reverse=True)
        
        for main_cat in sorted_main:
            percentage = (main_cat['товары'] / analyzed_products) * 100
            report_content += f"#### {main_cat['категория'].title()}\n"
            report_content += f"- **Товаров:** {main_cat['товары']:,} ({percentage:.1f}% ассортимента)\n"
            
            # Медианные показатели
            if main_cat['медиана_цены_rub']:
                report_content += f"- **Медианная цена:** {format_number(main_cat['медиана_цены_rub'], 'currency_rub')}\n"
            if main_cat['средний_тираж']:
                report_content += f"- **Средний тираж:** {format_number(main_cat['средний_тираж'], 'number')} шт\n"
            
            # Реальные 70% диапазоны
            if main_cat['gaussian_ranges']:
                report_content += f"- **Диапазоны для планирования (реальные 70% товаров):**\n"
                if 'price_rub' in main_cat['gaussian_ranges']:
                    report_content += f"  - Цены: {format_gaussian_for_report(main_cat['gaussian_ranges'], 'price_rub')}\n"
                if 'avg_requested_tirage' in main_cat['gaussian_ranges']:
                    report_content += f"  - Тиражи: {format_gaussian_for_report(main_cat['gaussian_ranges'], 'avg_requested_tirage')}\n"
            
            # Подкатегории
            related_subcats = [s for s in subcategories if s['родитель'] == main_cat['категория']]
            if related_subcats:
                report_content += f"- **Подкатегории:**\n"
                for subcat in sorted(related_subcats, key=lambda x: x['товары'], reverse=True):
                    sub_percentage = (subcat['товары'] / main_cat['товары']) * 100
                    report_content += f"  - {subcat['категория']}: {subcat['товары']:,} товаров ({sub_percentage:.0f}%)\n"
            
            report_content += "\n"

        report_content += f"""---

## 📊 Рекомендации для Бизнеса

### 🎯 Приоритетные Направления

1. **Фокус на лидеров** — категории "{top_10[0]['категория']}", "{top_10[1]['категория']}", "{top_10[2]['категория']}" составляют {sum(cat['товары'] for cat in top_10[:3]) / analyzed_products * 100:.1f}% ассортимента

2. **Оптимизация закупок** — используйте реальные 70% диапазоны для планирования тиражей

3. **Ценовое позиционирование** — реальные 70% товаров в каждой категории помогут установить конкурентные цены

### 💡 Возможности Роста

"""

        # Анализ потенциала роста
        growth_opportunities = []
        for category in main_categories:
            if 20 <= category['товары'] <= 100:  # Средние категории с потенциалом
                growth_opportunities.append(category)
        
        growth_opportunities = sorted(growth_opportunities, key=lambda x: x['товары'], reverse=True)[:5]
        
        for i, category in enumerate(growth_opportunities, 1):
            report_content += f"{i}. **{category['категория'].title()}** — {category['товары']} товаров, потенциал расширения\n"

        report_content += f"""

### 📈 Планирование Закупок

**Используйте реальные 70% диапазоны для:**
- Определения оптимальных тиражей заказов
- Прогнозирования логистических затрат  
- Ценового позиционирования новых товаров
- Планирования складских запасов

---

## 📋 Заключение

Анализ показал хорошо структурированный ассортимент с {len(main_categories)} основными категориями товаров. 

**Ключевые достижения:**
- ✅ {coverage:.1f}% товаров успешно категоризированы
- ✅ {len([s for s in stats if s['gaussian_ranges']])} категорий имеют статистически значимые данные для планирования
- ✅ Иерархическая структура с {len(subcategories)} подкатегориями для детального анализа

**Система готова для:**
- Автоматизации закупочных процессов
- Стратегического планирования ассортимента
- Оптимизации логистики и складских операций

---

*Анализ выполнен на основе {total_products:,} товаров из корпоративной базы данных.*
*Реальные 70% диапазоны рассчитаны для каждой категории индивидуально.*
"""

        # Сохранение отчета
        output_file = Path(__file__).parent / 'CLEAN_BUSINESS_REPORT.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Чистый бизнес-отчет создан: {output_file}")
        print(f"📋 Содержание:")
        print(f"  • Ключевые результаты и структура ассортимента")
        print(f"  • Ценовая аналитика с гауссовскими диапазонами")
        print(f"  • Логистическая аналитика по категориям")
        print(f"  • Детальный анализ всех {len(main_categories)} категорий")
        print(f"  • Бизнес-рекомендации и планы роста")
        print(f"")
        print(f"🎯 ОСОБЕННОСТИ ОТЧЕТА:")
        print(f"  • Без технических деталей — только бизнес-информация")
        print(f"  • Реальные 70% диапазоны для каждой категории отдельно")
        print(f"  • Готовые рекомендации для принятия решений")
        print(f"  • Структурированный анализ для презентаций")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analyzer.conn.close()

if __name__ == "__main__":
    create_clean_business_report()
