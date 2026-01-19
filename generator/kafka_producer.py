import time
import json
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import os

def create_producer():
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8")
            )
            return producer
        except NoBrokersAvailable:
            print("Kafka not ready, retrying in 3s...")
            time.sleep(3)
