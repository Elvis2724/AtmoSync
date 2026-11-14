-- ============================================================================
-- AtmoSync Relational Analytical Warehouse Schema (`powerbi db/database/schema.sql`)
-- Used by SQLite (`atmosync.db`) to store raw Kafka stream, staging, and mart tables.
-- ============================================================================

CREATE TABLE IF NOT EXISTS raw_iot_stream (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TEXT,
    container_id TEXT,
    kafka_topic TEXT,
    kafka_partition INTEGER,
    raw_payload_json TEXT
);

CREATE TABLE IF NOT EXISTS stg_telemetry (
    event_timestamp TEXT,
    container_id TEXT,
    commodity_id TEXT,
    temp_c REAL,
    humidity_pct REAL,
    vibration_g REAL,
    co2_ppm REAL,
    ethylene_ppm REAL,
    lat REAL,
    lon REAL,
    speed_kmh REAL,
    compressor_status TEXT,
    quality_remaining_pct REAL
);

CREATE TABLE IF NOT EXISTS mart_spoilage_arbitrage (
    snapshot_timestamp TEXT,
    container_id TEXT,
    commodity_name TEXT,
    compressor_status TEXT,
    temp_c REAL,
    humidity_pct REAL,
    vibration_g REAL,
    quality_remaining_pct REAL,
    degradation_multiplier REAL,
    time_to_spoilage_hrs REAL,
    primary_market TEXT,
    primary_eta_hrs REAL,
    primary_expected_value_usd REAL,
    recommended_secondary_market TEXT,
    secondary_eta_hrs REAL,
    secondary_net_value_usd REAL,
    spoilage_arbitrage_usd REAL,
    risk_status TEXT,
    recommended_action TEXT
);
