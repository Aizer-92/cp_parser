#!/usr/bin/env python3
"""
Проверка сколько изображений нужно загрузить на FTP
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def check_upload_needed():
    """Проверяет сколько изображений нужно загрузить на FTP"""
    
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("📊 АНАЛИЗ ИЗОБРАЖЕНИЙ ДЛЯ ЗАГРУЗКИ НА FTP")
    print("=" * 80)
    
    with db.get_session() as session:
        # Всего изображений в БД
        total = session.execute(text("""
            SELECT COUNT(*) FROM product_images
        """)).scalar()
        
        # Изображения с локальными путями (нужно загрузить)
        local = session.execute(text("""
            SELECT COUNT(*) FROM product_images
            WHERE image_url LIKE 'storage/images/%'
        """)).scalar()
        
        # Изображения уже на FTP (https)
        on_ftp = session.execute(text("""
            SELECT COUNT(*) FROM product_images
            WHERE image_url LIKE 'https://%'
        """)).scalar()
        
        # Изображения без URL (ошибки?)
        no_url = session.execute(text("""
            SELECT COUNT(*) FROM product_images
            WHERE image_url IS NULL OR image_url = ''
        """)).scalar()
        
        # Локальные файлы
        local_dir = Path('storage/images')
        if local_dir.exists():
            local_files = list(local_dir.glob('*'))
            local_files_count = len(local_files)
            total_size = sum(f.stat().st_size for f in local_files if f.is_file())
        else:
            local_files_count = 0
            total_size = 0
        
        print(f"\n📦 СТАТИСТИКА БД:")
        print(f"  Всего записей:           {total:,}")
        print(f"  ✅ На FTP (https):        {on_ftp:,}")
        print(f"  📥 Нужно загрузить:       {local:,}")
        print(f"  ⚠️  Без URL:              {no_url:,}")
        
        print(f"\n💾 ЛОКАЛЬНЫЕ ФАЙЛЫ:")
        print(f"  Файлов в storage/images: {local_files_count:,}")
        print(f"  Общий размер:            {total_size:,} байт ({total_size/1024/1024:.1f} МБ)")
        
        print(f"\n🎯 ИТОГ:")
        if local > 0:
            print(f"  ❗ Нужно загрузить {local:,} изображений на FTP")
            print(f"  📁 Локально доступно: {local_files_count:,} файлов")
            
            if local_files_count != local:
                diff = abs(local_files_count - local)
                print(f"  ⚠️  Расхождение: {diff:,} (БД vs локальные файлы)")
        else:
            print(f"  ✅ Все изображения уже на FTP!")
        
        print("=" * 80)
        
        # Показываем команду для загрузки
        if local > 0:
            print(f"\n💡 ДЛЯ ЗАГРУЗКИ НА FTP:")
            print(f"  python3 upload_all_images_simple.py")
            print("=" * 80)
        
        return {
            'total': total,
            'on_ftp': on_ftp,
            'to_upload': local,
            'no_url': no_url,
            'local_files': local_files_count,
            'local_size_mb': total_size/1024/1024
        }

if __name__ == '__main__':
    check_upload_needed()

