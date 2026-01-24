from datetime import datetime, timedelta
import random

def generate_event(scooter, router):
    now = datetime.utcnow()

    # Если самокат на зарядке
    if scooter.get("charging_until"):
        if now >= scooter["charging_until"]:
            scooter["battery"] = 100
            scooter["charging_until"] = None
            scooter["status"] = "available"
        else:
            return None  # ещё заряжается

    # Батарея села → ставим на зарядку
    if scooter["battery"] <= 0:
        scooter["charging_until"] = now + timedelta(minutes=1)
        scooter["status"] = "charging"
        return {
            "scooter_id": scooter["id"],
            "event_type": "charging_start",
            "ts": now,
            "data": {}
        }

    # Аренда
    if scooter["status"] == "available" and random.random() < 0.05:
        dst = router.weighted_hotspot_node()
        scooter["route"] = router.shortest_path(scooter["node"], dst)
        scooter["route_idx"] = 0
        scooter["status"] = "rented"
        return {
            "scooter_id": scooter["id"],
            "event_type": "rental_start",
            "ts": now,
            "data": {}
        }

    #  Движение
    if scooter["status"] == "rented":
        if scooter["route_idx"] < len(scooter["route"]) - 1:
            scooter["route_idx"] += 1
            scooter["node"] = scooter["route"][scooter["route_idx"]]
            scooter["lat"], scooter["lon"] = router.node_coords(scooter["node"])
            scooter["battery"] -= 1

            return {
                "scooter_id": scooter["id"],
                "event_type": "location_update",
                "ts": now,
                "data": {
                    "lat": scooter["lat"],
                    "lon": scooter["lon"],
                    "battery": scooter["battery"]
                }
            }
        else:
            scooter["status"] = "available"
            return {
                "scooter_id": scooter["id"],
                "event_type": "rental_end",
                "ts": now,
                "data": {}
            }

    return None
