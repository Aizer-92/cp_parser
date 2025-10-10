"""
📦 CATEGORIES API ROUTER
Эндпоинты для управления категориями товаров (CRUD)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from database import get_database_connection, upsert_category

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("")
async def list_categories():
    """
    Получить список всех категорий
    """
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        if db_type == "postgres":
            cursor.execute("SELECT DISTINCT ON (id) id, data FROM categories ORDER BY id")
        else:
            cursor.execute("SELECT id, data FROM categories GROUP BY id ORDER BY id")
        
        rows = cursor.fetchall()
        cursor.close()
        
        categories = []
        for row in rows:
            import json
            
            # Для PostgreSQL row это dict, для SQLite это tuple
            if db_type == "postgres":
                category_id = row['id']
                category_json = row['data']
            else:
                category_id = row[0]
                category_json = row[1]
            
            # Парсим JSON
            if isinstance(category_json, str):
                category_data = json.loads(category_json)
            elif isinstance(category_json, dict):
                # PostgreSQL JSONB возвращает dict напрямую - создаем НОВЫЙ dict
                category_data = dict(category_json)
            else:
                category_data = dict(category_json) if category_json else {}
            
            # 🔥 КРИТИЧНО: Создаем НОВЫЙ dict с ID в начале для гарантии
            result = {
                'id': category_id,
                **category_data
            }
            
            categories.append(result)
        
        print(f"✅ Загружено {len(categories)} категорий")
        
        return categories
    except Exception as e:
        print(f"❌ Ошибка получения категорий: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка получения категорий: {str(e)}")

@router.get("/names")
async def get_category_names():
    """
    Получить список названий категорий для автокомплита (без авторизации для V2)
    """
    try:
        import yaml
        
        # Загружаем категории напрямую из YAML (проще и быстрее)
        categories_path = root_dir / "config" / "categories.yaml"
        
        with open(categories_path, 'r', encoding='utf-8') as f:
            categories_data = yaml.safe_load(f)
        
        categories = categories_data.get('categories', [])
        
        if not categories:
            print("⚠️ Категории пустые")
            return []
        
        # Формируем список категорий с названием и материалом
        category_names = []
        for cat in categories:
            name = cat.get('category', '')
            material = cat.get('material', '')
            
            if not name:
                continue
            
            # Создаем красивое отображение
            if material:
                display_name = f"{name} ({material})"
            else:
                display_name = name
            
            category_names.append({
                'value': name,  # Реальное значение для отправки в API
                'label': display_name  # Отображаемое название
            })
        
        print(f"✅ Загружено названий категорий: {len(category_names)}")
        return sorted(category_names, key=lambda x: x['label'])
    except Exception as e:
        print(f"❌ Ошибка получения названий категорий: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.get("/statistics")
async def get_categories_statistics():
    """
    Получить статистику по ценам для всех категорий
    """
    try:
        from database import get_database_connection
        
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Получаем статистику по ценам в юанях для каждой категории
        if db_type == "postgres":
            query = """
                SELECT 
                    category,
                    COUNT(*) as count,
                    MIN(price_yuan) as min_price,
                    MAX(price_yuan) as max_price,
                    AVG(price_yuan) as avg_price,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_yuan) as median_price
                FROM calculations
                WHERE category IS NOT NULL AND price_yuan > 0
                GROUP BY category
                ORDER BY count DESC
            """
        else:
            # SQLite не поддерживает PERCENTILE_CONT
            query = """
                SELECT 
                    category,
                    COUNT(*) as count,
                    MIN(price_yuan) as min_price,
                    MAX(price_yuan) as max_price,
                    AVG(price_yuan) as avg_price
                FROM calculations
                WHERE category IS NOT NULL AND price_yuan > 0
                GROUP BY category
                ORDER BY count DESC
            """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        statistics = []
        for row in rows:
            if db_type == "postgres":
                if hasattr(row, 'keys'):
                    stat = dict(row)
                else:
                    columns = [desc[0] for desc in cursor.description]
                    stat = dict(zip(columns, row))
            else:
                columns = [desc[0] for desc in cursor.description]
                stat = dict(zip(columns, row))
            
            # Приводим к нужному формату
            statistics.append({
                'category': stat['category'],
                'count': int(stat['count']) if stat['count'] else 0,
                'min_price': float(stat['min_price']) if stat.get('min_price') else 0,
                'max_price': float(stat['max_price']) if stat.get('max_price') else 0,
                'avg_price': float(stat['avg_price']) if stat.get('avg_price') else 0,
                'median_price': float(stat['median_price']) if stat.get('median_price') else None
            })
        
        cursor.close()
        conn.close()
        
        print(f"✅ Загружена статистика для {len(statistics)} категорий")
        return statistics
    except Exception as e:
        print(f"❌ Ошибка получения статистики категорий: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.get("/{category_id}")
async def get_category(category_id: int):
    """
    Получить категорию по ID
    """
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        if db_type == "postgres":
            cursor.execute("SELECT id, data FROM categories WHERE id = %s", (category_id,))
        else:
            cursor.execute("SELECT id, data FROM categories WHERE id = ?", (category_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        import json
        category_data = json.loads(row[1] if isinstance(row[1], str) else row[1])
        category_data['id'] = row[0]
        
        return category_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка получения категории: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения категории: {str(e)}")

@router.post("")
async def create_category(category: Dict[str, Any]):
    """
    Создать новую категорию
    """
    try:
        # Сохраняем в БД через upsert_category
        category_id = upsert_category(category)
        
        # Возвращаем созданную категорию с ID
        category['id'] = category_id
        
        print(f"✅ Категория создана: {category.get('category')} (ID: {category_id})")
        return category
    except Exception as e:
        print(f"❌ Ошибка создания категории: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка создания категории: {str(e)}")

@router.put("/{category_id}")
async def update_category(category_id: int, category: Dict[str, Any]):
    """
    Обновить существующую категорию
    """
    try:
        # Проверяем существование категории
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        if db_type == "postgres":
            cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        else:
            cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        # Обновляем в БД
        import json
        
        if db_type == "postgres":
            cursor.execute(
                "UPDATE categories SET data = %s WHERE id = %s",
                (json.dumps(category), category_id)
            )
        else:
            cursor.execute(
                "UPDATE categories SET data = ? WHERE id = ?",
                (json.dumps(category), category_id)
            )
        
        conn.commit()
        cursor.close()
        
        # Возвращаем обновленную категорию
        category['id'] = category_id
        
        print(f"✅ Категория обновлена: {category.get('category')} (ID: {category_id})")
        return category
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка обновления категории: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления категории: {str(e)}")

@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """
    Удалить категорию
    """
    try:
        conn, db_type = get_database_connection()
        cursor = conn.cursor()
        
        # Проверяем существование
        if db_type == "postgres":
            cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        else:
            cursor.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
        
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        # Удаляем
        if db_type == "postgres":
            cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        else:
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        
        conn.commit()
        cursor.close()
        
        print(f"✅ Категория удалена (ID: {category_id})")
        return {"success": True, "message": "Категория удалена"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка удаления категории: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления категории: {str(e)}")