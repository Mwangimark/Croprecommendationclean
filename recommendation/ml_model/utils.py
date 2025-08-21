import pandas as pd
import joblib
import os

# Load model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'crop_model', 'crop_recommendation_model.pkl')
model = joblib.load(MODEL_PATH)

# Feature names used during training
FEATURE_NAMES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

# Hardcoded label map (from your training notebook)
LABEL_MAP = {
    0: 'apple', 1: 'banana', 2: 'blackgram', 3: 'chickpea', 4: 'coconut',
    5: 'coffee', 6: 'cotton', 7: 'grapes', 8: 'jute', 9: 'kidneybeans',
    10: 'lentil', 11: 'maize', 12: 'mango', 13: 'mothbeans', 14: 'mungbean',
    15: 'muskmelon', 16: 'orange', 17: 'papaya', 18: 'pigeonpeas',
    19: 'pomegranate', 20: 'rice', 21: 'watermelon'
}

def predict_top_crops(input_data):
    """
    Takes in feature data and returns top 3 crop predictions with their confidence.
    """
    # Prepare input
    if isinstance(input_data, list):
        input_df = pd.DataFrame([input_data], columns=FEATURE_NAMES)
    elif isinstance(input_data, dict):
        input_df = pd.DataFrame([input_data])
    else:
        raise ValueError("Invalid input type for prediction")

    # Predict probabilities
    probs = model.predict_proba(input_df)[0]
    top3_indices = probs.argsort()[-3:][::-1]

    # Map to crop names
    top3 = [(LABEL_MAP[i], probs[i]) for i in top3_indices]

    return top3
