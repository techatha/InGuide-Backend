from flask import Flask, request, jsonify
from flask_cors import CORS
from preprocess import preprocess
import pickle
import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/inguide'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True


try:
    with open('Models/lightGBM-model_v4.pkl', 'rb') as f:
        model = pickle.load(f)

except FileNotFoundError:
    print("Error: Model file 'lightGBM-model_v3.pkl' not found.")
    model = None
db = SQLAlchemy(app)


class GPSLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


with app.app_context():
    db.create_all()


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


@app.route('/beaconLog', methods=['GET'])
def logBeaconData():
    try:
        sensor_id = request.args.get('sensorID')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)

        if not all([sensor_id, lat, lon]):
            return jsonify({"error": "Missing sensorID, lat, or lon"}), 400

        gps_entry = GPSLog(sensor_id=sensor_id, latitude=lat, longitude=lon)
        db.session.add(gps_entry)
        try:
            db.session.commit()
        except Exception as commit_err:
            db.session.rollback()
            print("Commit error:", commit_err)
            return jsonify({"status": "error", "message": "Database commit failed: " + str(commit_err)}), 500

        return jsonify({"status": "success", "message": "GPS data logged"}), 200

    except Exception as e:
        print("yes error")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('localhost+4.pem', 'localhost+4-key.pem'),
        debug=True
    )
