from flask import Blueprint, request, jsonify
from google.cloud.firestore_v1 import GeoPoint
from firebase_init import db

building_bp = Blueprint('building', __name__)

@building_bp.route('', methods=['GET'])
def get_buildings():
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        buildings = []
        for doc in db.collection('buildings').stream():
            building_data = doc.to_dict() or {}
            building_data['id'] = doc.id

            for k, v in list(building_data.items()):
                if isinstance(v, GeoPoint):
                    building_data[k] = [v.latitude, v.longitude]

            floors_ref = doc.reference.collection('floors')
            floors = []
            for floor_doc in floors_ref.stream():
                floor_data = floor_doc.to_dict() or {}
                floor_data['id'] = floor_doc.id
                floors.append(floor_data)

            building_data['floors'] = sorted(floors, key=lambda x: x.get('floor', 0))
            buildings.append(building_data)

        return jsonify(buildings), 200
    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@building_bp.route('/<building_id>', methods=['GET'])
def get_building_with_floors(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        ref = db.collection('buildings').document(building_id)
        snap = ref.get()
        if not snap.exists:
            return jsonify({"error": "Building not found."}), 404

        data = snap.to_dict() or {}
        for k, v in list(data.items()):
            if isinstance(v, GeoPoint):
                data[k] = [v.latitude, v.longitude]

        floors = []
        for d in ref.collection('floors').stream():
            fd = d.to_dict() or {}
            fd['id'] = d.id
            floors.append(fd)

        sorted_floors = sorted(floors, key=lambda x: x.get('floor', 0))
        response = {
            'id': ref.id,
            'name': data.get('name', '< Unnamed Building >'),
            'NE_bound': data.get('NE_bound'),
            'SW_bound': data.get('SW_bound'),  # fixed: was 'SE_bound'
            'floors': sorted_floors
        }
        return jsonify(response), 200
    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
