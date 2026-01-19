from prometheus_client import Counter, start_http_server

events_generated = Counter(
    "events_generated_total",
    "Total generated events",
    ["event_type"]
)

def start_metrics():
    start_http_server(8000)
