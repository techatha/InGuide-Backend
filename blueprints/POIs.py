from flask import Blueprint, request, jsonify
from app import db, bucket  # Assuming 'bucket' is from GCS
from google.cloud.firestore import GeoPoint

POIs_bp = Blueprint('POIs', __name__)


@POIs_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_POIs(building_id, floor_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' parameter."}), 400
    if not floor_id:
        return jsonify({"error": "Missing 'floor_id' parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        # Correctly get the floor document
        floor_doc_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)
        floor_doc = floor_doc_ref.get()

        if not floor_doc.exists:
            return jsonify({"error": f"Floor '{floor_id}' not found for building '{building_id}'."}), 404

        POIs_ref = floor_doc_ref.collection('POIs')
        POIs_docs = POIs_ref.stream()

        POIs = []
        for doc in POIs_docs:
            poi_data = doc.to_dict()
            poi_data['id'] = doc.id
            poi_data['floor'] = floor_doc.get('floor')  # Use the floor_doc
            for key, value in poi_data.items():
                if isinstance(value, GeoPoint):
                    poi_data[key] = [value.latitude, value.longitude]
            POIs.append(poi_data)

        return jsonify(POIs), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/<floor_id>', methods=['POST'])
def save_POIs(building_id, floor_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' parameter."}), 400
    if not floor_id:
        return jsonify({"error": "Missing 'floor_id' parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        POIs_data = data.get('pois')
        if not isinstance(POIs_data, list):
            return jsonify({"error": "Invalid 'pois' data. Must be a list."}), 400

        floor_doc_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)
        floor_doc = floor_doc_ref.get()

        if not floor_doc.exists:
            return jsonify({"error": f"Floor '{floor_id}' not found for building '{building_id}'."}), 404

        POIs_ref = floor_doc_ref.collection('POIs')
        batch = db.batch()

        # Clear all existing POIs in the collection
        for doc in POIs_ref.stream():
            batch.delete(doc.reference)

        # Add all new POIs from the request
        for POI in POIs_data:
            if 'id' not in POI:
                return jsonify({"error": "Each POI must have an 'id'."}), 400

            poi_id = POI['id']
            POI_copy = POI.copy()
            POI_copy.pop('id')  # Remove the ID field before saving
            if 'location' in POI_copy and isinstance(POI_copy['location'], list) and len(POI_copy['location']) == 2:
                POI_copy['location'] = GeoPoint(POI_copy['location'][0], POI_copy['location'][1])

            POI_doc_ref = POIs_ref.document(poi_id)
            batch.set(POI_doc_ref, POI_copy)

        batch.commit()
        return jsonify({"status": "success", "message": "POIs saved successfully."}), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/<floor_id>/<poi_id>', methods=['PATCH'])
def update_poi(building_id, floor_id, poi_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' parameter."}), 400
    if not floor_id:
        return jsonify({"error": "Missing 'floor_id' parameter."}), 400
    if not poi_id:
        return jsonify({"error": "Missing 'poi_id' parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400

        # Example expected payload: {"location": [13.7563, 100.5018]}
        update_data = {}
        if 'location' in data and isinstance(data['location'], list) and len(data['location']) == 2:
            update_data['location'] = GeoPoint(data['location'][0], data['location'][1])

        # Update POI doc
        poi_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id).collection('POIs').document(poi_id)
        poi_ref.update(update_data)

        return jsonify({"status": "success", "message": f"POI {poi_id} updated successfully."}), 200

    except Exception as e:
        print(f"Error updating POI: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('POI_info/<building_id>/<poi_id>', methods=['GET'])
def get_POI(building_id, poi_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' query parameter."}), 400
    if not poi_id:
        return jsonify({"error": "Missing 'poi_id' query parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        # Query across all floors for the given POI
        floor_query = db.collection('buildings').document(building_id).collection('floors')
        for floor_doc in floor_query.stream():
            poi_doc_ref = floor_doc.reference.collection('POIs').document(poi_id)
            poi_snapshot = poi_doc_ref.get()
            if poi_snapshot.exists:
                query_result = poi_snapshot.to_dict()
                query_result['id'] = poi_snapshot.id
                query_result['floor'] = floor_doc.get('floor')
                for key, value in query_result.items():
                    if isinstance(value, GeoPoint):
                        query_result[key] = [value.latitude, value.longitude]
                return jsonify(query_result), 200

        # If the loop finishes without finding the POI
        return jsonify({"error": f"Cannot find poi id: {poi_id} for building {building_id}."}), 404

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

