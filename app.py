import os
from flask import Flask, render_template, request, jsonify
from flasgger import Swagger
import models
from routes.feedback import feedback_bp
from routes.shop import shop_bp
from routes.admin import admin_bp
from routes.api_v1 import api_v1_bp
from routes.api_v2 import api_v2_bp

app = Flask(__name__)

# Конфігурація додатка
app.config['SECRET_KEY'] = 'dev-secret-key-lab05-rest-api'
app.config['DATABASE'] = os.path.join(app.root_path, 'db.sqlite')
app.config['JSON_AS_ASCII'] = False  # Коректне відображення кирилиці в JSON

# Налаштування Swagger / Flasgger (Рівень 2)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Outerwear Shop REST API",
        "description": "Повноцінний REST API для інтернет-магазину верхнього одягу (Лабораторна робота №5).\n\n"
                       "**Виконання завдань:**\n"
                       "- **Рівень 1**: Базовий REST API для ресурсів Products та Feedbacks (JSON, коди 200/201/204/400/404/500).\n"
                       "- **Рівень 2**: Інтерактивна документація Flasgger (Swagger UI) за адресою `/apidocs/`.\n"
                       "- **Рівень 3**: Валідація вхідних даних та версіонування API (`/api/v1` і `/api/v2`).\n\n"
                       "**Розподіл робіт (50% / 50%):**\n"
                       "- **Частина 1 (Виконано)**: Архітектура API, обробка помилок, Swagger UI, ендпоінти Products, Feedbacks, версія API v2 з пагінацією.\n"
                       "- **Частина 2 (Для напарника)**: Ендпоінти Orders, Order Items, Coupons, Customers.",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": [
        "http"
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Реєстрація автоматичного закриття з'єднання з БД після кожного запиту
app.teardown_appcontext(models.close_db)

# Реєстрація веб-Blueprint-ів (UI інтерфейс)
app.register_blueprint(feedback_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp)

# Реєстрація REST API Blueprint-ів (Лабораторна робота №5)
app.register_blueprint(api_v1_bp)
app.register_blueprint(api_v2_bp)

# ==========================================
# ОБРОБНИКИ ПОМИЛОК У ФОРМАТІ JSON ДЛЯ API
# ==========================================

@app.errorhandler(400)
def handle_bad_request(e):
    if request.path.startswith('/api/'):
        description = getattr(e, 'description', 'Некоректний запит (Bad Request)')
        return jsonify({'error': description, 'status': 400}), 400
    return "Некоректний запит (400)", 400

@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Запитуваний ресурс не знайдено (Not Found)', 'status': 404}), 404
    return render_template('home.html', products=models.get_all_products()[:4], feedbacks=models.get_all_feedbacks()[:3]), 404

@app.errorhandler(405)
def handle_method_not_allowed(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Метод не дозволений для цього ресурсу (Method Not Allowed)', 'status': 405}), 405
    return "Метод не підтримується (405)", 405

@app.errorhandler(500)
def handle_server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Внутрішня помилка сервера (Internal Server Error)', 'status': 500}), 500
    return "Внутрішня помилка сервера (500)", 500


@app.route('/')
def home():
    """Головна сторінка з новинками та останніми відгуками з БД."""
    products = models.get_all_products()[:4]
    feedbacks = models.get_all_feedbacks()[:3]
    return render_template('home.html', products=products, feedbacks=feedbacks)

@app.route('/about')
def about():
    """Сторінка 'Про нас'."""
    return render_template('about.html')

# Ініціалізація бази даних SQLite при запуску
with app.app_context():
    models.init_db(app)

if __name__ == '__main__':
    app.run(debug=True)
