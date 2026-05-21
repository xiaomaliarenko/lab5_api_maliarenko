# Модель: Оптимальне керування процесом очищення водойми (5 семестр)
# Автор: Маляренко Анастасія (у групі з Брагар Софією), група АІ-233

from flask import Flask, request, jsonify
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

app = Flask(__name__)

class WaterOptimizer:
    def __init__(self, V, Q, k, C_initial, C_target, Cin_max):
        self.V = V; self.Q = Q; self.k = k
        self.C_initial = C_initial
        self.C_target = C_target
        self.Cin_max = Cin_max

    def cstr_ode(self, t, C, Cin_profile, t_points):
        u_t = np.interp(t, t_points, Cin_profile)
        return (self.Q / self.V) * u_t - (self.Q / self.V + self.k) * C

    def objective_minimum_effort(self, Cin_profile, T_fix, N_steps):
        t_points = np.linspace(0, T_fix, N_steps)
        sol = solve_ivp(
            self.cstr_ode, (0, T_fix), [self.C_initial],
            args=(Cin_profile, t_points), method='RK45', t_eval=t_points
        )
        C_final = sol.y[0, -1]
        penalty = 0 if C_final <= self.C_target else (C_final - self.C_target)**2 * 1e5
        dt = T_fix / (N_steps - 1)
        return np.sum(Cin_profile**2) * dt + penalty

    def find_optimal_control(self, T_fix, N_steps=50):
        initial_guess = np.ones(N_steps) * self.Cin_max
        bounds = [(0, self.Cin_max)] * N_steps
        result = minimize(
            self.objective_minimum_effort, initial_guess,
            args=(T_fix, N_steps), method='SLSQP', bounds=bounds
        )
        return result.x, result.fun

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Отримання параметрів з JSON-запиту
        data = request.get_json() or {}
        
        # Значення за замовчуванням, якщо параметри не передані
        V = float(data.get('V', 1000))
        Q = float(data.get('Q', 50))
        k = float(data.get('k', 0.01))
        C_initial = float(data.get('C_initial', 0.5))
        C_target = float(data.get('C_target', 0.1))
        Cin_max = float(data.get('Cin_max', 0.2))
        T_fix = float(data.get('T_fix', 10))

        # Запуск обчислень моделі
        optimizer = WaterOptimizer(V, Q, k, C_initial, C_target, Cin_max)
        control_profile, cost = optimizer.find_optimal_control(T_fix=T_fix)

        # Формування відповіді API
        return jsonify({
            "status": "success",
            "meta": {
    "model": "Optimal control of water purification process",
    "authors": "Maliarenko Anastasiia, Brahar Sofiia",
    "group": "AI-233"
},
            "input_parameters": {
                "V": V, "Q": Q, "k": k, "C_initial": C_initial, "C_target": C_target, "Cin_max": Cin_max, "T_fix": T_fix
            },
            "result": {
                "minimum_energy_cost": float(cost),
                "optimal_control_vector_sample": [float(x) for x in control_profile[:5]]  # перші 5 точок для компактності
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
