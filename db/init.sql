-- extensions
CREATE EXTENSION IF NOT EXISTS postgis;

-- scooters (начальное состояние)
CREATE TABLE IF NOT EXISTS scooters (
    id SERIAL PRIMARY KEY,
    status TEXT NOT NULL,
    battery INT NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    updated_at TIMESTAMP DEFAULT now()
);

-- events (event store)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    scooter_id INT NOT NULL,
    event_type TEXT NOT NULL,
    ts TIMESTAMP NOT NULL,
    data JSONB
);

CREATE TABLE IF NOT EXISTS scooter_state (
    scooter_id INT PRIMARY KEY,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    battery INT,
    ts TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scooter_route (
    id SERIAL PRIMARY KEY,
    scooter_id INT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    battery INT,
    ts TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_scooter ON events(scooter_id);

-- создаем 100 самокатов
INSERT INTO scooters (status, battery)
SELECT 'available', 100
FROM generate_series(1, 100);
