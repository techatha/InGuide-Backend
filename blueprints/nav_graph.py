from flask import Blueprint, request, jsonify
from app import db

nav_graph_bp = Blueprint('nav_graph', __name__)


@nav_graph_bp.route('/<building_id>/<floor_id>', methods=['POST'])
def save_or_update_navigation_graph(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required."}), 400

        # Reference to the floor document
        floor_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)

        # Check if floor exists
        if not floor_ref.get().exists:
            return jsonify({"error": f"Floor '{floor_id}' not found in building '{building_id}'."}), 404

        # Update the graph field
        floor_ref.update({
            "graph": data,
        })

        return jsonify({"message": "Navigation graph saved successfully."}), 200

    except Exception as e:
        print(f"Error saving navigation graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@nav_graph_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_navigation_graph(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        floor_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)
        doc = floor_ref.get()

        if not doc.exists:
            return jsonify({"error": f"Floor '{floor_id}' not found in building '{building_id}'."}), 404

        floor_data = doc.to_dict()
        graph = floor_data.get("graph")

        if not graph:
            return jsonify({"error": "No navigation graph found for this floor."}), 404

        return jsonify(graph), 200

    except Exception as e:
        print(f"Error fetching navigation graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@nav_graph_bp.route('/<building_id>/portal-groups', methods=['GET'])
def get_portal_groups(building_id):
    """
    Scans all floor graphs in a building and returns a unique
    list of all portalGroup names currently in use.
    """
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        portal_names = set()  # Use a set for automatic de-duplication
        floors_ref = db.collection('buildings').document(building_id).collection('floors')
        all_floors = floors_ref.stream()

        for floor in all_floors:
            floor_data = floor.to_dict()
            graph = floor_data.get("graph")

            if graph and graph.get("nodes"):
                for node in graph["nodes"]:
                    if node.get("portalGroup") and node["portalGroup"]:
                        portal_names.add(node["portalGroup"])

        # Return the set as a JSON list
        return jsonify(list(portal_names)), 200

    except Exception as e:
        print(f"Error fetching portal groups: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@nav_graph_bp.route('/<building_id>/supergraph', methods=['GET'])
def get_super_graph(building_id):
    """
    Fetches all floor graphs for a building, merges them, and
    connects all nodes that share the same 'portalGroup' name.
    """
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        # 1. Get all floor documents for the building
        floors_ref = db.collection('buildings').document(building_id).collection('floors')
        all_floors = floors_ref.stream()

        super_nodes = []
        super_adj = {}
        # This will store: {"Main Stairs": ["f1_stair_id", "f2_stair_id"]}
        portal_map = {}

        # --- LOOP 1: Merge all graphs and find portals ---
        for floor in all_floors:
            floor_data = floor.to_dict()
            graph = floor_data.get("graph")

            # Skip floor if it has no graph
            if not graph or not graph.get("nodes") or not graph.get("adjacencyList"):
                print(f"Skipping floor {floor.id}, graph data is incomplete.")
                continue

            # Add this floor's nodes and edges to the super graph
            super_nodes.extend(graph.get("nodes", []))
            super_adj.update(graph.get("adjacencyList", {}))

            # Find all nodes in this graph that are portals
            for node in graph.get("nodes", []):
                # Check for the "portalGroup" name
                if node.get("portalGroup"):
                    group_name = node["portalGroup"]
                    node_id = node["id"]

                    # Add this node to the portal map
                    if group_name not in portal_map:
                        portal_map[group_name] = []
                    portal_map[group_name].append(node_id)

        # --- LOOP 2: Connect all portals ---
        # "Cost" to use stairs/elevator (e.g., 30 seconds)
        FLOOR_CHANGE_WEIGHT = 30

        for group_name, node_ids in portal_map.items():
            # Connect every node in this group to every other node in the same group
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    node_id_a = node_ids[i]
                    node_id_b = node_ids[j]

                    # Add edge A -> B
                    if node_id_a not in super_adj: super_adj[node_id_a] = []
                    super_adj[node_id_a].append({
                        "targetNodeId": node_id_b,
                        "weight": FLOOR_CHANGE_WEIGHT
                    })

                    # Add edge B -> A
                    if node_id_b not in super_adj: super_adj[node_id_b] = []
                    super_adj[node_id_b].append({
                        "targetNodeId": node_id_a,
                        "weight": FLOOR_CHANGE_WEIGHT
                    })

        # Return the final merged graph
        return jsonify({"nodes": super_nodes, "adjacencyList": super_adj}), 200

    except Exception as e:
        print(f"Error building super graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
