
import os
import time
from dotenv import load_dotenv
from confluent_kafka.avro import AvroProducer, CachedSchemaRegistryClient, loads

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID")
KAFKA_USERNAME = os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
SCHEMA_REGISTRY_API_KEY = os.getenv("SCHEMA_REGISTRY_API_KEY")
SCHEMA_REGISTRY_API_SECRET = os.getenv("SCHEMA_REGISTRY_API_SECRET")

CONVERSATION_TOPIC = os.getenv("KAFKA_CONVERSATION_TOPIC")

producer: AvroProducer = None

conversation_schema_str = """
{
  "type": "record",
  "name": "VillagerConversationMessage",
  "namespace": "stardew",
  "fields": [
    { "name": "from",    "type": "string" },
    { "name": "to",      "type": "string" },
    { "name": "message", "type": "string" },
    { "name": "timestamp", "type": { "type": "long", "logicalType": "timestamp-millis" } }
  ]
}
"""

def init_conversation_producer():
    global producer

    # Schema Registry client
    schema_registry_conf = {
        "url": SCHEMA_REGISTRY_URL,
        "basic.auth.user.info": f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"
    }
    schema_registry_client = CachedSchemaRegistryClient(schema_registry_conf)

    # Producer configuration
    avro_producer_conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": KAFKA_CLIENT_ID,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": KAFKA_USERNAME,
        "sasl.password": KAFKA_PASSWORD,
        "schema.registry.url": SCHEMA_REGISTRY_URL,
        "schema.registry.basic.auth.user.info": f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"
    }

    # Parse schema
    schema_obj = loads(conversation_schema_str)

    producer = AvroProducer(
        avro_producer_conf,
        default_value_schema=schema_obj,
        schema_registry=schema_registry_client
    )

    print("Conversation AvroProducer initialized and schema registered.")

def send_conversation_message(from_user: str, to_user: str, message: str):
    global producer
    if producer is None:
        raise RuntimeError("Conversation producer not initialized. Call init_conversation_producer() first.")

    payload = {
        "from": from_user,
        "to": to_user,
        "message": message,
        "timestamp": int(time.time() * 1000)
    }

    try:
        producer.produce(topic=CONVERSATION_TOPIC, value=payload)
        producer.flush()
    except Exception as e:
        print("Error sending conversation message to Kafka:", e)
