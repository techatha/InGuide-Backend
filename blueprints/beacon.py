import datetime
from flask import Blueprint, request, jsonify
from app import db
from google.cloud.firestore import GeoPoint

beacons_bp = Blueprint('Beacons', __name__)


# --------------------------
# GET all beacons for a floor
# --------------------------
@beacons_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_beacons(building_id, floor_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' parameter."}), 400
    if not floor_id:
        return jsonify({"error": "Missing 'floor_id' parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        floor_ref = db.collection('buildings').document(building_id)\
            .collection('floors').document(floor_id)
        if not floor_ref.get().exists:
            return jsonify({"error": f"Floor '{floor_id}' not found in building '{building_id}'."}), 404

        beacons_ref = floor_ref.collection('beacons')
        beacon_docs = beacons_ref.stream()

        beacons = []
        for doc in beacon_docs:
            beacon_data = doc.to_dict()
            beacon_data['beaconId'] = doc.id
            beacon_data['name'] = beacon_data.get('name', '')
            if 'latLng' in beacon_data and isinstance(beacon_data['latLng'], GeoPoint):
                beacon_data['latLng'] = [beacon_data['latLng'].latitude, beacon_data['latLng'].longitude]
            beacons.append(beacon_data)

        return jsonify(beacons), 200

    except Exception as e:
        print(f"Error fetching beacons: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------
# ADD beacon
# --------------------------
@beacons_bp.route('/<building_id>/<floor_id>', methods=['POST'])
def add_beacon(building_id, floor_id):
    try:
        data = request.get_json()
        if not data or 'beaconId' not in data or 'latLng' not in data or 'name' not in data:
            return jsonify({"error": "Beacon must have 'beaconId', 'name', and 'latLng' [lat, lng]."}), 400

        beacon_id = data['beaconId']
        name = data['name']
        lat, lng = data['latLng']

        beacon_ref = db.collection('buildings').document(building_id)\
            .collection('floors').document(floor_id)\
            .collection('beacons').document(beacon_id)

        beacon_ref.set({
            "latLng": GeoPoint(lat, lng),
            "name": name
        })

        return jsonify({"status": "success", "message": f"Beacon {beacon_id} added."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------
# UPDATE beacon
# --------------------------
@beacons_bp.route('/<building_id>/<floor_id>/<beacon_id>', methods=['PATCH'])
def update_beacon(building_id, floor_id, beacon_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required."}), 400

        update_data = {}
        if 'latLng' in data:
            lat, lng = data['latLng']
            update_data['latLng'] = GeoPoint(lat, lng)
        if 'name' in data:
            update_data['name'] = data['name']

        if not update_data:
            return jsonify({"error": "Nothing to update. Provide 'latLng' or 'name'."}), 400

        beacon_ref = db.collection('buildings').document(building_id)\
            .collection('floors').document(floor_id)\
            .collection('beacons').document(beacon_id)

        if not beacon_ref.get().exists:
            return jsonify({"error": f"Beacon {beacon_id} not found"}), 404

        beacon_ref.update(update_data)

        return jsonify({"status": "success", "message": f"Beacon {beacon_id} updated."}), 200
    except Exception as e:
        print(f"Error updating beacon: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------
# DELETE beacon
# --------------------------
@beacons_bp.route('/<building_id>/<floor_id>/<beacon_id>', methods=['DELETE'])
def delete_beacon(building_id, floor_id, beacon_id):
    try:
        beacon_ref = db.collection('buildings').document(building_id)\
            .collection('floors').document(floor_id)\
            .collection('beacons').document(beacon_id)

        if not beacon_ref.get().exists:
            return jsonify({"error": f"Beacon {beacon_id} not found"}), 404

        beacon_ref.delete()
        return jsonify({"status": "success", "message": f"Beacon {beacon_id} deleted."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------
# LOG beacon data (GPS logs)
# --------------------------
@beacons_bp.route('/beaconLog', methods=['GET'])
def logBeaconData():
    try:
        sensor_id = request.args.get('sensorID')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)

        if not all([sensor_id, lat, lon]):
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
