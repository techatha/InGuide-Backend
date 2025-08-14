from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from preprocess import preprocess
import pickle

model_bp = Blueprint('model', __name__)
try:
    with open('Models/lightGBM-model_v4.pkl', 'rb') as f:
        model = pickle.load(f)

except FileNotFoundError:
    print("Error: Model file 'lightGBM-model_v3.pkl' not found.")
    model = None


@model_bp.route('/predictMovement', methods=['POST'])
def predictMovement():
    if model is None:
        return jsonify({"error": "Model not loaded. Please check the model file path."}), 500

    try:
        request_payload = request.get_json()
        if request_payload is None:
            return jsonify({"error": "Invalid JSON data provided."}), 400

        if 'data' not in request_payload:
            return jsonify({"error": "Missing 'data' array in JSON payload."}), 400

        data_list = request_payload['data']
        data_df = pd.DataFrame(data_list)
        data_interval = request_payload.get('interval')
        processed_data = preprocess(data_df, data_interval)

        # Make prediction
        prob = model.predict_proba(processed_data)[0]
        prediction = int(np.argmax(prob))
        action_label = {0: 'Halt', 1: 'Forward', 2: 'Turn'}
        prediction_label = action_label.get(prediction, 'Unknown')

        return jsonify({
            "prediction": prediction,
            "action": prediction_label,
            "probability": {
                "Halt": prob[0],
                "Forward": prob[1],
                "Turn": prob[2]
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

