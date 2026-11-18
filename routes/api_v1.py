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
# 3. ЗАМОВЛЕННЯ (ORDERS API) - Частина 2
# =====================================================================

@api_v1_bp.route('/orders', methods=['GET'])
def get_orders():
    """Отримати список усіх замовлень із можливістю фільтрації
    ---
    tags:
      - Orders (Частина 2 - Замовлення)
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
        description: Список замовлень
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              customer_id:
                type: integer
                example: 1
              customer_name:
                type: string
                example: Марія Шевченко
              customer_phone:
                type: string
                example: "+380671234567"
              customer_address:
                type: string
                example: м. Київ, вул. Хрещатик, 10
              status:
                type: string
                example: Нове
              total_price:
                type: number
                example: 4680.0
              coupon_code:
                type: string
                example: SALE10
              discount_amount:
                type: number
                example: 520.0
              created_at:
                type: string
                example: "2026-11-18 20:15:00"
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


@api_v1_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order_by_id_endpoint(order_id):
    """Отримати деталі конкретного замовлення з переліком куплених позицій
    ---
    tags:
      - Orders (Частина 2 - Замовлення)
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: Унікальний ідентифікатор замовлення
    responses:
      200:
        description: Дані замовлення та позиції order_items
      404:
        description: Замовлення не знайдено
        schema:
          type: object
          properties:
            error:
              type: string
              example: Замовлення #999 не знайдено
            status:
              type: integer
              example: 404
    """
    order, items = models.get_order_details(order_id)
    if not order:
        return jsonify({'error': f'Замовлення #{order_id} не знайдено', 'status': 404}), 404

    order_dict = row_to_dict(order)
    order_dict['items'] = [row_to_dict(item) for item in items]
    return jsonify(order_dict), 200


@api_v1_bp.route('/orders', methods=['POST'])
def create_order_endpoint():
    """Створити нове замовлення через REST API (з валідацією даних)
    ---
    tags:
      - Orders (Частина 2 - Замовлення)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - phone
            - address
            - items
          properties:
            name:
              type: string
              example: Марія Шевченко
            phone:
              type: string
              example: "+380671234567"
            address:
              type: string
              example: м. Київ, вул. Хрещатик, 10
            coupon_code:
              type: string
              example: SALE10
            items:
              type: array
              items:
                type: object
                required:
                  - product_id
                  - quantity
                  - price
                properties:
                  product_id:
                    type: integer
                    example: 1
                  quantity:
                    type: integer
                    example: 2
                  price:
                    type: number
                    example: 3200.0
    responses:
      201:
        description: Замовлення успішно створено
      400:
        description: Помилка валідації вхідних даних
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Очікується тіло запиту у форматі JSON', 'status': 400}), 400

    name = data.get('name')
    phone = data.get('phone')
    address = data.get('address')
    items = data.get('items')
    coupon_code = data.get('coupon_code')

    errors = []
    if not name or not isinstance(name, str) or len(name.strip()) < 2:
        errors.append('Поле "name" має містити щонайменше 2 символи.')
    if not phone or not isinstance(phone, str) or len(phone.strip()) < 7:
        errors.append('Поле "phone" обов\'язкове (мінімум 7 символів).')
    if not address or not isinstance(address, str) or len(address.strip()) < 5:
        errors.append('Поле "address" обов\'язкове (мінімум 5 символів).')
    if not items or not isinstance(items, list) or len(items) == 0:
        errors.append('Список "items" має містити хоча б один товар.')
    else:
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f'Позиція #{idx+1} у списку items має бути об\'єктом.')
                continue
            if 'product_id' not in item or not isinstance(item['product_id'], int):
                errors.append(f'Позиція #{idx+1}: "product_id" має бути цілим числом.')
            if 'quantity' not in item or not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                errors.append(f'Позиція #{idx+1}: "quantity" має бути додатним цілим числом.')
            if 'price' not in item or not isinstance(item['price'], (int, float)) or float(item['price']) <= 0:
                errors.append(f'Позиція #{idx+1}: "price" має бути додатним числом.')

    if errors:
        return jsonify({'error': 'Помилка валідації замовлення', 'details': errors, 'status': 400}), 400

    order_id = models.create_order(
        name=name.strip(),
        phone=phone.strip(),
        address=address.strip(),
        items=items,
        coupon_code=coupon_code.strip() if coupon_code and isinstance(coupon_code, str) else None
    )

    created_order, order_items = models.get_order_details(order_id)
    result = row_to_dict(created_order)
    result['items'] = [row_to_dict(i) for i in order_items]
    return jsonify(result), 201


