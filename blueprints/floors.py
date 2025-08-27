from flask import Blueprint, request, jsonify
from app import db, bucket
from google.cloud.firestore import GeoPoint

floors_bp = Blueprint('floors', __name__)


@floors_bp.route('/<building_id>', methods=['GET'])
def get_all_floor(building_id):
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

        sorted_floors = sorted(floors, key=lambda x: x['floor'])
        return jsonify(sorted_floors), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@floors_bp.route('/<building_id>', methods=['POST'])
def add_floor(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        if not data or 'floor_plan_url' not in data:
            return jsonify({"error": "Missing 'floor_plan_url' field or invalid JSON in request body."}), 400

        building_ref = db.collection('buildings').document(building_id)
        if not building_ref.get().exists:
            return jsonify({"error": "Building not found."}), 404

        floor_ref = building_ref.collection('floors')
        latest_floor_query = floor_ref.order_by('floor', direction='DESCENDING').limit(1).stream()
        latest_floor_doc = next(latest_floor_query, None)

        if latest_floor_doc:
            latest_floor_number = latest_floor_doc.to_dict()['floor']
            new_floor_number = latest_floor_number + 1
        else:
            new_floor_number = 1

        new_floor_data = {
            'floor': new_floor_number,
            'floor_plan_url': data['floor_plan_url']
        }

        _, new_floor_ref = floor_ref.add(new_floor_data)

        response = {
            "message": "Floor added successfully.",
            "id": new_floor_ref.id,
            "floor": new_floor_number
        }
        return jsonify(response), 201

    except Exception as e:
        print(f"An error occurred during floor creation: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@floors_bp.route('/<building_id>', methods=['DELETE'])
def delete_top_floor(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        # Get a reference to the floors subcollection
        floors_ref = db.collection('buildings').document(building_id).collection('floors')

        # Find the highest-numbered floor using a query
        latest_floor_query = floors_ref.order_by('floor', direction='DESCENDING').limit(1).stream()
        latest_floor_doc = next(latest_floor_query, None)

        # Check if a floor was found
        if not latest_floor_doc:
            return jsonify({"error": "No floors found to delete."}), 404

        # Delete the top floor document
        latest_floor_doc.reference.delete()

        return jsonify({"message": f"Floor {latest_floor_doc.to_dict()['floor']} deleted successfully."}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
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
