from flask import Blueprint, request, jsonify
from app import db, bucket

floors_bp = Blueprint('floors', __name__)


@floors_bp.route('/', methods=['GET'])
def get_all_floor():
    building_id = request.args.get('building_id')
    if not building_id:
        return jsonify({"error": "Missing 'building_id' query parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        building_ref = db.collection('buildings').document(building_id)
        floor_ref = building_ref.collection('floors')
        floor_docs = list(floor_ref.stream())
        floors = []
        for doc in floor_docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            floors.append(log_data)
        return jsonify(floors), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@floors_bp.route('/getFloorPlan', methods=['GET'])
def get_floor_plan():
    file_name = request.args.get('floor')
    if not file_name:
        return jsonify({"error": "Missing 'fileName' query parameter."}), 400
    try:
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File '{file_name}' not found."}), 404
        url = blob.public_url
        return jsonify({"url": url}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error."}), 500
