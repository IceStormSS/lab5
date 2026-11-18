import sqlite3
from flask import g, current_app

def get_db():
    """Отримує з'єднання з базою даних для поточного контексту запиту."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        # Обов'язково вмикаємо перевірку зовнішніх ключів для SQLite
        g.db.execute('PRAGMA foreign_keys = ON;')
    return g.db

def close_db(e=None):
    """Закриває з'єднання з базою даних після завершення запиту."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """Ініціалізує таблиці бази даних та заповнює початковими даними."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # 1. Таблиця відгуків (Рівень 1)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 2. Таблиця товарів (Рівень 1)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 3. Таблиця клієнтів (Рівень 2 - Предметна область магазину)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 4. Таблиця замовлень (Частина 2 - Реалізація напарника)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_address TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Нове',
                total_price REAL NOT NULL,
                coupon_code TEXT,
                discount_amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
            );
        ''')

        # 5. Таблиця зв'язку замовлень і товарів (Many-to-Many)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
        ''')

        # 6. Таблиця промокодів (Рівень 3 - Додаткова функція №2)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                discount_percent INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Заповнення початковими товарами, якщо таблиця пуста
        cursor.execute('SELECT COUNT(*) FROM products;')
        if cursor.fetchone()[0] == 0:
            initial_products = [
                ('Зимова куртка-пуховик', 'Куртки', 3200, 'Теплий пуховик з водовідштовхувальної тканини.'),
                ('Демісезонна куртка', 'Куртки', 2400, 'Зручна вітрозахисна куртка на весну та осінь.'),
                ('Шкіряна куртка', 'Куртки', 5800, 'Стильна куртка з натуральної шкіри.'),
                ('Джинсова куртка', 'Куртки', 1900, 'Класична джинсовка з міцного деніму.'),
                ('Бомбер', 'Куртки', 2100, 'Молодіжний легкий бомбер на блискавці.'),
                ('Класичне пальто', 'Пальта', 4500, 'Елегантне двобортне пальто прямого крою.'),
                ('Вовняне пальто оверсайз', 'Пальта', 5200, 'Тепле затишне пальто з натуральної вовни.'),
                ('Тренч', 'Пальта', 3900, 'Класичний бежевий тренчкот.'),
                ('Пальто-кокон', 'Пальта', 4800, 'Об\'ємне пальто вільного силуету.'),
                ('Вітровка', 'Легкий верхній одяг', 1800, 'Ультралегка вітровка для пробіжок та прогулянок.'),
                ('Дощовик', 'Легкий верхній одяг', 1500, 'Непромокальний стильний плащ-дощовик.'),
                ('Софтшелл', 'Легкий верхній одяг', 2300, 'Функціональна мембранна куртка.'),
                ('Жилет утеплений', 'Жилети', 1700, 'Зручний жилет на синтепоні для прохолодних днів.'),
                ('Жилет пуховий', 'Жилети', 2000, 'Легкий та теплий жилет з пуховим наповнювачем.'),
                ('Парка з капюшоном', 'Парки', 4100, 'Подовжена куртка-парка з глибоким капюшоном.'),
                ('Парка зимова з хутром', 'Парки', 4900, 'Зимова утеплена парка з натуральним хутром.'),
                ('Анорак', 'Парки', 2600, 'Куртка-анорак з великою кишенею-кенгуру.'),
                ('Дублянка', 'Зимовий одяг', 7500, 'Тепла натуральна дублянка високої якості.'),
                ('Шуба штучна', 'Зимовий одяг', 6200, 'Модна еко-шуба з м\'якого штучного хутра.'),
                ('Куртка гірськолижна', 'Спортивний одяг', 5400, 'Професійна гірськолижна куртка зі снігозахистом.')
            ]
            cursor.executemany(
                'INSERT INTO products (name, category, price, description) VALUES (?, ?, ?, ?)',
                initial_products
            )

        # Заповнення тестовими клієнтами, якщо таблиця пуста
        cursor.execute('SELECT COUNT(*) FROM customers;')
        if cursor.fetchone()[0] == 0:
            initial_customers = [
                ('Олександр Коваленко', 'oleksandr@example.com', '+380501234567', 'м. Київ, вул. Хрещатик, 1'),
                ('Марія Шевченко', 'maria@example.com', '+380679876543', 'м. Львів, вул. Городоцька, 15'),
                ('Іван Бондаренко', 'ivan@example.com', '+380931112233', 'м. Одеса, вул. Дерибасівська, 8')
            ]
            cursor.executemany(
                'INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)',
                initial_customers
            )

        # Заповнення тестовим відгуком, якщо таблиця пуста
        cursor.execute('SELECT COUNT(*) FROM feedbacks;')
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO feedbacks (name, email, message) VALUES (?, ?, ?)',
                ('Марія Шевченко', 'maria@example.com', 'Чудовий магазин! Замовляла пальто оверсайз — якість перевершила очікування!')
            )

        # Заповнення початковими промокодами (Рівень 3)
        cursor.execute('SELECT COUNT(*) FROM coupons;')
        if cursor.fetchone()[0] == 0:
            initial_coupons = [
                ('SALE10', 10),
                ('WARM20', 20),
                ('WINTER15', 15),
                ('VIP30', 30)
            ]
            cursor.executemany(
                'INSERT INTO coupons (code, discount_percent) VALUES (?, ?)',
                initial_coupons
            )

        # Заповнення тестовими замовленнями (Частина 2)
        cursor.execute('SELECT COUNT(*) FROM orders;')
        if cursor.fetchone()[0] == 0:
            # Замовлення 1: Олександр Коваленко
            cursor.execute('''
                INSERT INTO orders (customer_id, customer_name, customer_phone, customer_address, status, total_price, coupon_code, discount_amount)
                VALUES (1, 'Олександр Коваленко', '+380501234567', 'м. Київ, вул. Хрещатик, 1', 'В обробці', 3200.0, NULL, 0);
            ''')
            order_id_1 = cursor.lastrowid
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, 1, 1, 3200.0);
            ''', (order_id_1,))

            # Замовлення 2: Марія Шевченко (зі знижкою за промокодом SALE10)
            cursor.execute('''
                INSERT INTO orders (customer_id, customer_name, customer_phone, customer_address, status, total_price, coupon_code, discount_amount)
                VALUES (2, 'Марія Шевченко', '+380679876543', 'м. Львів, вул. Городоцька, 15', 'Нове', 4680.0, 'SALE10', 520.0);
            ''')
            order_id_2 = cursor.lastrowid
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, 7, 1, 5200.0);
            ''', (order_id_2,))

        db.commit()

