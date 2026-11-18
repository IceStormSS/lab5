from flask import Blueprint, render_template, request, redirect, url_for, flash
import models

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

@admin_bp.route('/')
def dashboard():
    """Головна сторінка адмін-панелі зі статистикою."""
    feedbacks = models.get_all_feedbacks()
    products = models.get_all_products()
    customers = models.get_all_customers()
    orders = models.get_all_orders()
    coupons = models.get_all_coupons()
    total_revenue = sum(o['total_price'] for o in orders if o['status'] != 'Скасовано')

    return render_template(
        'admin/dashboard.html',
        feedbacks_count=len(feedbacks),
        products_count=len(products),
        customers_count=len(customers),
        orders_count=len(orders),
        coupons_count=len(coupons),
        total_revenue=total_revenue
    )

# --- КЕРУВАННЯ ВІДГУКАМИ (FEEDBACK) ---
@admin_bp.route('/feedbacks')
def feedbacks_list():
    feedbacks = models.get_all_feedbacks()
    return render_template('admin/feedbacks.html', feedbacks=feedbacks)

@admin_bp.route('/feedbacks/delete/<int:feedback_id>', methods=['POST'])
def feedback_delete(feedback_id):
    models.delete_feedback(feedback_id)
    flash('Відгук успішно видалено!', 'success')
    return redirect(url_for('admin_bp.feedbacks_list'))

# --- КЕРУВАННЯ ТОВАРАМИ (PRODUCTS) ---
@admin_bp.route('/products')
def products_list():
    products = models.get_all_products()
    categories = models.get_categories()
    return render_template('admin/products.html', products=products, categories=categories)

@admin_bp.route('/products/add', methods=['POST'])
def product_add():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price = request.form.get('price', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not category or not price:
        flash('Будь ласка, заповніть обов\'язкові поля (назва, категорія, ціна).', 'error')
    else:
        try:
            price_float = float(price)
            models.add_product(name, category, price_float, description)
            flash(f'Товар "{name}" успішно додано до бази даних!', 'success')
        except ValueError:
            flash('Ціна повинна бути числовим значенням.', 'error')

    return redirect(url_for('admin_bp.products_list'))

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def product_delete(product_id):
    models.delete_product(product_id)
    flash('Товар успішно видалено з бази даних!', 'success')
    return redirect(url_for('admin_bp.products_list'))

# --- КЕРУВАННЯ КЛІЄНТАМИ (CUSTOMERS - Рівень 2) ---
@admin_bp.route('/customers')
def customers_list():
    customers = models.get_all_customers()
    return render_template('admin/customers.html', customers=customers)

@admin_bp.route('/customers/add', methods=['POST'])
def customer_add():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()

    if not name or not email:
        flash('Ім\'я та Email є обов\'язковими для створення клієнта.', 'error')
    else:
        models.add_customer(name, email, phone, address)
        flash(f'Клієнта "{name}" успішно додано!', 'success')

    return redirect(url_for('admin_bp.customers_list'))

@admin_bp.route('/customers/delete/<int:customer_id>', methods=['POST'])
def customer_delete(customer_id):
    models.delete_customer(customer_id)
    flash('Клієнта успішно видалено.', 'success')
    return redirect(url_for('admin_bp.customers_list'))

# =========================================================================
# ЧАСТИНА 2: КЕРУВАННЯ ЗАМОВЛЕННЯМИ (ORDERS) ТА ПРОМОКОДАМИ (COUPONS)
# =========================================================================

@admin_bp.route('/orders')
def orders_list():
    """Перегляд списку всіх замовлень із можливістю фільтрації за статусом."""
    status_filter = request.args.get('status', '').strip()
    all_orders = models.get_all_orders()
    
    if status_filter and status_filter != 'all':
        orders = [o for o in all_orders if o['status'] == status_filter]
    else:
        orders = all_orders

    return render_template(
        'admin/orders.html',
        orders=orders,
        current_status=status_filter,
        total_count=len(all_orders)
    )

@admin_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    """Детальний перегляд замовлення, замовлених товарів та керування статусом."""
    order, items = models.get_order_details(order_id)
    if not order:
        flash('Замовлення не знайдено.', 'error')
        return redirect(url_for('admin_bp.orders_list'))

    statuses = ['Нове', 'В обробці', 'Відправлено', 'Виконано', 'Скасовано']
    return render_template(
        'admin/order_detail.html',
        order=order,
        items=items,
        statuses=statuses
    )

@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
def order_status_update(order_id):
    """Зміна статусу замовлення через випадаючий список в адмін-панелі."""
    new_status = request.form.get('status', '').strip()
    valid_statuses = ['Нове', 'В обробці', 'Відправлено', 'Виконано', 'Скасовано']

    if new_status in valid_statuses:
        models.update_order_status(order_id, new_status)
        flash(f'Статус замовлення #{order_id} успішно змінено на «{new_status}»!', 'success')
    else:
        flash('Некоректний статус замовлення.', 'error')

    return redirect(url_for('admin_bp.order_detail', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/delete', methods=['POST'])
def order_delete(order_id):
    """Видалення замовлення з бази даних (разом із записами в order_items)."""
    models.delete_order(order_id)
    flash(f'Замовлення #{order_id} успішно видалено!', 'success')
    return redirect(url_for('admin_bp.orders_list'))

# --- КЕРУВАННЯ ПРОМОКОДАМИ (COUPONS - Рівень 3) ---
@admin_bp.route('/coupons')
def coupons_list():
    """Перегляд списку діючих промокодів."""
    coupons = models.get_all_coupons()
    return render_template('admin/coupons.html', coupons=coupons)

@admin_bp.route('/coupons/add', methods=['POST'])
def coupon_add():
    """Додавання нового промокоду."""
    code = request.form.get('code', '').strip().upper()
    discount_str = request.form.get('discount_percent', '').strip()

    if not code or not discount_str:
        flash('Вкажіть код купона та відсоток знижки.', 'error')
    else:
        try:
            discount = int(discount_str)
            if discount <= 0 or discount > 100:
                flash('Знижка повинна становити від 1 до 100 відсотків.', 'error')
            elif models.get_coupon(code):
                flash(f'Промокод «{code}» вже існує в системі.', 'error')
            else:
                models.add_coupon(code, discount)
                flash(f'Промокод «{code}» на знижку {discount}% успішно створено!', 'success')
        except ValueError:
            flash('Відсоток знижки повинен бути цілим числом.', 'error')

    return redirect(url_for('admin_bp.coupons_list'))

@admin_bp.route('/coupons/delete/<int:coupon_id>', methods=['POST'])
def coupon_delete(coupon_id):
    """Видалення промокоду."""
    models.delete_coupon(coupon_id)
    flash('Промокод успішно видалено.', 'success')
    return redirect(url_for('admin_bp.coupons_list'))
