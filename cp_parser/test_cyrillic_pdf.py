"""
Тестовый скрипт для проверки кириллицы в PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

# Регистрация шрифта DejaVu
font_dir = Path(__file__).parent / 'fonts'
font_file = font_dir / 'DejaVuSans.ttf'
font_bold_file = font_dir / 'DejaVuSans-Bold.ttf'

print(f"📁 Шрифт Regular: {font_file}")
print(f"📁 Существует: {font_file.exists()}")
print(f"📁 Шрифт Bold: {font_bold_file}")
print(f"📁 Существует: {font_bold_file.exists()}")

if font_file.exists():
    try:
        # Регистрируем шрифт
        font_regular = TTFont('DejaVuSans', str(font_file))
        font_bold = TTFont('DejaVuSans-Bold', str(font_bold_file))
        
        pdfmetrics.registerFont(font_regular)
        pdfmetrics.registerFont(font_bold)
        
        print("✅ Шрифты зарегистрированы")
        
        # Создаем тестовый PDF
        output_file = Path(__file__).parent / 'test_cyrillic.pdf'
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName='DejaVuSans-Bold',
            fontSize=18,
            textColor=colors.HexColor('#1f2937')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=12,
            textColor=colors.HexColor('#374151')
        )
        
        # Контент
        story = []
        
        story.append(Paragraph('ТЕСТ КИРИЛЛИЦЫ В PDF', title_style))
        story.append(Spacer(1, 10*mm))
        
        story.append(Paragraph('Товар: Чехол треугольный', normal_style))
        story.append(Paragraph('Описание: карабин металл, 10*10 см на молнии', normal_style))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('Образец: $8000.00 | Срок: 22 дн.', normal_style))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph('Цены: 300 шт - $6.64 / ₽558.04', normal_style))
        story.append(Paragraph('Цены: 300 шт - $6.84 / ₽574.84', normal_style))
        
        # Генерируем PDF
        doc.build(story)
        
        print(f"✅ PDF создан: {output_file}")
        print("📄 Откройте файл и проверьте кириллицу")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Шрифт не найден!")

