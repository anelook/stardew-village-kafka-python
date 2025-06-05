
import os
import time
from dotenv import load_dotenv
from confluent_kafka.avro import AvroProducer, CachedSchemaRegistryClient, loads

load_dotenv()

# ─── Environment Variables ─────────────────────────────────────────────────────
KAFKA_BROKER           = os.getenv("KAFKA_BROKER")
KAFKA_CLIENT_ID        = os.getenv("KAFKA_CLIENT_ID")
KAFKA_USERNAME         = os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD         = os.getenv("KAFKA_PASSWORD")

SCHEMA_REGISTRY_URL    = os.getenv("SCHEMA_REGISTRY_URL")
SCHEMA_REGISTRY_API_KEY   = os.getenv("SCHEMA_REGISTRY_API_KEY")
SCHEMA_REGISTRY_API_SECRET= os.getenv("SCHEMA_REGISTRY_API_SECRET")

TOPIC = os.getenv("KAFKA_VILLAGERS_LOCATION_TOPIC")
# ────────────────────────────────────────────────────────────────────────────────

producer: AvroProducer = None

# The Avro schema must be a valid JSON string
villager_location_schema_str = """
{
  "type": "record",
  "name": "villagerMovementRecord",
  "namespace": "stardew",
  "fields": [
    { "name": "name",      "type": "string" },
    { "name": "x",         "type": "float" },
    { "name": "y",         "type": "float" },
    { "name": "timestamp", "type": { "type": "long", "logicalType": "timestamp-millis" } }
  ]
}
"""


def init_movement_producer():
    global producer

    schema_registry_conf = {
        "url": SCHEMA_REGISTRY_URL,
        "basic.auth.user.info": f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"
    }
    schema_registry_client = CachedSchemaRegistryClient(schema_registry_conf)

    avro_producer_conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": KAFKA_CLIENT_ID,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": KAFKA_USERNAME,
        "sasl.password": KAFKA_PASSWORD
    }

    schema_obj = loads(villager_location_schema_str)

    producer = AvroProducer(
        avro_producer_conf,
        default_value_schema=schema_obj,
        schema_registry=schema_registry_client
    )

    print("Movement AvroProducer initialized and schema ready.")


def send_villager_location_update(villager_name: str, x: float, y: float):
    global producer
    if producer is None:
        raise RuntimeError("Movement producer not initialized. Call init_movement_producer() first.")

    payload = {
        "name": villager_name,
        "x": x,
        "y": y,
        "timestamp": int(time.time() * 1000)
    }

    try:
        producer.produce(topic=TOPIC, value=payload)
        producer.flush()
    except Exception as e:
        print("Error sending update to Kafka:", e)
