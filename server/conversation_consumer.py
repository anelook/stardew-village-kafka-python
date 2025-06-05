
import os
import threading
from dotenv import load_dotenv
from confluent_kafka.avro import AvroConsumer
from confluent_kafka.avro.serializer import SerializerError

load_dotenv()

# Environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
SCHEMA_REGISTRY_API_KEY = os.getenv("SCHEMA_REGISTRY_API_KEY")
SCHEMA_REGISTRY_API_SECRET = os.getenv("SCHEMA_REGISTRY_API_SECRET")
CONVERSATION_TOPIC = os.getenv("KAFKA_CONVERSATION_TOPIC")
GROUP_ID = "villager-conversation-consumer"

consumer: AvroConsumer = None

def init_conversation_consumer(socketio):
    """
    Initialize an AvroConsumer that listens for conversation messages,
    decodes them, and emits each payload via Socket.IO under 'villagerConversationMessage'.
    """
    global consumer

    # Consumer configuration
    conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": KAFKA_CLIENT_ID,
        "group.id": GROUP_ID,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": KAFKA_USERNAME,
        "sasl.password": KAFKA_PASSWORD,
        "auto.offset.reset": "latest",  # start from new messages
        # Schema Registry settings
        "schema.registry.url": SCHEMA_REGISTRY_URL,
        "basic.auth.credentials.source": "USER_INFO",
        "basic.auth.user.info": f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}",
    }

    consumer = AvroConsumer(conf)
    consumer.subscribe([CONVERSATION_TOPIC])

    def _consume_loop():
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    print(f"Consumer error: {msg.error()}")
                    continue

                try:
                    value = msg.value()

                    from_user = value.get("from")
                    to_user = value.get("to")
                    text = value.get("message")
                    timestamp = value.get("timestamp")

                    print("📬 conversation →", {"from": from_user, "to": to_user, "text": text})

                    socketio.emit(
                        "villagerConversationMessage",
                        {"from": from_user, "to": to_user, "message": text, "timestamp": timestamp}
                    )
                except SerializerError as e:
                    print(f"Failed to deserialize message: {e}")
                except Exception as e:
                    print(f"Unexpected error processing message: {e}")
        finally:
            consumer.close()

    thread = threading.Thread(target=_consume_loop, daemon=True)
    thread.start()

    print("Kafka conversation‐consumer up and running…")
