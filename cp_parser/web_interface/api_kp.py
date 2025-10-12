"""
API для работы с КП (коммерческим предложением)

Эндпоинты:
- POST   /api/kp/add           - Добавить товар (price_offer) в КП
- DELETE /api/kp/remove/<id>   - Удалить из КП
- GET    /api/kp               - Получить все товары в КП
- DELETE /api/kp/clear         - Очистить КП
- GET    /api/kp/check         - Проверить какие price_offer_id уже в КП
"""

from flask import Blueprint, request, jsonify, session
from sqlalchemy import text
from datetime import datetime
import uuid

# Создаем Blueprint
api_kp = Blueprint('api_kp', __name__, url_prefix='/api/kp')

def get_session_id():
    """Получает или создает session_id для пользователя"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True  # Сессия сохраняется между визитами
    return session['session_id']

@api_kp.route('/add', methods=['POST'])
def add_to_kp(db_session):
    """Добавляет вариант цены (price_offer) в КП"""
    
    try:
        data = request.get_json()
        
        product_id = data.get('product_id')
        price_offer_id = data.get('price_offer_id')
        
        if not product_id or not price_offer_id:
            return jsonify({
                'success': False,
                'error': 'Не указан product_id или price_offer_id'
            }), 400
        
        session_id = get_session_id()
        
        # Проверяем существует ли товар и вариант цены
        result = db_session.execute(text("""
            SELECT p.id, p.name, po.id, po.quantity, po.route
            FROM products p
            JOIN price_offers po ON po.product_id = p.id
            WHERE p.id = :product_id AND po.id = :price_offer_id
        """), {
            'product_id': product_id,
            'price_offer_id': price_offer_id
        })
        
        row = result.fetchone()
        if not row:
            return jsonify({
                'success': False,
                'error': 'Товар или вариант цены не найден'
            }), 404
        
        # Добавляем в КП (если уже есть - игнорируем благодаря UNIQUE constraint)
        db_session.execute(text("""
            INSERT INTO kp_items (session_id, product_id, price_offer_id)
            VALUES (:session_id, :product_id, :price_offer_id)
            ON CONFLICT (session_id, price_offer_id) DO NOTHING
        """), {
            'session_id': session_id,
            'product_id': product_id,
            'price_offer_id': price_offer_id
        })
        db_session.commit()
        
        # Получаем общее количество товаров в КП
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM kp_items WHERE session_id = :session_id
        """), {'session_id': session_id})
        kp_count = result.scalar()
        
        return jsonify({
            'success': True,
            'message': f'Добавлено в КП: {row[1]} ({row[3]} шт, {row[4]})',
            'kp_count': kp_count
        })
        
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_kp.route('/remove/<int:kp_item_id>', methods=['DELETE'])
def remove_from_kp(kp_item_id, db_session):
    """Удаляет товар из КП"""
    
    try:
        session_id = get_session_id()
        
        # Удаляем
        db_session.execute(text("""
            DELETE FROM kp_items
            WHERE id = :kp_item_id AND session_id = :session_id
        """), {
            'kp_item_id': kp_item_id,
            'session_id': session_id
        })
        db_session.commit()
        
        # Получаем обновленное количество
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM kp_items WHERE session_id = :session_id
        """), {'session_id': session_id})
        kp_count = result.scalar()
        
        return jsonify({
            'success': True,
            'message': 'Удалено из КП',
            'kp_count': kp_count
        })
        
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_kp.route('', methods=['GET'])
@api_kp.route('/', methods=['GET'])
def get_kp(db_session):
    """Получает все товары в КП с полной информацией"""
    
    try:
        session_id = get_session_id()
        
        # Получаем все товары КП с join к products и price_offers
        result = db_session.execute(text("""
            SELECT 
                ki.id as kp_item_id,
                ki.quantity,
                ki.user_comment,
                ki.added_at,
                p.id as product_id,
                p.name as product_name,
                p.description,
                p.article_number,
                po.id as price_offer_id,
                po.quantity as offer_quantity,
                po.route,
                po.price_usd,
                po.price_rub,
                po.delivery_days,
                (SELECT image_url 
                 FROM product_images pi 
                 WHERE pi.product_id = p.id 
                 AND pi.image_url IS NOT NULL
                 ORDER BY 
                     CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END,
                     pi.id
                 LIMIT 1
                ) as main_image_url
            FROM kp_items ki
            JOIN products p ON p.id = ki.product_id
            JOIN price_offers po ON po.id = ki.price_offer_id
            WHERE ki.session_id = :session_id
            ORDER BY ki.added_at DESC
        """), {'session_id': session_id})
        
        kp_items = []
        for row in result:
            # Формируем URL изображения (если нет image_url, пробуем filename)
            image_url = row[14]
            if not image_url:
                # Попробуем найти по filename
                img_result = db_session.execute(text("""
                    SELECT image_filename
                    FROM product_images
                    WHERE product_id = :product_id
                    AND image_filename IS NOT NULL
                    ORDER BY 
                        CASE WHEN column_number = 1 THEN 0 ELSE 1 END,
                        id
                    LIMIT 1
                """), {'product_id': row[4]})
                filename_row = img_result.fetchone()
                if filename_row and filename_row[0]:
                    image_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename_row[0]}"
            
            kp_items.append({
                'kp_item_id': row[0],
                'quantity': row[1],
                'user_comment': row[2],
                'added_at': row[3].isoformat() if row[3] else None,
                'product': {
                    'id': row[4],
                    'name': row[5],
                    'description': row[6],
                    'article_number': row[7],
                    'image_url': image_url
                },
                'price_offer': {
                    'id': row[8],
                    'quantity': row[9],
                    'route': row[10],
                    'price_usd': float(row[11]) if row[11] else None,
                    'price_rub': float(row[12]) if row[12] else None,
                    'delivery_days': row[13]
                }
            })
        
        return jsonify({
            'success': True,
            'kp_items': kp_items,
            'total_items': len(kp_items)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_kp.route('/clear', methods=['DELETE'])
def clear_kp(db_session):
    """Очищает весь КП"""
    
    try:
        session_id = get_session_id()
        
        db_session.execute(text("""
            DELETE FROM kp_items WHERE session_id = :session_id
        """), {'session_id': session_id})
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': 'КП очищен',
            'kp_count': 0
        })
        
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_kp.route('/check', methods=['POST'])
def check_in_kp(db_session):
    """Проверяет какие price_offer_id уже добавлены в КП"""
    
    try:
        data = request.get_json()
        price_offer_ids = data.get('price_offer_ids', [])
        
        if not price_offer_ids:
            return jsonify({
                'success': True,
                'in_kp': []
            })
        
        session_id = get_session_id()
        
        # Формируем placeholders для SQL IN
        placeholders = ','.join([f':id{i}' for i in range(len(price_offer_ids))])
        params = {'session_id': session_id}
        params.update({f'id{i}': pid for i, pid in enumerate(price_offer_ids)})
        
        result = db_session.execute(text(f"""
            SELECT price_offer_id
            FROM kp_items
            WHERE session_id = :session_id
            AND price_offer_id IN ({placeholders})
        """), params)
        
        in_kp = [row[0] for row in result.fetchall()]
        
        return jsonify({
            'success': True,
            'in_kp': in_kp
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

