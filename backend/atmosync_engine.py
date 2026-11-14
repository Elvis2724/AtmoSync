"""
AtmoSync: Micro-Climate Arbitrage Analytics Engine (Backend Orchestrator)
-------------------------------------------------------------------------
Coordinates:
- Reference data loaded from `../data/*.json` via `models.py`
- Quantitative Spoilage & Arbitrage calculation via `arbitrage_calculator.py`
- SQLite ELT persistence & Star-Schema CSV exports via `database_manager.py`
"""

from __future__ import annotations

import random
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from arbitrage_calculator import evaluate_container_arbitrage
from database_manager import (
    export_star_schema_csvs,
    init_warehouse_db,
    persist_tick_records,
)
from models import (
    CommodityProfile,
    ContainerState,
    MarketHub,
    load_commodities,
    load_initial_containers,
    load_markets,
)

COMMODITIES: Dict[str, CommodityProfile] = load_commodities()
MARKETS: Dict[str, MarketHub] = load_markets()


class AtmoSyncEngine:
    """End-to-end simulator, ELT processor, and Spoilage Arbitrage orchestrator."""

    def __init__(self) -> None:
        self.commodities: Dict[str, CommodityProfile] = load_commodities()
        self.markets: Dict[str, MarketHub] = load_markets()
        self.containers: Dict[str, ContainerState] = load_initial_containers()
        self.alerts: List[Dict[str, Any]] = []
        self.kafka_stream_log: List[Dict[str, Any]] = []
        self.total_events_ingested: int = 0
        self.tick_count: int = 0
        init_warehouse_db()
        for _ in range(35):
            self.step_simulation(persist_to_db=True)

    def calculate_degradation_and_arbitrage(
        self, state: ContainerState
    ) -> Dict[str, Any]:
        return evaluate_container_arbitrage(state, self.commodities, self.markets)

    def step_simulation(self, persist_to_db: bool = True) -> List[Dict[str, Any]]:
        self.tick_count += 1
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        mart_rows: List[Dict[str, Any]] = []
        raw_and_stg_batch: List[Tuple[Dict[str, Any], Dict[str, Any], str, str]] = []

        for cid, state in self.containers.items():
            profile = self.commodities[state.commodity_id]
            target_mkt_id = state.rerouted_to_market_id or state.primary_market_id
            target_mkt = self.markets[target_mkt_id]

            dlat = target_mkt.lat - state.current_lat
            dlon = target_mkt.lon - state.current_lon
            step_scale = 0.008
            state.current_lat += dlat * step_scale + random.uniform(-0.015, 0.015)
            state.current_lon += dlon * step_scale + random.uniform(-0.015, 0.015)

            if state.anomaly_mode == "HUMIDITY_TEMP_SPIKE":
                state.temp_c = min(
                    profile.max_safe_temp_c + 4.2,
                    max(
                        profile.optimal_temp_c + 2.5,
                        state.temp_c + random.uniform(-0.08, 0.16),
                    ),
                )
                state.humidity_pct = min(
                    98.5, max(92.0, state.humidity_pct + random.uniform(-0.2, 0.35))
                )
                state.vibration_g = min(
                    1.5, max(0.55, state.vibration_g + random.uniform(-0.06, 0.08))
                )
            elif state.anomaly_mode == "THERMAL_DRIFT":
                state.temp_c = min(
                    profile.max_safe_temp_c + 3.8,
                    max(
                        profile.optimal_temp_c + 2.0,
                        state.temp_c + random.uniform(-0.06, 0.15),
                    ),
                )
                state.humidity_pct = min(
                    96.0, max(50.0, state.humidity_pct + random.uniform(-0.25, 0.3))
                )
                state.vibration_g = min(
                    1.3, max(0.4, state.vibration_g + random.uniform(-0.05, 0.06))
                )
            elif state.anomaly_mode == "VIBRATION_SURGE":
                state.temp_c = min(
                    profile.max_safe_temp_c + 2.5,
                    max(
                        profile.optimal_temp_c + 1.2,
                        state.temp_c + random.uniform(-0.07, 0.12),
                    ),
                )
                state.vibration_g = min(
                    1.85, max(1.15, state.vibration_g + random.uniform(-0.08, 0.12))
                )
            else:
                temp_pull = (profile.optimal_temp_c - state.temp_c) * 0.25
                state.temp_c += temp_pull + random.uniform(-0.09, 0.09)
                hum_pull = (profile.optimal_humidity_pct - state.humidity_pct) * 0.2
                state.humidity_pct += hum_pull + random.uniform(-0.2, 0.2)
                state.vibration_g = max(
                    0.18, min(0.55, state.vibration_g + random.uniform(-0.04, 0.04))
                )

            state.last_updated = now_iso
            calc = self.calculate_degradation_and_arbitrage(state)

            state.cumulative_quality_loss_pct = min(
                52.0,
                state.cumulative_quality_loss_pct + (calc["burn_rate_pct_per_hr"] * 0.12),
            )

            point = {
                "timestamp": now_iso,
                "tick": self.tick_count,
                "temp_c": calc["temp_c"],
                "humidity_pct": calc["humidity_pct"],
                "vibration_g": calc["vibration_g"],
                "quality_remaining_pct": calc["quality_remaining_pct"],
                "degradation_multiplier": calc["degradation_multiplier"],
                "spoilage_arbitrage_usd": calc["spoilage_arbitrage_usd"],
                "time_to_spoilage_hrs": calc["time_to_spoilage_hrs"],
            }
            state.history.append(point)
            if len(state.history) > 40:
                state.history.pop(0)

            kafka_event = {
                "topic": "iot.reefer.telemetry.v1",
                "partition": hash(cid) % 4,
                "offset": 100000 + self.total_events_ingested + 1,
                "timestamp": now_iso,
                "payload": {
                    "container_id": cid,
                    "commodity_id": state.commodity_id,
                    "sensors": {
                        "internal_temp_c": calc["temp_c"],
                        "humidity_pct": calc["humidity_pct"],
                        "vibration_g": calc["vibration_g"],
                        "co2_ppm": calc["co2_ppm"],
                        "ethylene_ppm": calc["ethylene_ppm"],
                    },
                    "gps": {
                        "lat": calc["current_lat"],
                        "lon": calc["current_lon"],
                        "speed_kmh": calc["speed_kmh"],
                    },
                    "reefer_unit": {"compressor_status": state.compressor_status},
                },
            }
            self.total_events_ingested += 1
            self.kafka_stream_log.insert(0, kafka_event)
            if len(self.kafka_stream_log) > 25:
                self.kafka_stream_log.pop()

            if calc["spoilage_arbitrage_usd"] >= 20000.0:
                existing_ids = {a["container_id"] for a in self.alerts[:6]}
                if cid not in existing_ids:
                    self.alerts.insert(
                        0,
                        {
                            "alert_id": f"ALT-{1000 + len(self.alerts) + 1}",
                            "timestamp": now_iso,
                            "severity": (
                                "CRITICAL"
                                if calc["spoilage_arbitrage_usd"] >= 45000
                                else "HIGH"
                            ),
                            "channel": "#trading-arbitrage-alerts",
                            "container_id": cid,
                            "commodity": calc["commodity_name"],
                            "message": (
                                f"Micro-climate drift on {cid} ({calc['temp_c']}°C, {calc['degradation_multiplier']}x burn). "
                                f"Reroute from {calc['primary_market_name']} to {calc['recommended_secondary_market']} "
                                f"for +${calc['spoilage_arbitrage_usd']:,.0f} Spoilage Arbitrage."
                            ),
                            "arbitrage_usd": calc["spoilage_arbitrage_usd"],
                        },
                    )
                    if len(self.alerts) > 20:
                        self.alerts.pop()

            raw_and_stg_batch.append(
                (kafka_event, calc, state.commodity_id, state.compressor_status)
            )
            mart_rows.append(calc)

        if persist_to_db:
            persist_tick_records(now_iso, raw_and_stg_batch, mart_rows)

        return mart_rows

    def inject_anomaly(
        self, container_id: str, anomaly_type: str = "HUMIDITY_TEMP_SPIKE"
    ) -> Dict[str, Any]:
        if container_id not in self.containers:
            raise KeyError(f"Unknown container {container_id}")
        state = self.containers[container_id]
        profile = self.commodities[state.commodity_id]
        state.rerouted_to_market_id = None
        state.anomaly_mode = anomaly_type
        state.compressor_status = "CYCLE_FAULT"
        state.temp_c = profile.max_safe_temp_c + 2.8
        state.humidity_pct = min(98.0, profile.max_safe_humidity_pct + 3.5)
        state.vibration_g = 1.25
        state.cumulative_quality_loss_pct = max(18.0, state.cumulative_quality_loss_pct)
        calc = self.calculate_degradation_and_arbitrage(state)
        self.alerts.insert(
            0,
            {
                "alert_id": f"ALT-{1000 + len(self.alerts) + 1}",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "severity": "CRITICAL",
                "channel": "#trading-arbitrage-alerts",
                "container_id": container_id,
                "commodity": calc["commodity_name"],
                "message": (
                    f"[SIMULATED ANOMALY] {anomaly_type} injected on {container_id}. "
                    f"Arbitrage margin jumped to +${calc['spoilage_arbitrage_usd']:,.0f} via {calc['recommended_secondary_market']}."
                ),
                "arbitrage_usd": calc["spoilage_arbitrage_usd"],
            },
        )
        return calc

    def execute_reroute(
        self, container_id: str, target_market_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if container_id not in self.containers:
            raise KeyError(f"Unknown container {container_id}")
        state = self.containers[container_id]
        calc_before = self.calculate_degradation_and_arbitrage(state)
        chosen_mkt = target_market_id or calc_before["recommended_secondary_id"]
        if chosen_mkt and chosen_mkt in self.markets:
            state.rerouted_to_market_id = chosen_mkt
            state.compressor_status = "DEGRADED"
        calc_after = self.calculate_degradation_and_arbitrage(state)
        self.alerts.insert(
            0,
            {
                "alert_id": f"ALT-{1000 + len(self.alerts) + 1}",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "severity": "EXECUTION",
                "channel": "#dispatch-routing-desk",
                "container_id": container_id,
                "commodity": calc_after["commodity_name"],
                "message": (
                    f"ORDER EXECUTED: {container_id} rerouted to {self.markets[chosen_mkt].name}. "
                    f"Captured +${calc_before['spoilage_arbitrage_usd']:,.0f} Spoilage Arbitrage value."
                ),
                "arbitrage_usd": calc_before["spoilage_arbitrage_usd"],
            },
        )
        return calc_after

    def export_powerbi_datasets(self) -> Dict[str, str]:
        snapshot = [
            self.calculate_degradation_and_arbitrage(c)
            for c in self.containers.values()
        ]
        return export_star_schema_csvs(
            snapshot, self.containers, self.commodities, self.markets
        )

    def get_dashboard_payload(self) -> Dict[str, Any]:
        containers_eval = [
            self.calculate_degradation_and_arbitrage(c)
            for c in self.containers.values()
        ]
        containers_eval.sort(key=lambda x: x["spoilage_arbitrage_usd"], reverse=True)

        total_cargo_val = sum(c["base_cargo_value_usd"] for c in containers_eval)
        total_arbitrage_usd = sum(c["spoilage_arbitrage_usd"] for c in containers_eval)
        at_risk_count = sum(
            1
            for c in containers_eval
            if c["risk_status"] in ("CRITICAL ARBITRAGE", "ELEVATED DRIFT")
        )
        critical_count = sum(
            1 for c in containers_eval if c["risk_status"] == "CRITICAL ARBITRAGE"
        )
        avg_degradation = round(
            sum(c["degradation_multiplier"] for c in containers_eval)
            / max(1, len(containers_eval)),
            2,
        )

        histories = {cid: st.history for cid, st in self.containers.items()}
        markets_list = [asdict(m) for m in self.markets.values()]

        return {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "kpis": {
                "active_containers": len(containers_eval),
                "at_risk_containers": at_risk_count,
                "critical_containers": critical_count,
                "total_fleet_cargo_usd": round(total_cargo_val, 2),
                "total_arbitrage_opportunity_usd": round(total_arbitrage_usd, 2),
                "avg_degradation_multiplier": avg_degradation,
                "total_events_ingested": self.total_events_ingested,
                "pipeline_latency_ms": random.randint(18, 42),
            },
            "containers": containers_eval,
            "histories": histories,
            "markets": markets_list,
            "alerts": self.alerts[:12],
            "kafka_stream": self.kafka_stream_log[:12],
        }


if __name__ == "__main__":
    engine = AtmoSyncEngine()
    paths = engine.export_powerbi_datasets()
    print("AtmoSync Backend Engine initialized and Power BI DB datasets exported:")
    for name, p in paths.items():
        print(f"  - {name}: {p}")
