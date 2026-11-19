
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
