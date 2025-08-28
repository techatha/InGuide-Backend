from flask import Blueprint, request, jsonify
from google.cloud.firestore_v1 import GeoPoint

from app import db

building_bp = Blueprint('building', __name__)


@building_bp.route('', methods=['GET'])
def get_buildings():
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        building_ref = db.collection('buildings')
        building_docs = list(building_ref.stream())
        buildings = []
        for doc in building_docs:
            building_data = doc.to_dict()
            building_data['id'] = doc.id

            for key, value in building_data.items():
                if isinstance(value, GeoPoint):
                    building_data[key] = [value.latitude, value.longitude]

            floors_ref = doc.reference.collection('floors')
            floor_docs = list(floors_ref.stream())

            floors = []
            for floor_doc in floor_docs:
                floor_data = floor_doc.to_dict()
                floor_data['id'] = floor_doc.id
                floors.append(floor_data)

            building_data['floors'] = sorted(floors, key=lambda x: x['floor'])
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
        building_ref = db.collection('buildings').document(building_id)
        building_doc = building_ref.get()

        if not building_doc.exists:
            return jsonify({"error": "Building not found."}), 404

        building_data = building_doc.to_dict()

        for key, value in building_data.items():
            if isinstance(value, GeoPoint):
                building_data[key] = [value.latitude, value.longitude]

        floor_ref = building_ref.collection('floors')
        floor_docs = list(floor_ref.stream())
        floors = []
        for doc in floor_docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            floors.append(log_data)

        sorted_floors = sorted(floors, key=lambda x: x['floor'])
        response = {
            'id': building_ref.id,
            'name': building_data.get('name', '< Unnamed Building >'),
            'NE_bound': building_data.get('NE_bound', '< Unnamed Building >'),
            'SW_bound': building_data.get('SE_bound', '< Unnamed Building >'),
            'floors': sorted_floors
        }
        return jsonify(response), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@building_bp.route('', methods=['POST'])
def add_building():
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        data = request.get_json()
        if 'name' not in data:
            return jsonify({"error": "Missing 'name' field in request body."}), 400

        building_name = data['name']
        _, building_ref = db.collection('buildings').add({'name': building_name})
        floor_data = {
            'floor': 1
        }
        building_ref.collection('floors').add(floor_data)

        return jsonify({
            "message": "Building and first floor added successfully.",
            "success": True,
            "building": {
                "id": building_ref.id,
                "name": building_name
            }
        }), 201

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@building_bp.route('/<building_id>', methods=['DELETE'])
def delete_building(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        building_ref = db.collection('buildings').document(building_id)
        building = building_ref.get()

        if not building.exists:
            return jsonify({"error": "Building not found."}), 404

        floors_ref = building_ref.collection('floors')
        floors_docs = floors_ref.stream()
        for doc in floors_docs:
            doc.reference.delete()

        building_ref.delete()
        return jsonify({"message": "Building deleted successfully."}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

