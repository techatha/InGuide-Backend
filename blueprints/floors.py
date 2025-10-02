from flask import Blueprint, request, jsonify
from app import db, bucket
from google.cloud.firestore import GeoPoint

floors_bp = Blueprint('floors', __name__)


@floors_bp.route('/<building_id>/floors', methods=['GET'])
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


@floors_bp.route('/<building_id>/floors', methods=['POST'])
def add_floor_plan(building_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required."}), 400

        floor_id = data['id']
        floor_copy = data.copy()
        floor_copy.pop('id')

        building_ref = db.collection('buildings').document(building_id)
        floor_ref = building_ref.collection('floors').document(floor_id)
        floor_ref.set(floor_copy)

        return jsonify({"status": "success", "message": f"Floor {floor_id} added."}), 201
    except Exception as e:
        print(f"Error adding a floor: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@floors_bp.route('/<building_id>/floors/<floor_id>', methods=['PATCH'])
def update_floor_plan(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400
        if 'floor_plan_url' not in data:
            return jsonify({"error": "Missing floor_plan_url parameter"}), 400

        building_ref = db.collection('buildings').document(building_id)
        floor_ref = building_ref.collection('floors').document(floor_id)

        floor_ref.update({"floor_plan_url": data['floor_plan_url']})

        return jsonify({"message": f"Floor {floor_id} updated successfully."}), 200
    except Exception as e:
        print(f"Error updating a floor: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@floors_bp.route('/<building_id>/floors/<floor_id>', methods=['DELETE'])
def delete_floor(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        building_ref = db.collection('buildings').document(building_id)
        floors_ref = building_ref.collection('floors')

        target_snapshot = floors_ref.document(floor_id).get()
        if not target_snapshot.exists:
            return jsonify({"error": "Floor not found"}), 404

        target_floor = target_snapshot.to_dict().get('floor')

        # Fetch all floors
        floor_docs = list(floors_ref.stream())
        floors = []
        for doc in floor_docs:
            data = doc.to_dict()
            data['id'] = doc.id
            floors.append(data)

        # Sort and shift down floors above the deleted one
        for floor in floors:
            if floor['floor'] > target_floor:
                floors_ref.document(floor['id']).update({"floor": floor['floor'] - 1})

        # --- Cascade delete subcollections ---
        floor_doc_ref = floors_ref.document(floor_id)

        def delete_subcollection(subcoll_name):
            sub_ref = floor_doc_ref.collection(subcoll_name)
            for doc in sub_ref.stream():
                doc.reference.delete()

        # Delete known subcollections (POIs, beacons, path_nodes)
        delete_subcollection("POIs")
        delete_subcollection("beacons")
        delete_subcollection("path_nodes")

        # Finally, delete the floor document itself
        floor_doc_ref.delete()

        return jsonify({"message": f"Floor {floor_id} and its data deleted successfully."}), 200

    except Exception as e:
        print(f"Error deleting a floor: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
