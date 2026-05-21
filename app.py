# Модель: Оптимальне керування процесом очищення водойми (5 семестр)
# Автор: Маляренко Анастасія, група АІ-233
# Варіант: 9 (Непарний — з етапом автоматичного тестування unittest)

import unittest
import json
import numpy as np
from flask import Flask, jsonify, request
from scipy.optimize import minimize

app = Flask(__name__)

# --- МАТЕМАТИЧНА МОДЕЛЬ (ВАРІАНТ 9) ---
def objective_function(u):
    """
    Цільова функція: мінімізація витрат енергії на очищення.
    u[0] - швидкість подачі коагулянту
    u[1] - інтенсивність аерації
    """
    return 0.6 * (u[0]**2) + 0.4 * (u[1]**2)

def constraint_pollution(u):
    """
    Обмеження на рівень забруднення води після очищення.
    Концентрація шкідливих речовин повинна знизитися до безпечного рівня.
    """
    initial_pollution = 15.0  # початковий рівень
    # Модель зниження забруднення залежно від керуючих впливів
    final_pollution = initial_pollution - (2.5 * u[0] + 1.8 * u[1])
    return 1.0 - final_pollution  # final_pollution <= 1.0 мг/л

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Початкове наближення для алгоритму оптимізації
        u0 = [1.0, 1.0]
        
        # Граничні умови для керуючих впливів (технічні обмеження обладнання)
        bounds = ((0.0, 10.0), (0.0, 10.0))
        
        # Опис системи обмежень
        constraints = {'type': 'ineq', 'fun': constraint_pollution}
        
        # Пошук оптимального керування
        solution = minimize(objective_function, u0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if solution.success:
            return jsonify({
                "status": "success",
                "model": "Optimal Water Purification Management",
                "variant": 9,
                "author": "Maliarenko Anastasia",
                "result": {
                    "coagulant_rate_u1": float(round(solution.x[0], 4)),
                    "aeration_intensity_u2": float(round(solution.x[1], 4)),
                    "minimum_energy_cost": float(round(solution.fun, 4))
                }
            }), 200
        else:
            return jsonify({"status": "error", "message": "Optimization failed"}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "active",
        "message": "Water Optimization API is running. Use /calculate endpoint."
    }), 200


class FlaskAPITestCase(unittest.TestCase):
    def setUp(self):
        """Налаштування віртуального клієнта перед початком тестування"""
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_index_endpoint(self):
        """Перевірка доступності головної сторінки сервісу"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'active')

    def test_calculate_endpoint_success(self):
        """Перевірка роботи математичного алгоритму оптимізації"""
        response = self.client.post('/calculate', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('result', data)
        self.assertIn('minimum_energy_cost', data['result'])
        # Тест валідує, що витрати енергії є позитивним числом
        self.assertGreater(data['result']['minimum_energy_cost'], 0)


# Логіка запуску додатка
if __name__ == '__main__':
    # Сервер запускається у звичайному режимі, якщо файл викликано стандартно
    app.run(host='0.0.0.0', port=5000)
