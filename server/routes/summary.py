from flask import Blueprint, request, jsonify
from server.conversation_summary_llm import generate_conversation_summary

summary_bp = Blueprint("summary", __name__)

@summary_bp.route("/summary", methods=["POST"])
def summary():
    """
    Expects JSON body:
      {
        "name": <string>,
        "partnerName": <string>,
        "history": <list of strings>
      }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    name = data.get("name")
    partner_name = data.get("partnerName")
    history = data.get("history", [])

    try:
        reply = generate_conversation_summary(
            name=name,
            partner_name=partner_name,
            history=history
        )
        return jsonify({"reply": reply}), 200
    except Exception as e:
        print("OpenAI error:", e)
        return jsonify({"error": "LLM failed"}), 500
