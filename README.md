# AtmoSync: Micro-Climate Arbitrage Analytics & Cold-Chain BI

AtmoSync is an end-to-end real-time cold-chain telemetry, ELT data warehouse, and quantitative **Spoilage Arbitrage** platform. It monitors perishable maritime reefer containers, models biological shelf-life degradation using Q10 / Arrhenius kinetics, and recommends profitable secondary port reroutes before cargo spoils.

---

## Project Directory Structure

Files are organized so that `frontend/`, `backend/`, and `powerbi db/` only contain the files that strictly belong to them, while shared datasets, dbt SQL models, documentation, and roadmap files live in dedicated root folders and files:

```text
atmosync777/
├── README.md                                   # Project overview & quick-start guide
├── roadmap.txt                                 # Phased implementation roadmap & milestones
├── requirements.txt                            # Python runtime & optional analytics dependencies
├── start_server.bat                            # One-click Windows launcher for the platform
│
├── data/                                       # Shared Reference & Seed Datasets
│   ├── commodities.json                        # Perishable commodity Q10 profiles & cargo values
│   ├── markets.json                            # Global port hubs, spot multipliers & reroute fees
│   ├── fleet_containers.json                   # Initial reefer container fleet telemetry specs
│   └── sample_kafka_stream.json                # Sample raw Kafka IoT telemetry payloads
│
├── docs/                                       # Architecture, API & Mathematical Specifications
│   ├── architecture.md                         # End-to-end system architecture & data flow
│   ├── api_reference.md                        # Backend REST API endpoint documentation
│   └── spoilage_arbitrage_formula.txt          # Q10 degradation & arbitrage pricing formulas
│
├── dbt/                                        # dbt SQL Warehouse Transformation Project
│   ├── dbt_project.yml                         # dbt project configuration
│   └── models/
│       ├── schema.yml                          # Table & column data quality tests
│       ├── stg_iot_telemetry.sql               # Staging model: cleans raw Kafka JSON stream
│       └── mart_spoilage_arbitrage.sql         # Mart model: calculates degradation & arbitrage
│
├── backend/                                    # Modular Python Backend Server & Simulation Engine
│   ├── app.py                                  # HTTP & REST API Server (port 8050)
│   ├── config.py                               # Workspace paths & simulation constants
│   ├── models.py                               # Dataclasses (CommodityProfile, MarketHub, ContainerState)
│   ├── arbitrage_calculator.py                 # Haversine distance, Q10 burn & arbitrage math
│   ├── database_manager.py                     # SQLite warehouse persistence & CSV Star-Schema exporter
│   └── atmosync_engine.py                      # Core IoT telemetry simulator & alert orchestrator
│
├── frontend/                                   # Modular Executive BI & Trading Desk Web Client
│   ├── index.html                              # Dashboard layout & KPI terminal
│   ├── styles.css                              # Institutional dark-mode UI styles
│   ├── mock_data.js                            # Standalone offline fallback dataset
│   ├── charts.js                               # SVG global maritime route map & Canvas curves
│   └── dashboard.js                            # Live polling, anomaly injection & reroute controller
│
└── powerbi db/                                 # Power BI Star-Schema Assets & SQLite Warehouse
    ├── database/
    │   ├── atmosync.db                         # Live SQLite analytical database
    │   └── schema.sql                          # Relational warehouse DDL schema
    ├── datasets/
    │   ├── Fact_Spoilage_Arbitrage.csv         # Star-Schema Fact: Live arbitrage & rerouting
    │   ├── Fact_IoT_Telemetry.csv              # Star-Schema Fact: Sensor time-series
    │   ├── Dim_Commodities.csv                 # Star-Schema Dimension: Commodity Q10 specs
    │   └── Dim_Markets.csv                     # Star-Schema Dimension: Global ports & pricing
    ├── dax/
    │   └── AtmoSync_DAX_Measures.dax           # Power BI DAX Measures library
    ├── powerquery/
    │   └── PowerQuery_M_Loader.pq              # Power Query (M) typed table loader script
    ├── theme/
    │   └── AtmoSync_Theme.json                 # Power BI custom dark-mode theme JSON
    └── scripts/
        └── powerbi_streaming_push.py           # Real-time Power BI Push Dataset REST API streamer
```

---

## Quick Start

1. **Launch the Backend Server & Live Dashboard**:
   ```powershell
   python backend/app.py
   ```
   Or double-click `start_server.bat`. Then open **http://127.0.0.1:8050** in your browser.

2. **Connect Power BI Desktop**:
   - Load the 4 Star-Schema CSV tables from `powerbi db/datasets/` (or use `powerbi db/powerquery/PowerQuery_M_Loader.pq`).
   - Import the custom theme from `powerbi db/theme/AtmoSync_Theme.json`.
   - Paste the measures from `powerbi db/dax/AtmoSync_DAX_Measures.dax`.
  

<p align="center">
  <img src="assets/atmosync-logo.png" alt="AtmoSync Logo" width="180" height="180">
</p>
