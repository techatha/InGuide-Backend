from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from preprocess import preprocess
import pickle
import os

model_bp = Blueprint('model', __name__)

MODEL_PATH = os.path.join('Models', 'lightGBM-model_v4.pkl')

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print(f"Error: Model file '{MODEL_PATH}' not found.")
    model = None

@model_bp.route('/predictMovement', methods=['POST'])
def predictMovement():
    if model is None:
        return jsonify({"error": "Model not loaded. Please check the model file path."}), 500
    try:
        request_payload = request.get_json(silent=True)
        if not request_payload:
            return jsonify({"error": "Invalid JSON data provided."}), 400
        if 'data' not in request_payload:
            return jsonify({"error": "Missing 'data' array in JSON payload."}), 400

        data_df = pd.DataFrame(request_payload['data'])
        processed = preprocess(data_df, request_payload.get('interval'))

        prob = model.predict_proba(processed)[0]
        prediction = int(np.argmax(prob))
        action_label = {0: 'Halt', 1: 'Forward', 2: 'Turn'}
        return jsonify({
            "prediction": prediction,
            "action": action_label.get(prediction, 'Unknown'),
            "probability": {"Halt": float(prob[0]), "Forward": float(prob[1]), "Turn": float(prob[2])}
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
