from flask import Blueprint, request, jsonify
from app import db
from google.cloud.firestore import GeoPoint

paths_bp = Blueprint('paths', __name__)


@paths_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_path(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        nodes_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id).collection(
            'path_nodes')
        nodes_docs = nodes_ref.stream()

        path_data = {
            "nodes": [],
            "adjacencyList": {}
        }

        for doc in nodes_docs:
            node_data = doc.to_dict()
            node_id = doc.id

            # Populate the nodes list
            path_data["nodes"].append({
                "id": node_id,
                "coordinates": [node_data['coordinates'].latitude, node_data['coordinates'].longitude],
                # --- FIX: Read the portalGroup property ---
                # Use .get() to safely handle nodes that don't have it
                "portalGroup": node_data.get('portalGroup', None)
            })

            # Populate the adjacency list
            if 'adjacencyList' in node_data:
                path_data["adjacencyList"][node_id] = node_data['adjacencyList']

        return jsonify(path_data), 200

    except Exception as e:
        print(f"An error occurred during path retrieval: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@paths_bp.route('/save/<building_id>/<floor_id>', methods=['POST'])
def save_path(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        nodes_data = data.get('nodes')
        adjacency_list_data = data.get('adjacencyList')

        if nodes_data is None or adjacency_list_data is None:
            return jsonify({"error": "Missing required data keys 'nodes' or 'adjacencyList'."}), 400

        nodes_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id).collection(
            'path_nodes')

        batch = db.batch()

        # Step 1: Delete all existing nodes (this is correct)
        for doc in nodes_ref.stream():
            batch.delete(doc.reference)

        # Step 2: Add the new nodes
        for node in nodes_data:
            node_adjacencies = adjacency_list_data.get(node['id'], [])
            node_doc_ref = nodes_ref.document(node['id'])

            # --- FIX: Correct Python syntax ---
            # Use node.get('portalGroup', None)
            # This is the Python equivalent of node.portalGroup || null
            node_doc_data = {
                'coordinates': GeoPoint(node['coordinates'][0], node['coordinates'][1]),
                'adjacencyList': node_adjacencies,
                'portalGroup': node.get('portalGroup', None)  # <-- Corrected line
            }
            batch.set(node_doc_ref, node_doc_data)

        batch.commit()

        return jsonify({"message": "Path data saved successfully."}), 200

    except Exception as e:
        print(f"An error occurred during path save: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500