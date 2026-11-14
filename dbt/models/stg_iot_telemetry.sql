-- ============================================================================
-- dbt Model: dbt/models/stg_iot_telemetry.sql
-- Phase 2: Cleans raw Kafka JSON IoT payloads landing in Snowflake / SQLite
-- ============================================================================

WITH raw_kafka_stream AS (
    SELECT
        event_id,
        CAST(event_timestamp AS TIMESTAMP) AS event_ts,
        container_id,
        kafka_topic,
        kafka_partition,
        raw_payload_json
    FROM {{ source('raw_iot', 'raw_iot_stream') }}
),

parsed_payloads AS (
    SELECT
        event_id,
        event_ts,
        container_id,
        JSON_EXTRACT(raw_payload_json, '$.commodity_id')                     AS commodity_id,
        CAST(JSON_EXTRACT(raw_payload_json, '$.sensors.internal_temp_c') AS FLOAT) AS temp_c,
        CAST(JSON_EXTRACT(raw_payload_json, '$.sensors.humidity_pct') AS FLOAT)    AS humidity_pct,
        CAST(JSON_EXTRACT(raw_payload_json, '$.sensors.vibration_g') AS FLOAT)     AS vibration_g,
        CAST(JSON_EXTRACT(raw_payload_json, '$.sensors.co2_ppm') AS FLOAT)         AS co2_ppm,
        CAST(JSON_EXTRACT(raw_payload_json, '$.sensors.ethylene_ppm') AS FLOAT)    AS ethylene_ppm,
        CAST(JSON_EXTRACT(raw_payload_json, '$.gps.lat') AS FLOAT)                 AS current_lat,
        CAST(JSON_EXTRACT(raw_payload_json, '$.gps.lon') AS FLOAT)                 AS current_lon,
        CAST(JSON_EXTRACT(raw_payload_json, '$.gps.speed_kmh') AS FLOAT)           AS speed_kmh,
        JSON_EXTRACT(raw_payload_json, '$.reefer_unit.compressor_status')    AS compressor_status
    FROM raw_kafka_stream
    WHERE container_id IS NOT NULL
)

SELECT *
FROM parsed_payloads
WHERE temp_c BETWEEN -35.0 AND 55.0
  AND humidity_pct BETWEEN 0.0 AND 100.0