# --- ФУНКЦІЇ ДЛЯ РОБОТИ З ВІДГУКАМИ (FEEDBACK CRUD) ---
def get_all_feedbacks():
    db = get_db()
    return db.execute('SELECT * FROM feedbacks ORDER BY created_at DESC;').fetchall()

def add_feedback(name, email, message):
    db = get_db()
    db.execute(
        'INSERT INTO feedbacks (name, email, message) VALUES (?, ?, ?);',
        (name, email, message)
    )
    db.commit()

def delete_feedback(feedback_id):
    db = get_db()
    db.execute('DELETE FROM feedbacks WHERE id = ?;', (feedback_id,))
    db.commit()

# --- ФУНКЦІЇ ДЛЯ РОБОТИ З ТОВАРАМИ (PRODUCTS CRUD) ---
def get_all_products(category=None, search=None):
    db = get_db()
    query = 'SELECT * FROM products WHERE 1=1'
    params = []

    if category and category != 'all':
        query += ' AND category = ?'
        params.append(category)

    if search:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        search_pattern = f'%{search}%'
        params.extend([search_pattern, search_pattern])

    query += ' ORDER BY id DESC;'
    return db.execute(query, params).fetchall()

def get_product_by_id(product_id):
    db = get_db()
    return db.execute('SELECT * FROM products WHERE id = ?;', (product_id,)).fetchone()

def add_product(name, category, price, description):
    db = get_db()
    cursor = db.execute(
        'INSERT INTO products (name, category, price, description) VALUES (?, ?, ?, ?);',
        (name, category, price, description)
    )
    db.commit()
    return cursor.lastrowid

def update_product(product_id, name, category, price, description):
    db = get_db()
    cursor = db.execute(
        'UPDATE products SET name = ?, category = ?, price = ?, description = ? WHERE id = ?;',
        (name, category, price, description, product_id)
    )
    db.commit()
    return cursor.rowcount > 0

