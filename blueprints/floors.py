from flask import Blueprint, request, jsonify
from firebase_init import db, bucket
from google.cloud.firestore_v1 import GeoPoint  # keep consistent

floors_bp = Blueprint('floors', __name__)

@floors_bp.route('/<building_id>', methods=['GET'])
def get_all_floor(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        ref = db.collection('buildings').document(building_id).collection('floors')
        floors = []
        for doc in ref.stream():
            d = doc.to_dict() or {}
            d['id'] = doc.id
            floors.append(d)
        return jsonify(sorted(floors, key=lambda x: x.get('floor', 0))), 200
    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@floors_bp.route('/<building_id>', methods=['POST'])
def add_floor(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        data = request.get_json(silent=True) or {}
        if 'floor_plan_url' not in data:
            return jsonify({"error": "Missing 'floor_plan_url' field in request body."}), 400

        building_ref = db.collection('buildings').document(building_id)
        if not building_ref.get().exists:
            return jsonify({"error": "Building not found."}), 404

        floors_ref = building_ref.collection('floors')
        latest = next(floors_ref.order_by('floor', direction='DESCENDING').limit(1).stream(), None)
        new_floor_number = (latest.to_dict()['floor'] + 1) if latest else 1

        _, new_floor_ref = floors_ref.add({'floor': new_floor_number, 'floor_plan_url': data['floor_plan_url']})
        return jsonify({"message": "Floor added successfully.", "id": new_floor_ref.id, "floor": new_floor_number}), 201
    except Exception as e:
        print(f"An error occurred during floor creation: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@floors_bp.route('/getFloorPlan', methods=['GET'])
def get_floor_plan():
    file_name = request.args.get('fileName')
    if not file_name:
        return jsonify({"error": "Missing 'fileName' query parameter."}), 400
    try:
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File '{file_name}' not found."}), 404
        return jsonify({"url": blob.public_url}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error."}), 500
