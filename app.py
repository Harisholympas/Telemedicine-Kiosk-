from flask import Flask, request, jsonify, render_template
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

vital_history = {
    'default': {
        'BP': [],
        'Oxygen_Level': [],
        'Pulse': [],
        'timestamps': []
    }
}

def generate_arima_forecast(data, n_periods=10):
    """Generate non-linear forecast using ARIMA model with dynamic order selection"""
    if len(data) < 3:  
        return [data[-1] if data else 0] * n_periods
    
    try:
        volatility = np.std(np.diff(data))
        
        if volatility > 2:
            order = (2, 1, 2) 
        elif volatility > 1:
            order = (1, 1, 1) 
        else:
            order = (1, 0, 1)  
            
      
        model = ARIMA(data, order=order)
        fitted_model = model.fit()
        
        
        base_forecast = fitted_model.forecast(steps=n_periods)
        
        time_factors = np.linspace(0, 1, n_periods)
        seasonal_component = 2 * np.sin(2 * np.pi * time_factors)
        trend_component = 0.5 * time_factors * volatility
        
   
        final_forecast = base_forecast + seasonal_component + trend_component
        
        if 'oxygen' in str(data).lower():
            final_forecast = np.clip(final_forecast, 85, 100)
        elif 'pulse' in str(data).lower():
            final_forecast = np.clip(final_forecast, 60, 100)
        elif 'bp' in str(data).lower():
            final_forecast = np.clip(final_forecast, 90, 180)
            
        return final_forecast.tolist()
        
    except:
        last_value = data[-1]
        trend = np.mean(np.diff(data[-3:])) 
        
        forecast = []
        for i in range(n_periods):
            seasonal = 2 * np.sin(2 * np.pi * i / n_periods)
            noise = np.random.normal(0, max(0.5, volatility/2))
            next_value = last_value + trend + seasonal + noise
            forecast.append(next_value)
            last_value = next_value
            
        return forecast

def generate_random_vitals(base_value, variation, min_val, max_val):
    """Generate random vital signs within reasonable range"""
    value = base_value + np.random.uniform(-variation, variation)
    return max(min_val, min(max_val, value))

def get_initial_vitals():
    """Generate initial vital values"""
    return {
        'BP': generate_random_vitals(120, 5, 90, 180),
        'Oxygen_Level': generate_random_vitals(97, 1, 85, 100),
        'Pulse': generate_random_vitals(75, 5, 60, 100)
    }

def update_vital_history(patient_id='default'):
    """Update vital history with new random values"""
    current_time = datetime.now()
    
    if len(vital_history[patient_id]['timestamps']) == 0:
        vitals = get_initial_vitals()
    else:
        last_bp = vital_history[patient_id]['BP'][-1]
        last_oxygen = vital_history[patient_id]['Oxygen_Level'][-1]
        last_pulse = vital_history[patient_id]['Pulse'][-1]
        
        vitals = {
            'BP': generate_random_vitals(last_bp, 3, 90, 180),
            'Oxygen_Level': generate_random_vitals(last_oxygen, 0.5, 85, 100),
            'Pulse': generate_random_vitals(last_pulse, 2, 60, 100)
        }
    
    vital_history[patient_id]['timestamps'].append(current_time.strftime('%H:%M:%S'))
    vital_history[patient_id]['BP'].append(vitals['BP'])
    vital_history[patient_id]['Oxygen_Level'].append(vitals['Oxygen_Level'])
    vital_history[patient_id]['Pulse'].append(vitals['Pulse'])
    
    max_history = 20
    for key in vital_history[patient_id]:
        vital_history[patient_id][key] = vital_history[patient_id][key][-max_history:]
    
    return vitals

