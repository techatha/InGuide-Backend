from flask import Blueprint, request, jsonify
from firebase_init import db
from google.cloud.firestore_v1 import GeoPoint

paths_bp = Blueprint('paths', __name__)

@paths_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_path(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        nodes_ref = db.collection('buildings').document(building_id)\
                      .collection('floors').document(floor_id)\
                      .collection('path_nodes')

        path_data = {"nodes": [], "adjacencyList": {}}
        for doc in nodes_ref.stream():
            data = doc.to_dict() or {}
            path_data["nodes"].append({
                "id": doc.id,
                "coordinates": [data['coordinates'].latitude, data['coordinates'].longitude]
            })
            if 'adjacencyList' in data:
                path_data["adjacencyList"][doc.id] = data['adjacencyList']
        return jsonify(path_data), 200
    except Exception as e:
        print(f"An error occurred during path retrieval: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@paths_bp.route('/save/<building_id>/<floor_id>', methods=['POST'])
def save_path(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500
    try:
        data = request.get_json(silent=True) or {}
        nodes_data = data.get('nodes')
        adjacency_list_data = data.get('adjacencyList')

        if not nodes_data or adjacency_list_data is None:
            return jsonify({"error": "Missing required data."}), 400

        nodes_ref = db.collection('buildings').document(building_id)\
                      .collection('floors').document(floor_id)\
                      .collection('path_nodes')

        batch = db.batch()
        for doc in nodes_ref.stream():
            batch.delete(doc.reference)

        for node in nodes_data:
            node_doc_ref = nodes_ref.document(node['id'])
            batch.set(node_doc_ref, {
                'coordinates': GeoPoint(node['coordinates'][0], node['coordinates'][1]),
                'adjacencyList': adjacency_list_data.get(node['id'], []),
            })
        batch.commit()
        return jsonify({"message": "Path data saved successfully."}), 200
    except Exception as e:
        print(f"An error occurred during path save: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
