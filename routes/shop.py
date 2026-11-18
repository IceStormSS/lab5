from flask import Blueprint, render_template, request, redirect, url_for, flash
import models

shop_bp = Blueprint('shop_bp', __name__)

@shop_bp.route('/shop')
def shop():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip()

    items = models.get_all_products(category=category, search=search)
    categories = models.get_categories()

    return render_template(
        'shop.html',
        items=items,
        categories=categories,
        current_category=category,
        search_query=search
    )

@shop_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = models.get_product_by_id(product_id)
    if not product:
        return render_template('404.html'), 404
    coupons = models.get_all_coupons()
    return render_template('product_detail.html', product=product, coupons=coupons)

@shop_bp.route('/product/<int:product_id>/order', methods=['POST'])
def create_product_order(product_id):
    product = models.get_product_by_id(product_id)
    if not product:
        flash('Товар не знайдено.', 'error')
        return redirect(url_for('shop_bp.shop'))

    customer_name = request.form.get('customer_name', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    customer_address = request.form.get('customer_address', '').strip()
    coupon_code = request.form.get('coupon_code', '').strip().upper()

    try:
        quantity = max(1, int(request.form.get('quantity', 1)))
    except ValueError:
        quantity = 1

    if not customer_name or not customer_phone or not customer_address:
        flash('Будь ласка, заповніть усі обов\'язкові поля (ПІБ, телефон, адреса доставки).', 'error')
        return redirect(url_for('shop_bp.product_detail', product_id=product_id))

    # Перевірка промокоду
    applied_coupon = None
    if coupon_code:
        coupon = models.get_coupon(coupon_code)
        if coupon:
            applied_coupon = coupon['code']
        else:
            flash(f'Промокод "{coupon_code}" не знайдено або термін його дії закінчився. Замовлення оформлено без знижки.', 'warning')

    items = [{
        'product_id': product['id'],
        'quantity': quantity,
        'price': product['price']
    }]

    order_id = models.create_order(
        name=customer_name,
        phone=customer_phone,
        address=customer_address,
        items=items,
        coupon_code=applied_coupon
    )

    flash(f'Дякуємо, {customer_name}! Ваше замовлення #{order_id} успішно прийнято в обробку!', 'success')
    return redirect(url_for('shop_bp.order_success', order_id=order_id))

@shop_bp.route('/order/success/<int:order_id>')
def order_success(order_id):
    order, items = models.get_order_details(order_id)
    if not order:
        flash('Замовлення не знайдено.', 'error')
        return redirect(url_for('shop_bp.shop'))
    return render_template('order_success.html', order=order, items=items)

@shop_bp.route('/my-orders', methods=['GET', 'POST'])
def my_orders():
    phone = request.values.get('phone', '').strip()
    orders = []
    if phone:
        orders = models.get_orders_by_phone(phone)
    return render_template('my_orders.html', phone=phone, orders=orders)
