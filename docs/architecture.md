# AtmoSync System Architecture

## 1. Data Ingestion & Simulation Layer (`data/` & `backend/atmosync_engine.py`)
- Loads reference commodity profiles (`data/commodities.json`), global market ports (`data/markets.json`), and active reefer container fleet telemetry (`data/fleet_containers.json`).
- Emits synthetic Apache Kafka telemetry events on topic `iot.reefer.telemetry.v1` every 3 seconds with internal temperature (°C), relative humidity (%), vibration shock (G), $\text{CO}_2$ (ppm), ethylene ($\text{C}_2\text{H}_4$ ppm), and vessel GPS coordinates.

## 2. ELT Warehouse & dbt Transformation Layer (`powerbi db/database/` & `dbt/`)
- **Raw Landing (`raw_iot_stream`)**: Stores incoming Kafka JSON events with partition and offset metadata.
- **Staging (`stg_telemetry` / `dbt/models/stg_iot_telemetry.sql`)**: Parses JSON sensor attributes, casts types, and filters out corrupted sensor spikes.
- **Analytical Mart (`mart_spoilage_arbitrage` / `dbt/models/mart_spoilage_arbitrage.sql`)**: Joins live telemetry with commodity $Q_{10}$ kinetic parameters and port distances to compute real-time spoilage arbitrage margins.

## 3. Quantitative Arbitrage Calculator (`backend/arbitrage_calculator.py`)
- Computes thermal, humidity, and vibration degradation multipliers.
- Evaluates arrival cargo quality at the **Primary Destination Port** vs. **Candidate Secondary Ports** (accounting for spot price multipliers and port diversion fees).
- Triggers automated alerts to `#trading-arbitrage-alerts` when net reroute alpha exceeds \$20,000.

## 4. Presentation & BI Layer (`frontend/` & `powerbi db/`)
- **Web Trading Terminal (`frontend/`)**: Interactive SVG global route map, HTML5 Canvas degradation curves, and one-click reroute execution matrix.
- **Power BI Star-Schema (`powerbi db/`)**: Auto-updated CSV fact/dimension tables, DAX measures library, Power Query M loader, and custom dark theme.
