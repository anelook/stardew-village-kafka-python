from flask import Blueprint, request, jsonify
from server.store_long_term_memory import store_long_term_memory
from server.search_long_term_memory import search_long_term_memory

memory_bp = Blueprint("memory", __name__)

@memory_bp.route("/store", methods=["POST"])
def store():
    """
    Expects JSON body:
      {
        "conversation_summary": <string>,
        "name": <string>
      }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    conversation_summary = data.get("conversation_summary")
    name = data.get("name")

    try:
        reply = store_long_term_memory(
            conversation_summary=conversation_summary,
            name=name
        )
        return jsonify({"reply": reply}), 200
    except Exception as e:
        print("Memory error:", e)
        return jsonify({"error": "memory service failed"}), 500

@memory_bp.route("/search", methods=["POST"])
def search():
    """
    Expects JSON body:
      {
        "query": <string>,
        "name": <string>
      }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    query = data.get("query")
    name = data.get("name")

    try:
        reply = search_long_term_memory(
            query=query,
            name=name
        )
        return jsonify({"reply": reply}), 200
    except Exception as e:
        print("Memory error:", e)
        return jsonify({"error": "memory service failed"}), 500