def get_tamil_meal_plan(bmi_category):
    """Get Tamil Nadu specific meal recommendations based on BMI category"""
    base_meals = {
        "underweight": {
            "breakfast": ["Pongal with ghee", "Idli with sambar", "Ven Pongal with coconut chutney"],
            "lunch": ["Sambar rice with ghee", "Curd rice with pickle", "Vegetable biryani"],
            "dinner": ["Dosa with potato masala", "Idiyappam with kurma", "Chapati with vegetable curry"],
            "snacks": ["Sundal", "Murukku", "Sweet pongal"]
        },
        "normal": {
            "breakfast": ["Idli with sambar", "Dosa with chutney", "Upma"],
            "lunch": ["Rice with sambar and vegetables", "Rasam rice", "Lemon rice"],
            "dinner": ["Chapati with dal", "Idiyappam with curry", "Dosa with chutney"],
            "snacks": ["Vazhaipoo vadai", "Thattai", "Verkadalai urundai"]
        },
        "overweight": {
            "breakfast": ["Ragi dosa", "Multigrain idli", "Vegetable upma"],
            "lunch": ["Brown rice with sambar", "Kodo millet rice", "Ragi rice"],
            "dinner": ["Millet dosa", "Vegetable soup", "Ragi roti"],
            "snacks": ["Sprouted green gram", "Boiled chickpeas", "Cucumber salad"]
        }
    }
    return base_meals.get(bmi_category, base_meals["normal"])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/update_vitals', methods=['GET'])
def update_vitals():
    patient_id = request.args.get('patient_id', 'default')
    
    new_vitals = update_vital_history(patient_id)
    
    response = {
        'vital_predictions': {
            'BP': {
                'historical': vital_history[patient_id]['BP'],
                'forecast': generate_arima_forecast(vital_history[patient_id]['BP']),
                'timestamps': vital_history[patient_id]['timestamps']
            },
            'Oxygen_Level': {
                'historical': vital_history[patient_id]['Oxygen_Level'],
                'forecast': generate_arima_forecast(vital_history[patient_id]['Oxygen_Level']),
                'timestamps': vital_history[patient_id]['timestamps']
            },
            'Pulse': {
                'historical': vital_history[patient_id]['Pulse'],
                'forecast': generate_arima_forecast(vital_history[patient_id]['Pulse']),
                'timestamps': vital_history[patient_id]['timestamps']
            }
        }
    }
    
    return jsonify(response)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        height_m = data['Height'] / 100
        weight_kg = data['Weight']
        bmi = weight_kg / (height_m ** 2)
        
        if bmi < 18.5:
            bmi_category = "underweight"
        elif bmi < 25:
            bmi_category = "normal"
        else:
            bmi_category = "overweight"
        
        risk_score = 0
        if data['BP'] > 140: risk_score += 1
        if data['Oxygen_Level'] < 95: risk_score += 1
        if data['Pulse'] > 100 or data['Pulse'] < 60: risk_score += 1
        if bmi > 30: risk_score += 1
        
        risk_level = "High" if risk_score >= 3 else "Medium" if risk_score >= 1 else "Low"
        
        initial_vitals = update_vital_history()
        
        meal_plan = get_tamil_meal_plan(bmi_category)
        
        response = {
            "health_risk": risk_level,
            "vital_predictions": {
                'BP': {
                    'historical': vital_history['default']['BP'],
                    'forecast': generate_arima_forecast(vital_history['default']['BP']),
                    'timestamps': vital_history['default']['timestamps']
                },
                'Oxygen_Level': {
                    'historical': vital_history['default']['Oxygen_Level'],
                    'forecast': generate_arima_forecast(vital_history['default']['Oxygen_Level']),
                    'timestamps': vital_history['default']['timestamps']
                },
                'Pulse': {
                    'historical': vital_history['default']['Pulse'],
                    'forecast': generate_arima_forecast(vital_history['default']['Pulse']),
                    'timestamps': vital_history['default']['timestamps']
                }
            },
            "nutrition_plan": {
                "general_advice": "Follow a balanced Tamil Nadu diet with regular exercise.",
                "calories_recommendation": f"{int(weight_kg * 24)} - {int(weight_kg * 26)} calories/day",
                "hydration": f"Drink {int(weight_kg * 0.033)} liters of water daily",
                "exercise_recommendation": "30 minutes of walking or yoga 5 times per week",
                "meal_plan": meal_plan
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)