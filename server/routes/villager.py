from flask import Blueprint, request, jsonify
from server.villager_response_llm import generate_villager_reply

villager_bp = Blueprint("villager", __name__)

@villager_bp.route("/reply", methods=["POST"])
def reply():
    """
    Expects JSON body with keys:
      - name
      - metadata (object)
      - partnerName
      - partnerMetadata (object)
      - history (array of strings)
      - heardMessage (string)
      - relevantMemories (object or string)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    name = data.get("name")
    metadata = data.get("metadata", {})
    partner_name = data.get("partnerName")
    partner_metadata = data.get("partnerMetadata", {})
    history = data.get("history", [])
    heard_message = data.get("heardMessage")
    relevant_memories = data.get("relevantMemories", {})

    try:
        reply_text = generate_villager_reply(
            name=name,
            metadata=metadata,
            partner_name=partner_name,
            partner_metadata=partner_metadata,
            history=history,
            heard_message=heard_message,
            relevant_memories=relevant_memories,
        )
        return jsonify({"reply": reply_text}), 200
    except Exception as e:
        print("Error in generate_villager_reply:", e)
        return jsonify({"error": "LLM failed"}), 500
