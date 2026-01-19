import json
import logging
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from db import get_conn  # твой модуль db/init.py с get_conn()
from prometheus_client import Counter, Gauge, start_http_server


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("map-consumer")

TOPIC = "scooter_events"

# === Prometheus metrics ===

EVENTS_TOTAL = Counter(
    "scooter_events_total",
    "Total number of scooter events",
    ["event_type"]
)

SCOOTER_BATTERY = Gauge(
    "scooter_battery",
    "Current scooter battery level",
    ["scooter_id"]
)

SCOOTER_LAST_SEEN = Gauge(
    "scooter_last_seen_timestamp",
    "Last event timestamp per scooter",
    ["scooter_id"]
)

def create_consumer():
    """Создаём KafkaConsumer с авто-переподключением"""
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=["kafka:9092"],
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                group_id="map_consumer_v1"
            )
            logger.info("Kafka consumer initialized")
            return consumer
        except NoBrokersAvailable:
            logger.warning("Kafka not ready yet, retrying in 3s...")
            time.sleep(3)


def parse_ts(ts):
    """Конвертируем ts в datetime для Postgres"""
    if ts is None:
        return None
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return None
    return ts  # если уже datetime


def main():
    start_http_server(8000)
    consumer = create_consumer()
    conn = get_conn()
    conn.autocommit = True
    logger.info("Consumer started, waiting for events...")

    for msg in consumer:
        event = msg.value
        data = event.get("data")

        EVENTS_TOTAL.labels(
            event_type=event.get("event_type", "unknown")
        ).inc()

        # Игнорируем события без координат
        if not data or "lat" not in data or "lon" not in data:
            continue

        ts = parse_ts(event.get("ts"))

        if data.get("battery") is not None:
            SCOOTER_BATTERY.labels(
                scooter_id=str(event["scooter_id"])
            ).set(data["battery"])

        if ts is not None:
            SCOOTER_LAST_SEEN.labels(
                scooter_id=str(event["scooter_id"])
            ).set(ts.timestamp())

        try:
            with conn.cursor() as cur:
                # 1️⃣ Обновляем текущее состояние
                cur.execute(
                    """
                    INSERT INTO scooter_state (scooter_id, lat, lon, battery, ts)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (scooter_id)
                    DO UPDATE SET
                        lat = EXCLUDED.lat,
                        lon = EXCLUDED.lon,
                        battery = EXCLUDED.battery,
                        ts = EXCLUDED.ts
                    """,
                    (event["scooter_id"], data["lat"], data["lon"], data.get("battery"), ts)
                )

                # 2️⃣ Сохраняем историю маршрута
                cur.execute(
                    """
                    INSERT INTO scooter_route (scooter_id, lat, lon, battery, ts)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (event["scooter_id"], data["lat"], data["lon"], data.get("battery"), ts)
                )

            logger.info("Updated scooter %s at lat=%s lon=%s", event["scooter_id"], data["lat"], data["lon"])

        except Exception:
            logger.exception("Error updating scooter_state or scooter_route")


if __name__ == "__main__":
    main()
