"""
AtmoSync: Power BI Real-Time Streaming Dataset Pusher & Local CSV Sync
----------------------------------------------------------------------
Supports two modes:
1. Local Star-Schema Auto-Refresh (Default): Continuously steps the AtmoSync IoT & Arbitrage engine
   and updates `powerbi db/datasets/*.csv` + `powerbi db/database/atmosync.db` for Power BI Desktop.
2. Power BI Service Push Dataset REST API: Set `POWERBI_PUSH_URL` environment variable to push
   real-time JSON rows directly to a Power BI Streaming Dataset tile.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
from atmosync_engine import AtmoSyncEngine


def push_to_powerbi_service(push_url: str, rows: list[dict]) -> int:
    payload = json.dumps(rows).encode("utf-8")
    req = urllib.request.Request(
        push_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status


def main() -> None:
    push_url = os.environ.get("POWERBI_PUSH_URL", "").strip()
    engine = AtmoSyncEngine()
    paths = engine.export_powerbi_datasets()
    print("Initial Power BI Star-Schema datasets generated:")
    for k, v in paths.items():
        print(f"  [OK] {k}: {v}")

    if push_url:
        print(f"\nStreaming live rows to Power BI Push Dataset endpoint: {push_url[:48]}...")
        while True:
            mart_rows = engine.step_simulation(persist_to_db=True)
            engine.export_powerbi_datasets()
            status = push_to_powerbi_service(push_url, mart_rows)
            print(f"Pushed {len(mart_rows)} container arbitrage records -> HTTP {status}")
            time.sleep(3.0)
    else:
        print(
            "\nTip: Set POWERBI_PUSH_URL to push directly to Power BI Cloud Service, "
            "or connect Power BI Desktop to the CSVs above."
        )


if __name__ == "__main__":
    main()