def delete_product(product_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?;', (product_id,))
    db.commit()

def get_categories():
    db = get_db()
    rows = db.execute('SELECT DISTINCT category FROM products ORDER BY category;').fetchall()
    return [row['category'] for row in rows]

# --- ФУНКЦІЇ ДЛЯ РОБОТИ З КЛІЄНТАМИ (CUSTOMERS - Рівень 2) ---
def get_all_customers():
    db = get_db()
    return db.execute('SELECT * FROM customers ORDER BY created_at DESC;').fetchall()

def add_customer(name, email, phone, address):
    db = get_db()
    cursor = db.execute(
        'INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?);',
        (name, email, phone, address)
    )
    db.commit()
    return cursor.lastrowid

def delete_customer(customer_id):
    db = get_db()
    db.execute('DELETE FROM customers WHERE id = ?;', (customer_id,))
    db.commit()

# --- ФУНКЦІЇ ДЛЯ РОБОТИ ІЗ ЗАМОВЛЕННЯМИ (ORDERS & ORDER_ITEMS - Частина 2) ---
def create_order(name, phone, address, items, coupon_code=None, customer_id=None):
    """
    Створює нове замовлення, розраховує підсумкову вартість з урахуванням промокоду,
    зберігає зв'язані позиції в order_items (Many-to-Many) та фіксує транзакцію.
    items: список словників [{'product_id': int, 'quantity': int, 'price': float}]
    """
    db = get_db()
    cursor = db.cursor()

    # Спроба зв'язати з наявним клієнтом за телефоном, якщо customer_id не передано явно
    if not customer_id and phone:
        cust = db.execute('SELECT id FROM customers WHERE phone = ?;', (phone.strip(),)).fetchone()
        if cust:
            customer_id = cust['id']

    raw_total = sum(float(item['price']) * int(item['quantity']) for item in items)
    discount_amount = 0.0
    applied_coupon = None

    if coupon_code:
        coupon = get_coupon(coupon_code)
        if coupon:
            applied_coupon = coupon['code']
            discount_amount = round(raw_total * (coupon['discount_percent'] / 100.0), 2)

    total_price = max(0.0, raw_total - discount_amount)

    cursor.execute('''
        INSERT INTO orders (customer_id, customer_name, customer_phone, customer_address, status, total_price, coupon_code, discount_amount)
        VALUES (?, ?, ?, ?, 'Нове', ?, ?, ?);
    ''', (customer_id, name.strip(), phone.strip(), address.strip(), total_price, applied_coupon, discount_amount))

    order_id = cursor.lastrowid

    for item in items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?);
        ''', (order_id, int(item['product_id']), int(item['quantity']), float(item['price'])))

    db.commit()
    return order_id

def get_all_orders():
    """Повертає список усіх замовлень у зворотному хронологічному порядку."""
    db = get_db()
    return db.execute('SELECT * FROM orders ORDER BY created_at DESC;').fetchall()

def get_order_by_id(order_id):
    """Повертає інформацію про конкретне замовлення."""
    db = get_db()
    return db.execute('SELECT * FROM orders WHERE id = ?;', (order_id,)).fetchone()

def get_order_details(order_id):
    """
    Повертає кортеж (order, items):
    order: запис із таблиці orders
    items: список позицій із order_items з приєднаними назвами та категоріями з products
    """
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?;', (order_id,)).fetchone()
    if not order:
        return None, []
    items = db.execute('''
        SELECT oi.*, p.name AS product_name, p.category AS product_category
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?;
    ''', (order_id,)).fetchall()
    return order, items

def update_order_status(order_id, new_status):
    """Оновлює поточний статус замовлення."""
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?;', (new_status, order_id))
    db.commit()

def delete_order(order_id):
    """Видаляє замовлення (order_items каскадно видаляються СКБД завдяки ON DELETE CASCADE)."""
    db = get_db()
    db.execute('DELETE FROM orders WHERE id = ?;', (order_id,))
    db.commit()

def get_orders_by_phone(phone):
    """Пошук усіх замовлень за номером телефону (для відстеження клієнтом)."""
    db = get_db()
    clean = phone.strip()
    return db.execute(
        'SELECT * FROM orders WHERE customer_phone LIKE ? ORDER BY created_at DESC;',
        (f'%{clean}%',)
    ).fetchall()

# --- ФУНКЦІЇ ДЛЯ РОБОТИ З ПРОМОКОДАМИ (COUPONS - Рівень 3) ---
def get_coupon(code):
    """Знаходить промокод за кодом (без урахування регістру символів)."""
    if not code:
        return None
    db = get_db()
    return db.execute('SELECT * FROM coupons WHERE UPPER(code) = UPPER(?);', (code.strip(),)).fetchone()

def get_all_coupons():
    """Повертає перелік усіх діючих промокодів."""
    db = get_db()
    return db.execute('SELECT * FROM coupons ORDER BY id ASC;').fetchall()

def add_coupon(code, discount_percent):
    """Створює новий промокод."""
    db = get_db()
    cursor = db.execute(
        'INSERT INTO coupons (code, discount_percent) VALUES (?, ?);',
        (code.strip().upper(), int(discount_percent))
    )
    db.commit()
    return cursor.lastrowid

def delete_coupon(coupon_id):
    """Видаляє промокод за його ID."""
    db = get_db()
    db.execute('DELETE FROM coupons WHERE id = ?;', (coupon_id,))
    db.commit()
