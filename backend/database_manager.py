"""
AtmoSync Database & Star-Schema CSV Warehouse Manager
Manages SQLite persistence (`powerbi db/database/atmosync.db`) and exports
Star-Schema CSVs (`powerbi db/datasets/*.csv`).
"""

from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

from config import DB_DIR, DB_PATH, POWERBI_DATASETS_DIR, SCHEMA_SQL_PATH
from models import CommodityProfile, ContainerState, MarketHub

DEFAULT_SCHEMA_SQL = """
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
"""


def init_warehouse_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    POWERBI_DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    ddl = (
        SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        if SCHEMA_SQL_PATH.exists()
        else DEFAULT_SCHEMA_SQL
    )
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(ddl)
        conn.commit()


def persist_tick_records(
    now_iso: str,
    raw_and_stg_batch: List[Tuple[Dict[str, Any], Dict[str, Any], str, str]],
    mart_rows: List[Dict[str, Any]],
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        for kafka_event, calc, commodity_id, compressor_status in raw_and_stg_batch:
            cid = calc["container_id"]
            cur.execute(
                """
                INSERT INTO raw_iot_stream (
                    event_timestamp, container_id, kafka_topic, kafka_partition, raw_payload_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    now_iso,
                    cid,
                    kafka_event["topic"],
                    kafka_event["partition"],
                    json.dumps(kafka_event["payload"]),
                ),
            )
            cur.execute(
                """
                INSERT INTO stg_telemetry (
                    event_timestamp, container_id, commodity_id, temp_c, humidity_pct,
                    vibration_g, co2_ppm, ethylene_ppm, lat, lon, speed_kmh,
                    compressor_status, quality_remaining_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_iso,
                    cid,
                    commodity_id,
                    calc["temp_c"],
                    calc["humidity_pct"],
                    calc["vibration_g"],
                    calc["co2_ppm"],
                    calc["ethylene_ppm"],
                    calc["current_lat"],
                    calc["current_lon"],
                    calc["speed_kmh"],
                    compressor_status,
                    calc["quality_remaining_pct"],
                ),
            )

        cur.execute("DELETE FROM mart_spoilage_arbitrage")
        for row in mart_rows:
            cur.execute(
                """
                INSERT INTO mart_spoilage_arbitrage VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    now_iso,
                    row["container_id"],
                    row["commodity_name"],
                    row["compressor_status"],
                    row["temp_c"],
                    row["humidity_pct"],
                    row["vibration_g"],
                    row["quality_remaining_pct"],
                    row["degradation_multiplier"],
                    row["time_to_spoilage_hrs"],
                    row["primary_market_name"],
                    row["primary_eta_hrs"],
                    row["primary_expected_value_usd"],
                    row["recommended_secondary_market"],
                    row["secondary_eta_hrs"],
                    row["secondary_net_value_usd"],
                    row["spoilage_arbitrage_usd"],
                    row["risk_status"],
                    row["recommended_action"],
                ),
            )
        conn.commit()


def export_star_schema_csvs(
    snapshot: List[Dict[str, Any]],
    containers: Dict[str, ContainerState],
    commodities: Dict[str, CommodityProfile],
    markets: Dict[str, MarketHub],
) -> Dict[str, str]:
    POWERBI_DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    arb_path = POWERBI_DATASETS_DIR / "Fact_Spoilage_Arbitrage.csv"
    arb_fields = [
        "container_id",
        "vessel_or_carrier",
        "commodity_id",
        "commodity_name",
        "category",
        "origin_name",
        "current_lat",
        "current_lon",
        "speed_kmh",
        "temp_c",
        "optimal_temp_c",
        "max_safe_temp_c",
        "humidity_pct",
        "vibration_g",
        "co2_ppm",
        "ethylene_ppm",
        "compressor_status",
        "quality_remaining_pct",
        "degradation_multiplier",
        "burn_rate_pct_per_hr",
        "time_to_spoilage_hrs",
        "base_cargo_value_usd",
        "primary_market_id",
        "primary_market_name",
        "primary_distance_km",
        "primary_eta_hrs",
        "primary_arrival_quality_pct",
        "primary_expected_value_usd",
        "recommended_secondary_id",
        "recommended_secondary_market",
        "secondary_distance_km",
        "secondary_eta_hrs",
        "secondary_arrival_quality_pct",
        "secondary_net_value_usd",
        "spoilage_arbitrage_usd",
        "risk_status",
        "recommended_action",
        "last_updated",
    ]
    with open(arb_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=arb_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(snapshot)

    tel_path = POWERBI_DATASETS_DIR / "Fact_IoT_Telemetry.csv"
    tel_rows = []
    for cid, state in containers.items():
        for pt in state.history:
            tel_rows.append(
                {
                    "container_id": cid,
                    "commodity_id": state.commodity_id,
                    "timestamp": pt["timestamp"],
                    "tick": pt["tick"],
                    "temp_c": pt["temp_c"],
                    "humidity_pct": pt["humidity_pct"],
                    "vibration_g": pt["vibration_g"],
                    "quality_remaining_pct": pt["quality_remaining_pct"],
                    "degradation_multiplier": pt["degradation_multiplier"],
                    "spoilage_arbitrage_usd": pt["spoilage_arbitrage_usd"],
                    "time_to_spoilage_hrs": pt["time_to_spoilage_hrs"],
                }
            )
    if tel_rows:
        with open(tel_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(tel_rows[0].keys()))
            writer.writeheader()
            writer.writerows(tel_rows)

    com_path = POWERBI_DATASETS_DIR / "Dim_Commodities.csv"
    with open(com_path, "w", newline="", encoding="utf-8") as f:
        com_rows = [asdict(c) for c in commodities.values()]
        writer = csv.DictWriter(f, fieldnames=list(com_rows[0].keys()))
        writer.writeheader()
        writer.writerows(com_rows)

    mkt_path = POWERBI_DATASETS_DIR / "Dim_Markets.csv"
    with open(mkt_path, "w", newline="", encoding="utf-8") as f:
        mkt_rows = [asdict(m) for m in markets.values()]
        writer = csv.DictWriter(f, fieldnames=list(mkt_rows[0].keys()))
        writer.writeheader()
        writer.writerows(mkt_rows)

    return {
        "Fact_Spoilage_Arbitrage": str(arb_path),
        "Fact_IoT_Telemetry": str(tel_path),
        "Dim_Commodities": str(com_path),
        "Dim_Markets": str(mkt_path),
        "SQLite_Database": str(DB_PATH),
    }
