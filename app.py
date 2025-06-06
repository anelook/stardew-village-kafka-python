import os
from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO
from server.routes.villager import villager_bp
from server.routes.memory import memory_bp
from server.routes.summary import summary_bp
from server.movement_producer import init_movement_producer, send_villager_location_update
from server.proximity_consumer import init_movement_consumer
from server.conversation_producer import init_conversation_producer, send_conversation_message
from server.conversation_consumer import init_conversation_consumer

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder="public", static_url_path="")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')


socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(villager_bp, url_prefix="/api/villager")
app.register_blueprint(summary_bp, url_prefix="/api/general")
app.register_blueprint(memory_bp, url_prefix="/api/memory")

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")

@socketio.on("connect")
def handle_connect():
    print(f"Client connected.")

@socketio.on("villagerMessageFromClient")
def handle_villager_message_from_client(msg):
    """
    msg is expected to be a dict like:
      { "from": "villagerA", "to": "villagerB", "message": "Hello" }
    """
    try:
        send_conversation_message(msg["from"], msg["to"], msg["message"])
        print(f"Produced conversation message: {msg['from']} -> {msg['to']}")
    except Exception as e:
        print("Error sending conversation message to Kafka:", e)


@socketio.on("villagerLocationUpdated")
def handle_villager_location_updated(data):
    """
    data: { "name": "...", "x": <number>, "y": <number> }
    """
    try:
        send_villager_location_update(data["name"], data["x"], data["y"])
    except Exception as e:
        print("Error sending location update to Kafka:", e)


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected.")


def start_kafka_clients():
    try:
        init_movement_producer()
    except Exception as e:
        print("Failed to initialize Kafka movement producer:", e)
        exit(1)

    try:
        # Pass socketio so that your consumer can push real‐time updates if needed
        init_movement_consumer(socketio)
    except Exception as e:
        print("Failed to initialize Kafka movement consumer:", e)
        exit(1)

    try:
        init_conversation_producer()
    except Exception as e:
        print("Failed to initialize Kafka conversation producer:", e)
        exit(1)

    try:
        init_conversation_consumer(socketio)
    except Exception as e:
        print("Failed to initialize Kafka conversation consumer:", e)
        exit(1)


if __name__ == "__main__":
    start_kafka_clients()

    port = int(os.getenv("PORT", 3000))
    socketio.run(app, host="0.0.0.0", port=port)

