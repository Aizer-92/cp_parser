"""Скачивание шрифтов DejaVu как бинарных файлов"""
import urllib.request
import ssl
from pathlib import Path

font_dir = Path(__file__).parent / 'fonts'
font_dir.mkdir(exist_ok=True)

urls = {
    'DejaVuSans.ttf': 'https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip',
}

# Альтернативный источник - SourceForge
sourceforge_urls = [
    ('DejaVuSans.ttf', 'https://downloads.sourceforge.net/project/dejavu/dejavu/2.37/dejavu-fonts-ttf-2.37.tar.bz2'),
]

# Пробуем скачать напрямую с CDN
cdn_urls = {
    'DejaVuSans.ttf': 'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans.ttf',
    'DejaVuSans-Bold.ttf': 'https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans-Bold.ttf',
}

print("📥 Скачиваю шрифты DejaVu...")

# Создаем SSL context
context = ssl._create_unverified_context()

for filename, url in cdn_urls.items():
    output_file = font_dir / filename
    try:
        print(f"   Скачиваю {filename} из CDN...")
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(request, context=context, timeout=30)
        data = response.read()
        
        # Проверяем что это бинарный файл
        if len(data) < 100:
            print(f"   ⚠️  Слишком маленький файл: {len(data)} байт")
            continue
            
        with open(output_file, 'wb') as f:
            f.write(data)
        
        print(f"   ✅ Скачано: {filename} ({len(data)} байт)")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

# Проверяем результат
import subprocess
result = subprocess.run(['file', 'fonts/DejaVuSans.ttf', 'fonts/DejaVuSans-Bold.ttf'], 
                       capture_output=True, text=True)
print("\n📄 Проверка файлов:")
print(result.stdout)

