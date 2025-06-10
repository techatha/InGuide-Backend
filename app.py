from flask import Flask, request, jsonify
from flask_cors import CORS
from preprocess import preprocess
import pickle
import pandas as pd

app = Flask(__name__)
CORS(app)

try:
    with open('Models/lightGBM-model_v1.pkl', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("Error: Model file 'lightGBM-model_v1.pkl' not found.")
    model = None


@app.route('/predictMovement', methods=['POST'])
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
        prediction = model.predict(processed_data)

        return jsonify({"prediction": prediction.tolist()}), 200  # Convert prediction to list for JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)