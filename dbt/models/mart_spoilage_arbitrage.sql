-- ============================================================================
-- dbt Model: dbt/models/mart_spoilage_arbitrage.sql
-- Phase 3: Computes Arrhenius/Q10 Degradation Curves, Dynamic Time-to-Spoilage,
--          and Primary vs. Secondary Market Spoilage Arbitrage Margins ($)
-- ============================================================================

WITH latest_telemetry AS (
    SELECT *
    FROM {{ ref('stg_iot_telemetry') }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY container_id ORDER BY event_ts DESC) = 1
),

commodity_specs AS (
    SELECT * FROM {{ ref('dim_commodities') }}
),

degradation_calc AS (
    SELECT
        t.container_id,
        t.event_ts,
        t.commodity_id,
        c.name AS commodity_name,
        c.base_cargo_value_usd,
        c.optimal_temp_c,
        c.max_safe_temp_c,
        c.optimal_humidity_pct,
        c.base_shelf_life_hours,
        c.q10_factor,
        c.vibration_sensitivity,
        t.temp_c,
        t.humidity_pct,
        t.vibration_g,
        t.current_lat,
        t.current_lon,
        t.speed_kmh,
        t.compressor_status,
        -- Q10 Thermal + Humidity + Vibration Degradation Multiplier
        ROUND(
            POWER(c.q10_factor, GREATEST(0.0, t.temp_c - c.optimal_temp_c) / 10.0)
            * (1.0 + (GREATEST(0.0, t.humidity_pct - c.optimal_humidity_pct) / 10.0) * 0.42)
            * (1.0 + GREATEST(0.0, t.vibration_g - 0.35) * c.vibration_sensitivity * 0.55),
            2
        ) AS degradation_multiplier
    FROM latest_telemetry t
    INNER JOIN commodity_specs c
        ON t.commodity_id = c.commodity_id
)

SELECT
    container_id,
    commodity_name,
    compressor_status,
    temp_c,
    humidity_pct,
    vibration_g,
    degradation_multiplier,
    ROUND(base_shelf_life_hours / NULLIF(degradation_multiplier, 0), 1) AS dynamic_time_to_spoilage_hrs,
    base_cargo_value_usd
FROM degradation_calc
