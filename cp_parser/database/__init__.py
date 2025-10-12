"""
Database package initialization
КРИТИЧЕСКИ ВАЖНО: Регистрируем PostgreSQL типы при импорте пакета
"""

# Регистрируем типы ПЕРВЫМ делом при импорте пакета database
try:
    import psycopg2
    import psycopg2.extensions
    import logging
    
    # Регистрируем TEXT (OID 25) глобально
    TEXT_OID = psycopg2.extensions.new_type((25,), "TEXT", psycopg2.STRING)
    psycopg2.extensions.register_type(TEXT_OID)
    
    # Регистрируем VARCHAR (OID 1043) глобально
    VARCHAR_OID = psycopg2.extensions.new_type((1043,), "VARCHAR", psycopg2.STRING)
    psycopg2.extensions.register_type(VARCHAR_OID)
    
    # Регистрируем BPCHAR (OID 1042) глобально
    BPCHAR_OID = psycopg2.extensions.new_type((1042,), "BPCHAR", psycopg2.STRING)
    psycopg2.extensions.register_type(BPCHAR_OID)
    
    print("✅ [INIT] PostgreSQL типы зарегистрированы глобально при импорте database пакета")
    
except Exception as e:
    print(f"❌ [INIT] Критическая ошибка регистрации типов: {e}")
    import traceback
    traceback.print_exc()


