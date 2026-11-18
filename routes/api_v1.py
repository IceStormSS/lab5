import re
from flask import Blueprint, request, jsonify
import models

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

def row_to_dict(row):
    """Допоміжна функція конвертації рядка sqlite3.Row у звичайний dict."""
    if row is None:
        return None
    return dict(row)

# ==========================================
# 1. ТОВАРИ (PRODUCTS API) - Частина 1
# ==========================================

@api_v1_bp.route('/products', methods=['GET'])
def get_products():
    """Отримати список товарів з можливістю фільтрації та пошуку
    ---
    tags:
      - Products (Частина 1)
    parameters:
      - name: category
        in: query
        type: string
        required: false
        description: Фільтрація за категорією (наприклад, 'Куртки', 'Пальта')
      - name: search
        in: query
        type: string
        required: false
        description: Пошук за назвою або описом
      - name: min_price
        in: query
        type: number
        required: false
        description: Мінімальна ціна товару
      - name: max_price
        in: query
        type: number
        required: false
        description: Максимальна ціна товару
    responses:
      200:
        description: Список знайдених товарів
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              name:
                type: string
                example: Зимова куртка-пуховик
              category:
                type: string
                example: Куртки
              price:
                type: number
                example: 3200.0
              description:
                type: string
                example: Теплий пуховик з водовідштовхувальної тканини.
              created_at:
                type: string
                example: "2026-11-18 20:00:00"
    """
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    rows = models.get_all_products(category=category, search=search)
    products = [row_to_dict(r) for r in rows]

    # Додаткова фільтрація за ціною, якщо вказана
    if min_price is not None:
        products = [p for p in products if p['price'] >= min_price]
    if max_price is not None:
        products = [p for p in products if p['price'] <= max_price]

    return jsonify(products), 200


@api_v1_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Отримати деталі конкретного товару за його ID
    ---
    tags:
      - Products (Частина 1)
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: Унікальний ідентифікатор товару
    responses:
      200:
        description: Дані товару успішно знайдено
      404:
        description: Товар з вказаним ID не знайдено
        schema:
          type: object
          properties:
            error:
              type: string
              example: Товар з ID 999 не знайдено
            status:
              type: integer
              example: 404
    """
    row = models.get_product_by_id(product_id)
    if row is None:
        return jsonify({
            'error': f'Товар з ID {product_id} не знайдено',
            'status': 404
        }), 404
    return jsonify(row_to_dict(row)), 200


@api_v1_bp.route('/products', methods=['POST'])
def create_product():
    """Створити новий товар (з валідацією полів)
    ---
    tags:
      - Products (Частина 1)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - category
            - price
          properties:
            name:
              type: string
              example: Парка демісезонна
            category:
              type: string
              example: Парки
            price:
              type: number
              example: 2800.0
            description:
              type: string
              example: Зручна стильна парка з капюшоном.
    responses:
      201:
        description: Товар успішно створено
      400:
        description: Помилка валідації вхідних даних
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            'error': 'Некоректне тіло запиту. Очікується JSON-об\'єкт',
            'status': 400
        }), 400

    errors = []
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')
    description = data.get('description', '')

    # Рівень 3: валідація полів
    if not name or not isinstance(name, str) or not name.strip():
        errors.append('Поле "name" обов\'язкове і має бути непорожнім рядком.')
    elif len(name.strip()) < 2:
        errors.append('Поле "name" має містити щонайменше 2 символи.')

    if not category or not isinstance(category, str) or not category.strip():
        errors.append('Поле "category" обов\'язкове і має бути непорожнім рядком.')

    if price is None:
        errors.append('Поле "price" обов\'язкове.')
    else:
        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append('Поле "price" має бути додатним числом більше 0.')
            price = price_val
        except (ValueError, TypeError):
            errors.append('Поле "price" має бути коректним числом.')

    if errors:
        return jsonify({
            'error': 'Помилка валідації вхідних даних',
            'details': errors,
            'status': 400
        }), 400

    new_id = models.add_product(
        name=name.strip(),
        category=category.strip(),
        price=price,
        description=description.strip() if isinstance(description, str) else ''
    )

    created_product = row_to_dict(models.get_product_by_id(new_id))
    return jsonify(created_product), 201


