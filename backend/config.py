"""
AtmoSync Backend Configuration & Path Resolution
"""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_SEED_DIR = PROJECT_ROOT / "data"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
POWERBI_DB_ROOT = PROJECT_ROOT / "powerbi db"

DB_DIR = POWERBI_DB_ROOT / "database"
DB_PATH = DB_DIR / "atmosync.db"
SCHEMA_SQL_PATH = DB_DIR / "schema.sql"
POWERBI_DATASETS_DIR = POWERBI_DB_ROOT / "datasets"

COMMODITIES_JSON_PATH = DATA_SEED_DIR / "commodities.json"
MARKETS_JSON_PATH = DATA_SEED_DIR / "markets.json"
FLEET_CONTAINERS_JSON_PATH = DATA_SEED_DIR / "fleet_containers.json"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8050
STREAM_INTERVAL_SECONDS = 3.0
