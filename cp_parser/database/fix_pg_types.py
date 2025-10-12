"""
КРИТИЧЕСКИЙ ПАТЧ: Регистрация PostgreSQL типов ДО импорта SQLAlchemy
Этот модуль должен импортироваться ПЕРВЫМ в app.py
"""

import logging

# Регистрируем типы ГЛОБАЛЬНО до любых операций с SQLAlchemy
try:
    import psycopg2
    import psycopg2.extensions
    
    # Регистрируем TEXT (OID 25) глобально
    TEXT_OID = psycopg2.extensions.new_type((25,), "TEXT", psycopg2.STRING)
    psycopg2.extensions.register_type(TEXT_OID)
    
    # Регистрируем VARCHAR (OID 1043) глобально
    VARCHAR_OID = psycopg2.extensions.new_type((1043,), "VARCHAR", psycopg2.STRING)
    psycopg2.extensions.register_type(VARCHAR_OID)
    
    # Регистрируем BPCHAR (OID 1042) глобально
    BPCHAR_OID = psycopg2.extensions.new_type((1042,), "BPCHAR", psycopg2.STRING)
    psycopg2.extensions.register_type(BPCHAR_OID)
    
    logging.info("✅ PostgreSQL типы зарегистрированы глобально (TEXT, VARCHAR, BPCHAR)")
    
except Exception as e:
    logging.error(f"❌ Критическая ошибка регистрации типов: {e}")
    raise







КРИТИЧЕСКИЙ ПАТЧ: Регистрация PostgreSQL типов ДО импорта SQLAlchemy
Этот модуль должен импортироваться ПЕРВЫМ в app.py
"""

import logging

# Регистрируем типы ГЛОБАЛЬНО до любых операций с SQLAlchemy
try:
    import psycopg2
    import psycopg2.extensions
    
    # Регистрируем TEXT (OID 25) глобально
    TEXT_OID = psycopg2.extensions.new_type((25,), "TEXT", psycopg2.STRING)
    psycopg2.extensions.register_type(TEXT_OID)
    
    # Регистрируем VARCHAR (OID 1043) глобально
    VARCHAR_OID = psycopg2.extensions.new_type((1043,), "VARCHAR", psycopg2.STRING)
    psycopg2.extensions.register_type(VARCHAR_OID)
    
    # Регистрируем BPCHAR (OID 1042) глобально
    BPCHAR_OID = psycopg2.extensions.new_type((1042,), "BPCHAR", psycopg2.STRING)
    psycopg2.extensions.register_type(BPCHAR_OID)
    
    logging.info("✅ PostgreSQL типы зарегистрированы глобально (TEXT, VARCHAR, BPCHAR)")
    
except Exception as e:
    logging.error(f"❌ Критическая ошибка регистрации типов: {e}")
    raise










