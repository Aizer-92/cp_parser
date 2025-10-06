#!/usr/bin/env python3
"""
Быстрый тест подключения к PostgreSQL
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

print("🔌 Попытка подключения к PostgreSQL...")
print(f"URL: {POSTGRES_URL[:50]}...")

start = time.time()

try:
    engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 10})
    print(f"✅ Engine создан за {time.time()-start:.2f}с")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    print(f"✅ Session создана за {time.time()-start:.2f}с")
    
    result = session.execute(text("SELECT 1")).scalar()
    print(f"✅ Запрос выполнен за {time.time()-start:.2f}с: {result}")
    
    count = session.execute(text("SELECT COUNT(*) FROM projects")).scalar()
    print(f"✅ Projects count за {time.time()-start:.2f}с: {count}")
    
    session.close()
    print(f"\n✅ ВСЕ РАБОТАЕТ! Общее время: {time.time()-start:.2f}с")
    
except Exception as e:
    print(f"\n❌ ОШИБКА за {time.time()-start:.2f}с: {e}")
    import traceback
    traceback.print_exc()
