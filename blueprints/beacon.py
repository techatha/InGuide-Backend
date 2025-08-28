from flask import Blueprint, request, jsonify
import datetime
from firebase_init import db  # was: from app import db

beacon_bp = Blueprint('beacon', __name__)

@beacon_bp.route('/beaconLog', methods=['GET'])
def logBeaconData():
    try:
        sensor_id = request.args.get('sensorID')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)

        if sensor_id is None or lat is None or lon is None:
            return jsonify({"error": "Missing sensorID, lat, or lon"}), 400

        doc_ref = db.collection('gps_logs').document()
        gps_data = {
            'sensor_id': sensor_id,
            'latitude': lat,
            'longitude': lon,
            'timestamp': datetime.datetime.utcnow()
        }
        doc_ref.set(gps_data)
        return jsonify({"status": "success", "message": "GPS data logged"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
