import math
from flask import Blueprint, request, jsonify
import models

api_v2_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

# =======================================================
# РІВЕНЬ 3: ВЕРСІОНУВАННЯ API (API v2) З ПАГІНАЦІЄЮ ТА СОРТУВАННЯМ
# =======================================================

@api_v2_bp.route('/products', methods=['GET'])
def get_products_v2():
    """[API v2] Отримати список товарів з розширеною пагінацією та сортуванням
    ---
    tags:
      - Products (API v2 - Рівень 3)
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Номер сторінки (починаючи з 1)
      - name: per_page
        in: query
        type: integer
        required: false
        default: 6
        description: Кількість товарів на сторінці (від 1 до 50)
      - name: category
        in: query
        type: string
        required: false
        description: Фільтрація за категорією
      - name: sort
        in: query
        type: string
        required: false
        enum: [newest, price_asc, price_desc, name_asc]
        default: newest
        description: Сортування результатів
    responses:
      200:
        description: Успішна відповідь у форматі конверта (envelope) з метаданими пагінації
        schema:
          type: object
          properties:
            version:
              type: string
              example: "v2"
            pagination:
              type: object
              properties:
                page:
                  type: integer
                  example: 1
                per_page:
                  type: integer
                  example: 6
                total_items:
                  type: integer
                  example: 20
                total_pages:
                  type: integer
                  example: 4
                has_next:
                  type: boolean
                  example: true
                has_prev:
                  type: boolean
                  example: false
            items:
              type: array
              items:
                type: object
      400:
        description: Некоректні параметри пагінації або сортування
    """
    page_param = request.args.get('page', '1')
    per_page_param = request.args.get('per_page', '6')
    category = request.args.get('category')
    sort = request.args.get('sort', 'newest')

    # Валідація числових параметрів пагінації
    try:
        page = int(page_param)
        per_page = int(per_page_param)
        if page < 1:
            raise ValueError('Номер сторінки "page" має бути >= 1.')
        if per_page < 1 or per_page > 50:
            raise ValueError('Параметр "per_page" має бути в діапазоні від 1 до 50.')
    except ValueError as e:
        return jsonify({
            'error': f'Помилка валідації параметрів пагінації: {str(e)}',
            'status': 400
        }), 400

    rows = models.get_all_products(category=category)
    products = [row_to_dict(r) for r in rows]

    # Сортування
    if sort == 'price_asc':
        products.sort(key=lambda x: x['price'])
    elif sort == 'price_desc':
        products.sort(key=lambda x: x['price'], reverse=True)
    elif sort == 'name_asc':
        products.sort(key=lambda x: x['name'].lower())
    elif sort == 'newest':
        products.sort(key=lambda x: x['id'], reverse=True)

    total_items = len(products)
    total_pages = max(1, math.ceil(total_items / per_page)) if total_items > 0 else 1

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_items = products[start_idx:end_idx]

    return jsonify({
        'version': 'v2',
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'items': page_items
    }), 200


# =======================================================
# РІВЕНЬ 3: API v2 ДЛЯ ЗАМОВЛЕНЬ (СТАТИСТИКА ТА ПАГІНАЦІЯ) - Частина 2
# =======================================================

@api_v2_bp.route('/orders/stats', methods=['GET'])
def get_orders_stats_v2():
    """[API v2] Отримати агреговану статистику та аналітику замовлень
    ---
    tags:
      - Orders (API v2 - Рівень 3)
    responses:
      200:
        description: Зведена статистика замовлень магазину
        schema:
          type: object
          properties:
            version:
              type: string
              example: "v2"
            total_orders:
              type: integer
              example: 15
            total_revenue:
              type: number
              example: 48500.5
            average_order_value:
              type: number
              example: 3233.37
            by_status:
              type: object
              example:
                "Нове": 5
                "В обробці": 4
                "Відправлено": 3
                "Доставлено": 2
                "Скасовано": 1
    """
    orders = [row_to_dict(r) for r in models.get_all_orders()]
    total_orders = len(orders)
    total_revenue = sum(o['total_price'] for o in orders)
    avg_order = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    status_counts = {}
    for o in orders:
        st = o['status']
        status_counts[st] = status_counts.get(st, 0) + 1

    return jsonify({
        'version': 'v2',
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'average_order_value': avg_order,
        'by_status': status_counts
    }), 200


@api_v2_bp.route('/orders', methods=['GET'])
def get_orders_v2():
    """[API v2] Список замовлень із підтримкою пагінації, фільтрації та сортування
    ---
    tags:
      - Orders (API v2 - Рівень 3)
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Номер сторінки
      - name: per_page
        in: query
        type: integer
        required: false
        default: 5
        description: Кількість замовлень на сторінці (1-50)
      - name: status
        in: query
        type: string
        required: false
        description: Фільтрація за статусом
      - name: sort
        in: query
        type: string
        required: false
        enum: [newest, oldest, total_asc, total_desc]
        default: newest
        description: Сортування результатів
    responses:
      200:
        description: Список замовлень у форматі конверта (envelope)
      400:
        description: Некоректні параметри пагінації
    """
    page_param = request.args.get('page', '1')
    per_page_param = request.args.get('per_page', '5')
    status = request.args.get('status')
    sort = request.args.get('sort', 'newest')

    try:
        page = int(page_param)
        per_page = int(per_page_param)
        if page < 1:
            raise ValueError('Номер сторінки "page" має бути >= 1.')
        if per_page < 1 or per_page > 50:
            raise ValueError('Параметр "per_page" має бути від 1 до 50.')
    except ValueError as e:
        return jsonify({
            'error': f'Помилка валідації параметрів пагінації: {str(e)}',
            'status': 400
        }), 400

    rows = models.get_all_orders()
    orders = [row_to_dict(r) for r in rows]

    if status:
        orders = [o for o in orders if o.get('status') == status]

    if sort == 'total_asc':
        orders.sort(key=lambda x: x['total_price'])
    elif sort == 'total_desc':
        orders.sort(key=lambda x: x['total_price'], reverse=True)
    elif sort == 'oldest':
        orders.sort(key=lambda x: x['id'])
    elif sort == 'newest':
        orders.sort(key=lambda x: x['id'], reverse=True)

    total_items = len(orders)
    total_pages = max(1, math.ceil(total_items / per_page)) if total_items > 0 else 1

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_items = orders[start_idx:end_idx]

    return jsonify({
        'version': 'v2',
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'items': page_items
    }), 200
