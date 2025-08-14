from flask import Blueprint, request, jsonify
from app import db
import datetime

beacon_bp = Blueprint('beacon', __name__)


@beacon_bp.route('/beaconLog', methods=['GET'])
def logBeaconData():
    try:
        # Get data from the request arguments
        sensor_id = request.args.get('sensorID')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)

        # Basic validation for required fields
        if not all([sensor_id, lat, lon]):
            return jsonify({"error": "Missing sensorID, lat, or lon"}), 400

        # Create a document reference in the 'gps_logs' collection
        # Firestore automatically generates a new document ID here
        doc_ref = db.collection('gps_logs').document()

        # Data to be saved in the document
        gps_data = {
            'sensor_id': sensor_id,
            'latitude': lat,
            'longitude': lon,
            'timestamp': datetime.datetime.utcnow()
        }

        # Use the document reference to set the data
        doc_ref.set(gps_data)

        return jsonify({"status": "success", "message": "GPS data logged"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

