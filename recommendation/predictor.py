# recommendation/ml_models/predictor.py

import os
import joblib
from threading import Lock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'your_model.pkl')

# Thread-safe lazy loader
_model = None
_model_lock = Lock()

def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-checked locking
                try:
                    _model = joblib.load(MODEL_PATH)
                    print("✅ Model loaded successfully")
                except Exception as e:
                    _model = None
                    print(f"🔴 Error loading model: {e}")
    return _model

def predict_crops(data):
    """
    Takes a dictionary of input values and returns the top 3 predicted crops.
    Expected keys: nitrogen, phosphorus, potassium, pH, rainfall, temperature, humidity
    """
    model = get_model()
    if model is None:
        return ["Model not loaded"]

    input_values = [
        data.get('nitrogen'),
        data.get('phosphorus'),
        data.get('potassium'),
        data.get('ph'),
        data.get('rainfall'),
        data.get('temperature'),
        data.get('humidity'),
    ]

    probabilities = model.predict_proba([input_values])[0]
    top3_indices = probabilities.argsort()[-3:][::-1]
    crop_labels = model.classes_
    return [crop_labels[i] for i in top3_indices]
