"""
AtmoSync Quantitative Spoilage & Arbitrage Calculator
Computes Great-Circle distances, Q10/Arrhenius micro-climate degradation velocity,
and Primary vs. Secondary Market Net Value realization.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from models import CommodityProfile, ContainerState, MarketHub


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def compute_quality_realization(arrival_quality_pct: float) -> float:
    """Piecewise commercial realization curve based on arrival cargo quality."""
    if arrival_quality_pct >= 80.0:
        return 1.0
    if arrival_quality_pct >= 65.0:
        return 0.55 + 0.45 * ((arrival_quality_pct - 65.0) / 15.0)
    if arrival_quality_pct >= 55.0:
        return 0.22 + 0.33 * ((arrival_quality_pct - 55.0) / 10.0)
    return 0.08


def evaluate_container_arbitrage(
    state: ContainerState,
    commodities: Dict[str, CommodityProfile],
    markets: Dict[str, MarketHub],
) -> Dict[str, Any]:
    """Evaluate degradation velocity, ETAs, and spoilage arbitrage for a single container."""
    profile = commodities[state.commodity_id]
    active_primary_id = state.rerouted_to_market_id or state.primary_market_id
    primary_mkt = markets[active_primary_id]

    temp_delta = max(0.0, state.temp_c - profile.optimal_temp_c)
    thermal_factor = math.pow(profile.q10_factor, temp_delta / 10.0)

    humidity_excess = max(0.0, state.humidity_pct - profile.optimal_humidity_pct)
    humidity_factor = 1.0 + (humidity_excess / 10.0) * 0.42

    vibration_excess = max(0.0, state.vibration_g - 0.35)
    vibration_factor = 1.0 + vibration_excess * profile.vibration_sensitivity * 0.55

    degradation_multiplier = round(
        thermal_factor * humidity_factor * vibration_factor, 2
    )

    quality_remaining_pct = max(
        5.0, round(100.0 - state.cumulative_quality_loss_pct, 1)
    )
    usable_quality_buffer_pct = max(0.5, quality_remaining_pct - 55.0)
    nominal_burn_pct_per_hr = 45.0 / profile.base_shelf_life_hours
    actual_burn_pct_per_hr = nominal_burn_pct_per_hr * degradation_multiplier
    time_to_spoilage_hrs = round(
        usable_quality_buffer_pct / max(0.001, actual_burn_pct_per_hr), 1
    )

    dist_primary_km = haversine_km(
        state.current_lat, state.current_lon, primary_mkt.lat, primary_mkt.lon
    )
    primary_eta_hrs = round(
        (dist_primary_km / max(20.0, state.speed_kmh))
        + primary_mkt.port_handling_hours,
        1,
    )
    quality_at_primary = max(
        0.0, quality_remaining_pct - (primary_eta_hrs * actual_burn_pct_per_hr)
    )

    primary_quality_realization = compute_quality_realization(quality_at_primary)
    primary_expected_value_usd = round(
        profile.base_cargo_value_usd
        * primary_mkt.price_multiplier
        * primary_quality_realization,
        2,
    )

    best_secondary_mkt: Optional[MarketHub] = None
    best_secondary_eta_hrs = primary_eta_hrs
    best_secondary_dist_km = dist_primary_km
    best_secondary_net_value_usd = primary_expected_value_usd
    best_secondary_quality = quality_at_primary
    secondary_options_breakdown = []

    for sec_id in state.candidate_secondary_markets:
        sec_mkt = markets[sec_id]
        dist_sec_km = haversine_km(
            state.current_lat, state.current_lon, sec_mkt.lat, sec_mkt.lon
        )
        sec_eta_hrs = round(
            (dist_sec_km / max(20.0, state.speed_kmh)) + sec_mkt.port_handling_hours, 1
        )
        quality_at_sec = max(
            0.0, quality_remaining_pct - (sec_eta_hrs * actual_burn_pct_per_hr)
        )

        sec_realization = compute_quality_realization(quality_at_sec)
        gross_sec_val = (
            profile.base_cargo_value_usd * sec_mkt.price_multiplier * sec_realization
        )
        net_sec_val = round(gross_sec_val - sec_mkt.reroute_fee_usd, 2)

        secondary_options_breakdown.append(
            {
                "market_id": sec_mkt.market_id,
                "market_name": f"{sec_mkt.name} ({sec_mkt.country})",
                "distance_km": round(dist_sec_km, 0),
                "eta_hrs": sec_eta_hrs,
                "arrival_quality_pct": round(quality_at_sec, 1),
                "spot_multiplier": sec_mkt.price_multiplier,
                "reroute_fee_usd": sec_mkt.reroute_fee_usd,
                "net_value_usd": net_sec_val,
            }
        )

        if best_secondary_mkt is None or net_sec_val > best_secondary_net_value_usd:
            best_secondary_mkt = sec_mkt
            best_secondary_eta_hrs = sec_eta_hrs
            best_secondary_dist_km = round(dist_sec_km, 0)
            best_secondary_net_value_usd = net_sec_val
            best_secondary_quality = round(quality_at_sec, 1)

    if state.rerouted_to_market_id:
        spoilage_arbitrage_usd = 0.0
        risk_status = "REROUTED (LOCKED)"
        recommended_action = f"LOCKED -> {primary_mkt.name}"
    else:
        spoilage_arbitrage_usd = round(
            max(0.0, best_secondary_net_value_usd - primary_expected_value_usd), 2
        )
        if (
            spoilage_arbitrage_usd >= 25000.0
            or time_to_spoilage_hrs < primary_eta_hrs * 1.15
        ):
            risk_status = "CRITICAL ARBITRAGE"
            recommended_action = (
                f"REROUTE -> {best_secondary_mkt.name}"
                if best_secondary_mkt
                else "INSPECT REEFER"
            )
        elif degradation_multiplier >= 1.65 or spoilage_arbitrage_usd >= 8000.0:
            risk_status = "ELEVATED DRIFT"
            recommended_action = "WATCH / PRE-BOOK PORT"
        else:
            risk_status = "OPTIMAL"
            recommended_action = "HOLD PRIMARY ROUTE"

    return {
        "container_id": state.container_id,
        "vessel_or_carrier": state.vessel_or_carrier,
        "commodity_id": state.commodity_id,
        "commodity_name": profile.name,
        "category": profile.category,
        "origin_name": state.origin_name,
        "current_lat": round(state.current_lat, 4),
        "current_lon": round(state.current_lon, 4),
        "speed_kmh": round(state.speed_kmh, 1),
        "temp_c": round(state.temp_c, 2),
        "optimal_temp_c": profile.optimal_temp_c,
        "max_safe_temp_c": profile.max_safe_temp_c,
        "humidity_pct": round(state.humidity_pct, 1),
        "optimal_humidity_pct": profile.optimal_humidity_pct,
        "vibration_g": round(state.vibration_g, 2),
        "co2_ppm": round(state.co2_ppm, 0),
        "ethylene_ppm": round(state.ethylene_ppm, 2),
        "compressor_status": state.compressor_status,
        "quality_remaining_pct": quality_remaining_pct,
        "degradation_multiplier": degradation_multiplier,
        "burn_rate_pct_per_hr": round(actual_burn_pct_per_hr, 3),
        "time_to_spoilage_hrs": time_to_spoilage_hrs,
        "base_cargo_value_usd": profile.base_cargo_value_usd,
        "primary_market_id": primary_mkt.market_id,
        "primary_market_name": f"{primary_mkt.name} ({primary_mkt.country})",
        "primary_distance_km": round(dist_primary_km, 0),
        "primary_eta_hrs": primary_eta_hrs,
        "primary_arrival_quality_pct": round(quality_at_primary, 1),
        "primary_expected_value_usd": primary_expected_value_usd,
        "recommended_secondary_id": (
            best_secondary_mkt.market_id if best_secondary_mkt else ""
        ),
        "recommended_secondary_market": (
            f"{best_secondary_mkt.name} ({best_secondary_mkt.country})"
            if best_secondary_mkt
            else "N/A"
        ),
        "secondary_distance_km": best_secondary_dist_km,
        "secondary_eta_hrs": best_secondary_eta_hrs,
        "secondary_arrival_quality_pct": best_secondary_quality,
        "secondary_net_value_usd": best_secondary_net_value_usd,
        "spoilage_arbitrage_usd": spoilage_arbitrage_usd,
        "risk_status": risk_status,
        "recommended_action": recommended_action,
        "rerouted_to_market_id": state.rerouted_to_market_id,
        "secondary_options": secondary_options_breakdown,
        "last_updated": state.last_updated,
    }
