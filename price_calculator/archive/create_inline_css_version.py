#!/usr/bin/env python3
"""
🛠️ СОЗДАНИЕ ВЕРСИИ СО ВСТРОЕННЫМ CSS
Объединяет все модульные CSS файлы обратно в HTML
"""

def create_inline_css_version():
    """Создает версию index.html со встроенными стилями"""
    
    # Читаем текущий HTML
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Читаем все CSS файлы
    css_files = [
        'static/css/main.css',
        'static/css/components/header.css', 
        'static/css/components/cards.css',
        'static/css/components/forms.css',
        'static/css/components/history.css'
    ]
    
    combined_css = ""
    
    for css_file in css_files:
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
                combined_css += f"\n    /* {css_file} */\n"
                combined_css += css_content + "\n"
        except FileNotFoundError:
            print(f"Файл не найден: {css_file}")
    
    # Заменяем ссылки на CSS на встроенный стиль
    css_links_section = '''    <!-- 🎨 МОДУЛЬНЫЙ CSS - ФАЗА 2.1 -->
    <link rel="stylesheet" href="/static/css/main.css">
    <link rel="stylesheet" href="/static/css/components/header.css">
    <link rel="stylesheet" href="/static/css/components/cards.css">
    <link rel="stylesheet" href="/static/css/components/forms.css">
    <link rel="stylesheet" href="/static/css/components/history.css">'''
    
    inline_css_section = f'''    <!-- 🎨 ВСТРОЕННЫЙ CSS - ВОССТАНОВЛЕН -->
    <style>
{combined_css}    </style>'''
    
    # Заменяем в HTML
    new_html = html_content.replace(css_links_section, inline_css_section)
    
    # Сохраняем новую версию
    with open('index_with_inline_css.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print("Создан index_with_inline_css.html со встроенными стилями")
    print(f"Размер: {len(new_html):,} символов")
    
    return True

if __name__ == "__main__":
    create_inline_css_version()
