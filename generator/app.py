import time
import json
import random
import logging
from datetime import datetime

from db import get_conn
from kafka_producer import create_producer
from metrics import events_generated, start_metrics
from routing import CityRouter
from lifecycle import generate_event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("generator")

# Kafka
producer = create_producer()
TOPIC = "scooter_events"

def load_scooters(conn, router):
    """Загружаем самокаты из базы и привязываем к случайным узлам карты"""
    with conn.cursor() as cur:
        cur.execute("SELECT id, status, battery FROM scooters")
        rows = cur.fetchall()

    scooters = []
    for r in rows:
        node = router.random_node()
        lat, lon = router.node_coords(node)
        scooters.append({
            "id": r[0],
            "status": r[1],
            "battery": r[2],
            "node": node,
            "lat": lat,
            "lon": lon,
            "route": [],
            "route_idx": 0
        })
    return scooters

def main():
    start_metrics()
    conn = get_conn()
    conn.autocommit = True
    router = CityRouter()
    scooters = load_scooters(conn, router)

    while True:
        scooter = random.choice(scooters)
        event = generate_event(scooter, router)
        if event is None:
            time.sleep(0.05)
            continue

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO events (scooter_id,event_type,ts,data) VALUES (%s,%s,%s,%s)",
                    (event["scooter_id"], event["event_type"], event["ts"], json.dumps(event["data"], default=str))
                )
                cur.execute(
                    "UPDATE scooters SET status=%s,battery=%s,lat=%s,lon=%s,updated_at=now() WHERE id=%s",
                    (scooter["status"], scooter["battery"], scooter["lat"], scooter["lon"], scooter["id"])
                )
            events_generated.labels(event["event_type"]).inc()

            # Kafka — только bytes
            producer.send(TOPIC, event)

            # Лог — читаемый dict
            logger.info(event)
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            time.sleep(1)

        time.sleep(0.2)

if __name__ == "__main__":
    main()