@api_v1_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product_endpoint(product_id):
    """Повне оновлення існуючого товару
    ---
    tags:
      - Products (Частина 1)
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID товару для оновлення
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - category
            - price
          properties:
            name:
              type: string
              example: Оновлена куртка
            category:
              type: string
              example: Куртки
            price:
              type: number
              example: 3500.0
            description:
              type: string
              example: Оновлений опис товару.
    responses:
      200:
        description: Товар успішно оновлено
      400:
        description: Некоректні дані
      404:
        description: Товар не знайдено
    """
    existing = models.get_product_by_id(product_id)
    if not existing:
        return jsonify({
            'error': f'Товар з ID {product_id} не знайдено',
            'status': 404
        }), 404

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            'error': 'Некоректне тіло запиту. Очікується JSON-об\'єкт',
            'status': 400
        }), 400

    errors = []
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')
    description = data.get('description', '')

    if not name or not isinstance(name, str) or not name.strip():
        errors.append('Поле "name" обов\'язкове.')
    if not category or not isinstance(category, str) or not category.strip():
        errors.append('Поле "category" обов\'язкове.')
    if price is None:
        errors.append('Поле "price" обов\'язкове.')
    else:
        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append('Поле "price" має бути додатним числом.')
            price = price_val
        except (ValueError, TypeError):
            errors.append('Поле "price" має бути числом.')

    if errors:
        return jsonify({
            'error': 'Помилка валідації вхідних даних',
            'details': errors,
            'status': 400
        }), 400

    models.update_product(
        product_id=product_id,
        name=name.strip(),
        category=category.strip(),
        price=price,
        description=description.strip() if isinstance(description, str) else ''
    )

    updated = row_to_dict(models.get_product_by_id(product_id))
    return jsonify(updated), 200


@api_v1_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product_endpoint(product_id):
    """Видалити товар за його ID
    ---
    tags:
      - Products (Частина 1)
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID товару для видалення
    responses:
      204:
        description: Товар успішно видалено (тіло відповіді порожнє)
      404:
        description: Товар не знайдено
    """
    existing = models.get_product_by_id(product_id)
    if not existing:
        return jsonify({
            'error': f'Товар з ID {product_id} не знайдено',
            'status': 404
        }), 404

    models.delete_product(product_id)
    return '', 204


# ==========================================
# 2. ВІДГУКИ (FEEDBACKS API) - Частина 1
# ==========================================

@api_v1_bp.route('/feedbacks', methods=['GET'])
def get_feedbacks():
    """Отримати список усіх відгуків
    ---
    tags:
      - Feedbacks (Частина 1)
    responses:
      200:
        description: Список усіх відгуків покупців
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              name:
                type: string
                example: Марія Шевченко
              email:
                type: string
                example: maria@example.com
              message:
                type: string
                example: Чудовий магазин!
              created_at:
                type: string
                example: "2026-11-18 20:00:00"
    """
    rows = models.get_all_feedbacks()
    feedbacks = [row_to_dict(r) for r in rows]
    return jsonify(feedbacks), 200


@api_v1_bp.route('/feedbacks', methods=['POST'])
def create_feedback():
    """Залишити новий відгук (з валідацією імені, email та повідомлення)
    ---
    tags:
      - Feedbacks (Частина 1)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - message
          properties:
            name:
              type: string
              example: Іван Петренко
            email:
              type: string
              example: ivan@example.com
            message:
              type: string
              example: Дуже задоволений швидкою доставкою куртки!
    responses:
      201:
        description: Відгук успішно додано
      400:
        description: Помилка валідації полів
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            'error': 'Некоректне тіло запиту. Очікується JSON-об\'єкт',
            'status': 400
        }), 400

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    errors = []
    if not name or not isinstance(name, str) or len(name.strip()) < 2:
        errors.append('Поле "name" має містити щонайменше 2 символи.')

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not email or not isinstance(email, str) or not re.match(email_regex, email.strip()):
        errors.append('Поле "email" має містити коректну адресу електронної пошти.')

    if not message or not isinstance(message, str) or len(message.strip()) < 5:
        errors.append('Поле "message" має містити щонайменше 5 символів.')

    if errors:
        return jsonify({
            'error': 'Помилка валідації вхідних даних',
            'details': errors,
            'status': 400
        }), 400

    models.add_feedback(name.strip(), email.strip(), message.strip())

    # Повертаємо останній доданий відгук
    recent = models.get_all_feedbacks()[0]
    return jsonify(row_to_dict(recent)), 201


# =====================================================================
# 3. ЗАМОВЛЕННЯ ТА ПРОМОКОДИ (СТУБИ / ПЛАН ДЛЯ НАПАРНИКА - Частина 2)
# =====================================================================

@api_v1_bp.route('/orders', methods=['GET'])
def get_orders_placeholder():
    """[Частина 2: Для напарника] Отримати список усіх замовлень
    ---
    tags:
      - Orders (Частина 2 - Для напарника)
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: Фільтрація за статусом ('Нове', 'В обробці', 'Відправлено', 'Доставлено', 'Скасовано')
      - name: phone
        in: query
        type: string
        required: false
        description: Пошук за номером телефону клієнта
    responses:
      200:
        description: Список усіх замовлень магазину
    """
    status = request.args.get('status')
    phone = request.args.get('phone')

    if phone:
        rows = models.get_orders_by_phone(phone)
    else:
        rows = models.get_all_orders()

    orders = [row_to_dict(r) for r in rows]
    if status:
        orders = [o for o in orders if o.get('status') == status]

    return jsonify(orders), 200


@api_v1_bp.route('/coupons', methods=['GET'])
def get_coupons_placeholder():
    """[Частина 2: Для напарника] Отримати список діючих промокодів
    ---
    tags:
      - Coupons (Частина 2 - Для напарника)
    responses:
      200:
        description: Список промокодів зі знижками
    """
    rows = models.get_all_coupons()
    return jsonify([row_to_dict(r) for r in rows]), 200