@api_v1_bp.route('/orders/<int:order_id>/status', methods=['PATCH'])
def update_status_endpoint(order_id):
    """Оновити статус замовлення ('Нове', 'В обробці', 'Відправлено', 'Доставлено', 'Скасовано')
    ---
    tags:
      - Orders (Частина 2 - Замовлення)
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: ID замовлення
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              example: В обробці
    responses:
      200:
        description: Статус успішно оновлено
      400:
        description: Некоректний статус
      404:
        description: Замовлення не знайдено
    """
    order = models.get_order_by_id(order_id)
    if not order:
        return jsonify({'error': f'Замовлення #{order_id} не знайдено', 'status': 404}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    valid_statuses = ['Нове', 'В обробці', 'Відправлено', 'Доставлено', 'Скасовано']
    if not new_status or new_status not in valid_statuses:
        return jsonify({
            'error': f'Некоректний статус. Дозволені: {valid_statuses}',
            'status': 400
        }), 400

    models.update_order_status(order_id, new_status)
    return jsonify({'id': order_id, 'status': new_status, 'message': 'Статус оновлено'}), 200


@api_v1_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order_endpoint(order_id):
    """Видалити замовлення за його ID
    ---
    tags:
      - Orders (Частина 2 - Замовлення)
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: ID замовлення для видалення
    responses:
      204:
        description: Замовлення успішно видалено (без тіла)
      404:
        description: Замовлення не знайдено
    """
    order = models.get_order_by_id(order_id)
    if not order:
        return jsonify({'error': f'Замовлення #{order_id} не знайдено', 'status': 404}), 404

    models.delete_order(order_id)
    return '', 204


# =====================================================================
# 4. ПРОМОКОДИ ТА КЛІЄНТИ (COUPONS & CUSTOMERS API) - Частина 2
# =====================================================================

@api_v1_bp.route('/coupons', methods=['GET'])
def get_coupons():
    """Отримати список усіх діючих промокодів
    ---
    tags:
      - Coupons (Частина 2 - Промокоди)
    responses:
      200:
        description: Список промокодів зі знижками
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              code:
                type: string
                example: SALE10
              discount_percent:
                type: integer
                example: 10
              created_at:
                type: string
                example: "2026-11-18 20:00:00"
    """
    rows = models.get_all_coupons()
    return jsonify([row_to_dict(r) for r in rows]), 200


@api_v1_bp.route('/coupons/validate', methods=['POST'])
def validate_coupon_endpoint():
    """Перевірити валідність промокоду на знижку
    ---
    tags:
      - Coupons (Частина 2 - Промокоди)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - code
          properties:
            code:
              type: string
              example: SALE10
    responses:
      200:
        description: Результат перевірки промокоду
      400:
        description: Код промокоду не передано
    """
    data = request.get_json(silent=True) or {}
    code = data.get('code')
    if not code or not isinstance(code, str) or not code.strip():
        return jsonify({'error': 'Поле "code" обов\'язкове', 'status': 400}), 400

    coupon = models.get_coupon(code.strip())
    if not coupon:
        return jsonify({'valid': False, 'message': 'Промокод недійсний або не існує'}), 200

    return jsonify({
        'valid': True,
        'code': coupon['code'],
        'discount_percent': coupon['discount_percent']
    }), 200


@api_v1_bp.route('/customers', methods=['GET'])
def get_customers_endpoint():
    """Отримати список зареєстрованих клієнтів магазину
    ---
    tags:
      - Customers (Частина 2 - Клієнти)
    responses:
      200:
        description: Список клієнтів
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
                example: Олександр Коваленко
              email:
                type: string
                example: oleksandr@example.com
              phone:
                type: string
                example: "+380501234567"
              address:
                type: string
                example: "м. Київ, вул. Хрещатик, 1"
              created_at:
                type: string
                example: "2026-11-18 20:00:00"
    """
    rows = models.get_all_customers()
    return jsonify([row_to_dict(r) for r in rows]), 200
