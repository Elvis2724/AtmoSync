"""
AtmoSync Domain Models & Reference Data Loaders
Loads seed data from `../data/*.json`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import (
    COMMODITIES_JSON_PATH,
    FLEET_CONTAINERS_JSON_PATH,
    MARKETS_JSON_PATH,
)


@dataclass
class CommodityProfile:
    commodity_id: str
    name: str
    category: str
    optimal_temp_c: float
    max_safe_temp_c: float
    optimal_humidity_pct: float
    max_safe_humidity_pct: float
    vibration_sensitivity: float
    base_shelf_life_hours: float
    q10_factor: float
    base_cargo_value_usd: float
    unit_weight_tons: float


@dataclass
class MarketHub:
    market_id: str
    name: str
    country: str
    lat: float
    lon: float
    price_multiplier: float
    reroute_fee_usd: float
    port_handling_hours: float


@dataclass
class ContainerState:
    container_id: str
    vessel_or_carrier: str
    commodity_id: str
    origin_name: str
    origin_lat: float
    origin_lon: float
    primary_market_id: str
    candidate_secondary_markets: List[str]
    current_lat: float
    current_lon: float
    speed_kmh: float
    temp_c: float
    humidity_pct: float
    vibration_g: float
    co2_ppm: float
    ethylene_ppm: float
    compressor_status: str
    cumulative_quality_loss_pct: float
    anomaly_mode: Optional[str] = None
    rerouted_to_market_id: Optional[str] = None
    last_updated: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)


def load_commodities() -> Dict[str, CommodityProfile]:
    raw = json.loads(COMMODITIES_JSON_PATH.read_text(encoding="utf-8"))
    return {item["commodity_id"]: CommodityProfile(**item) for item in raw}


def load_markets() -> Dict[str, MarketHub]:
    raw = json.loads(MARKETS_JSON_PATH.read_text(encoding="utf-8"))
    return {item["market_id"]: MarketHub(**item) for item in raw}


def load_initial_containers() -> Dict[str, ContainerState]:
    raw = json.loads(FLEET_CONTAINERS_JSON_PATH.read_text(encoding="utf-8"))
    now_iso = datetime.now(timezone.utc).isoformat()
    containers: Dict[str, ContainerState] = {}
    for spec in raw:
        cid = spec["container_id"]
        containers[cid] = ContainerState(last_updated=now_iso, **spec)
    return containers
