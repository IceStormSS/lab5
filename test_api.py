import json
import unittest
from app import app
import models

class RestApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_01_swagger_docs(self):
        """Перевірка доступності сторінки Swagger UI та специфікації JSON"""
        res_docs = self.client.get('/apidocs/')
        self.assertEqual(res_docs.status_code, 200)

        res_spec = self.client.get('/apispec_1.json')
        self.assertEqual(res_spec.status_code, 200)
        spec = res_spec.get_json()
        self.assertIn('paths', spec)
        self.assertIn('/api/v1/products', spec['paths'])

    def test_02_get_all_products(self):
        """GET /api/v1/products - успішне отримання списку товарів"""
        res = self.client.get('/api/v1/products')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_03_get_product_by_id_success(self):
        """GET /api/v1/products/<id> - отримання конкретного товару"""
        res = self.client.get('/api/v1/products/1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['id'], 1)
        self.assertIn('name', data)
        self.assertIn('price', data)

    def test_04_get_product_by_id_not_found(self):
        """GET /api/v1/products/99999 - товар не знайдено (404)"""
        res = self.client.get('/api/v1/products/99999')
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data['status'], 404)
        self.assertIn('error', data)

    def test_05_create_product_success(self):
        """POST /api/v1/products - створення нового товару (201)"""
        payload = {
            "name": "Тестова парка REST API",
            "category": "Парки",
            "price": 3100.5,
            "description": "Опис для автоматичного тесту"
        }
        res = self.client.post(
            '/api/v1/products',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], payload['name'])
        self.assertEqual(data['price'], payload['price'])

        # Зберігаємо ID для наступних тестів
        self.__class__.created_product_id = data['id']

    def test_06_create_product_validation_error(self):
        """POST /api/v1/products - помилка валідації (ціна від'ємна, ім'я порожнє) (400)"""
        payload = {
            "name": "",
            "category": "Парки",
            "price": -100
        }
        res = self.client.post(
            '/api/v1/products',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data['status'], 400)
        self.assertIn('details', data)
        self.assertGreater(len(data['details']), 0)

    def test_07_update_product(self):
        """PUT /api/v1/products/<id> - оновлення товару (200)"""
        prod_id = getattr(self.__class__, 'created_product_id', 1)
        payload = {
            "name": "Оновлена назва товару",
            "category": "Оновлена категорія",
            "price": 4999.0,
            "description": "Оновлений тестовий опис"
        }
        res = self.client.put(
            f'/api/v1/products/{prod_id}',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['name'], payload['name'])
        self.assertEqual(data['price'], payload['price'])

    def test_08_delete_product(self):
        """DELETE /api/v1/products/<id> - видалення товару (204)"""
        prod_id = getattr(self.__class__, 'created_product_id', None)
        if prod_id:
            res = self.client.delete(f'/api/v1/products/{prod_id}')
            self.assertEqual(res.status_code, 204)

            # Перевіряємо, що повторний GET повертає 404
            check_res = self.client.get(f'/api/v1/products/{prod_id}')
            self.assertEqual(check_res.status_code, 404)

    def test_09_feedbacks_api(self):
        """GET /api/v1/feedbacks та POST /api/v1/feedbacks"""
        # 1. Отримання списку відгуків
        get_res = self.client.get('/api/v1/feedbacks')
        self.assertEqual(get_res.status_code, 200)
        self.assertIsInstance(get_res.get_json(), list)

        # 2. Додавання відгуку
        fb_payload = {
            "name": "Андрій Козак",
            "email": "andriy@test.com",
            "message": "Чудовий API та якісний магазин!"
        }
        post_res = self.client.post(
            '/api/v1/feedbacks',
            data=json.dumps(fb_payload),
            content_type='application/json'
        )
        self.assertEqual(post_res.status_code, 201)
        fb_data = post_res.get_json()
        self.assertEqual(fb_data['name'], fb_payload['name'])

        # 3. Валідація некоректного email
        bad_fb = {
            "name": "А",
            "email": "not-an-email",
            "message": "коротко"
        }
        bad_res = self.client.post(
            '/api/v1/feedbacks',
            data=json.dumps(bad_fb),
            content_type='application/json'
        )
        self.assertEqual(bad_res.status_code, 400)

    def test_10_api_v2_pagination(self):
        """GET /api/v2/products - версіонування v2 з пагінацією"""
        res = self.client.get('/api/v2/products?page=1&per_page=4')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['version'], 'v2')
        self.assertIn('pagination', data)
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['per_page'], 4)
        self.assertIsInstance(data['items'], list)
        self.assertEqual(len(data['items']), 4)

    def test_11_api_v2_invalid_page(self):
        """GET /api/v2/products?page=-5 - валідація сторінки (400)"""
        res = self.client.get('/api/v2/products?page=-5')
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data['status'], 400)

    def test_12_global_api_404_json(self):
        """Перевірка обробника 404 для API: повертає JSON"""
        res = self.client.get('/api/v1/some-missing-resource')
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data['status'], 404)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
