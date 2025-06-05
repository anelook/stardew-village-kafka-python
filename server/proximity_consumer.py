
import os
import threading
import time
from dotenv import load_dotenv
from confluent_kafka.avro import AvroConsumer
from confluent_kafka.avro.serializer import SerializerError

load_dotenv()

# Environment variables for Kafka and Schema Registry
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
SCHEMA_REGISTRY_API_KEY = os.getenv("SCHEMA_REGISTRY_API_KEY")
SCHEMA_REGISTRY_API_SECRET = os.getenv("SCHEMA_REGISTRY_API_SECRET")
PROXIMITY_TOPIC = os.getenv("KAFKA_PROXIMITY_TOPIC")
GROUP_ID = "villager-proximity-consumer-8"

consumer: AvroConsumer = None

def init_movement_consumer(socketio):
    """
    Initialize an AvroConsumer that listens for villager-proximity messages,
    decodes them, and emits each payload via Socket.IO under 'villagersProximityIOEvent'.
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
        # Schema Registry config
        "schema.registry.url": SCHEMA_REGISTRY_URL,
        "basic.auth.credentials.source": "USER_INFO",
        "basic.auth.user.info": f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}",
    }

    consumer = AvroConsumer(conf)
    consumer.subscribe([PROXIMITY_TOPIC])

    def _consume_loop():
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    # You can add more robust error handling here
                    print(f"Consumer error: {msg.error()}")
                    continue

                try:
                    value = msg.value()  # decoded Python dict from Avro
                    # Emit the decoded object to all connected clients
                    socketio.emit("villagersProximityIOEvent", value)
                except SerializerError as e:
                    print(f"Failed to deserialize message: {e}")
                except Exception as e:
                    print(f"Unexpected error processing message: {e}")
        finally:
            consumer.close()

    # Run the consumer loop in a separate daemon thread
    thread = threading.Thread(target=_consume_loop, daemon=True)
    thread.start()

    print("Kafka proximity‐consumer up and running...")
