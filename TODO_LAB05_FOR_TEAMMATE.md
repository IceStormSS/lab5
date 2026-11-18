# 📋 Інструкція для напарника: Реалізація Частини 2 (50%) — Лабораторна робота №5 (REST API)

Привіт! Першу половину лабораторної роботи №5 (50%) вже **повністю реалізовано та протестовано**:
1. **Архітектурна основа:**
   - Налаштовано модульні Blueprint-и API: `/api/v1` (`routes/api_v1.py`) та `/api/v2` (`routes/api_v2.py`).
   - Реалізовано централізовані глобальні обробники помилок у форматі JSON (`400 Bad Request`, `404 Not Found`, `405 Method Not Allowed`, `500 Server Error`).
2. **Рівень 1 (Базовий REST API):**
   - Реалізовано повний CRUD для **Товарів** (`/api/v1/products` — GET, GET by ID, POST, PUT, DELETE).
   - Реалізовано роботу з **Відгуками** (`/api/v1/feedbacks` — GET, POST).
3. **Рівень 2 (Документація Swagger UI):**
   - Підключено та налаштовано бібліотеку `flasgger`.
   - Інтерактивна сторінка доступна за адресою: `http://127.0.0.1:5000/apidocs/`.
4. **Рівень 3 (Версіонування та валідація):**
   - Реалізовано валідацію вхідних даних для методів POST/PUT.
   - Реалізовано ендпоінт версії v2 з пагінацією та сортуванням (`/api/v2/products`).
5. **Тестування:**
   - Створено колекцію запитів для Postman / Bruno: `postman_collection.json`.
   - Написано автоматичний набір тестів: `test_api.py` (запуск: `python test_api.py`).

---

## 🎯 Твоє завдання на 50% (Частина 2):

Тобі потрібно розширити наш REST API бізнес-логікою **Замовлень (Orders)**, **Промокодів (Coupons)**, **Клієнтів (Customers)** та додати версію v2 для замовлень.

Усі необхідні функції для роботи з базою даних SQLite **вже є в `models.py`** (`get_all_orders`, `get_order_details`, `create_order`, `update_order_status`, `get_coupon`, `get_all_customers` тощо).

---

### Крок 1. Реалізувати ендпоінти Замовлень у `routes/api_v1.py`

Відкрий файл `routes/api_v1.py` та додай наступні маршрути (замінивши або розширивши наявні заготовки):

#### 1. `GET /api/v1/orders/<int:order_id>` — Деталі замовлення
Повертає інформацію про замовлення та перелік замовлених товарів:
```python
@api_v1_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order_by_id_endpoint(order_id):
    """Отримати деталі конкретного замовлення з переліком куплених позицій
    ---
    tags:
      - Orders (Частина 2 - Для напарника)
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Дані замовлення та позиції order_items
      404:
        description: Замовлення не знайдено
    """
    order, items = models.get_order_details(order_id)
    if not order:
        return jsonify({'error': f'Замовлення #{order_id} не знайдено', 'status': 404}), 404
    
    order_dict = row_to_dict(order)
    order_dict['items'] = [row_to_dict(item) for item in items]
    return jsonify(order_dict), 200
```

#### 2. `POST /api/v1/orders` — Створення замовлення (з валідацією, Рівень 3)
Приймає JSON із даними клієнта, масивом товарів та опціональним промокодом:
```python
@api_v1_bp.route('/orders', methods=['POST'])
def create_order_endpoint():
    """Створити нове замовлення через REST API
    ---
    tags:
      - Orders (Частина 2 - Для напарника)
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

    if errors:
        return jsonify({'error': 'Помилка валідації замовлення', 'details': errors, 'status': 400}), 400

    order_id = models.create_order(
        name=name.strip(),
        phone=phone.strip(),
        address=address.strip(),
        items=items,
        coupon_code=coupon_code.strip() if coupon_code else None
    )

    created_order, order_items = models.get_order_details(order_id)
    result = row_to_dict(created_order)
    result['items'] = [row_to_dict(i) for i in order_items]
    return jsonify(result), 201
```

#### 3. `PATCH /api/v1/orders/<int:order_id>/status` — Оновлення статусу
```python
@api_v1_bp.route('/orders/<int:order_id>/status', methods=['PATCH'])
def update_status_endpoint(order_id):
    """Оновити статус замовлення (наприклад, 'В обробці', 'Відправлено', 'Доставлено', 'Скасовано')
    ---
    tags:
      - Orders (Частина 2 - Для напарника)
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
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
```

---

### Крок 2. Реалізувати перевірку промокодів і список клієнтів

#### 1. `POST /api/v1/coupons/validate` — Валідація промокоду
```python
@api_v1_bp.route('/coupons/validate', methods=['POST'])
def validate_coupon_endpoint():
    """Перевірити валідність промокоду на знижку
    ---
    tags:
      - Coupons (Частина 2 - Для напарника)
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
    if not code:
        return jsonify({'error': 'Поле "code" обов\'язкове', 'status': 400}), 400

    coupon = models.get_coupon(code)
    if not coupon:
        return jsonify({'valid': False, 'message': 'Промокод недійсний або не існує'}), 200

    return jsonify({
        'valid': True,
        'code': coupon['code'],
        'discount_percent': coupon['discount_percent']
    }), 200
```

#### 2. `GET /api/v1/customers` — Список зареєстрованих клієнтів
```python
@api_v1_bp.route('/customers', methods=['GET'])
def get_customers_endpoint():
    """Отримати список усіх клієнтів
    ---
    tags:
      - Customers (Частина 2 - Для напарника)
    responses:
      200:
        description: Список клієнтів
    """
    rows = models.get_all_customers()
    return jsonify([row_to_dict(r) for r in rows]), 200
```

---

### Крок 3. Додати версію API v2 для замовлень у `routes/api_v2.py`

У файл `routes/api_v2.py` додай аналітичний ендпоінт або пагінацію для замовлень:
```python
@api_v2_bp.route('/orders/stats', methods=['GET'])
def get_orders_stats_v2():
    """[API v2] Отримати агреговану статистику замовлень
    ---
    tags:
      - Orders (API v2 - Рівень 3)
    responses:
      200:
        description: Статистика замовлень (кількість, сума виручки, розподіл за статусами)
    """
    orders = [row_to_dict(r) for r in models.get_all_orders()]
    total_revenue = sum(o['total_price'] for o in orders)
    status_counts = {}
    for o in orders:
        st = o['status']
        status_counts[st] = status_counts.get(st, 0) + 1

    return jsonify({
        'version': 'v2',
        'total_orders': len(orders),
        'total_revenue': round(total_revenue, 2),
        'by_status': status_counts
    }), 200
```

---

### Крок 4. Тестування та звіт

1. **Запуск сервера:**
   Запусти `run.bat` або виконай `python app.py`.
2. **Перевірка документації Swagger:**
   Відкрий у браузері `http://127.0.0.1:5000/apidocs/` — твої нові ендпоінти автоматично з'являться у Swagger UI з можливістю протестувати їх кнопкою "Try it out".
3. **Postman / Bruno:**
   Імпортуй файл `postman_collection.json`, створи папку для своїх ендпоінтів Orders / Coupons, додай тести та зроби скріншоти відповідей (успішної `200/201` та помилки `400/404`).
4. **Звіт:**
   Заповни свій звіт у `lab-reports/lab05-report-part2.md` на основі виконаної роботи.
