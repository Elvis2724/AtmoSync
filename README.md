<div align="center">

# AtmoSync

### A Micro-Climate Arbitrage Analytics & Cold-Chain BI

_Detecting the drift before the decay_

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Ready-orange.svg)](https://powerbi.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Overview

AtmoSync is an advanced supply chain analytics and micro-climate engineering pipeline designed to monitor real-time, hyper-local sensor telemetry (temperature, humidity, vibration, GPS coordinates) inside shipping containers. By continuously computing "Spoilage Arbitrage", the system detects environmental drift, dynamically adjusts commodity shelf-life predictions, and recommends immediate rerouting to alternative secondary markets before cargo degrades, eliminating total inventory write-offs.

## Features

### IoT Telemetry Simulation

- High-Frequency Stream Generation: Emits time-series data at configurable intervals (e.g., every 15 minutes) across multiple concurrent active shipping containers.   - Multi-Parameter Tracking: Monitors vital transit telemetry fields simultaneously, including internal container temperature, relative humidity, mechanical vibration,    and live GPS coordinates (latitude/longitude).
- Controlled Anomaly Injection: Programmatically introduces micro-climate drift and environmental stress scenarios (such as sudden cooling failures in specific           container units like CONT-A101) to test system resilience.   

### Dynamic Spoilage Modeling

- Commodity-Specific Thresholds: Maintains relational master rules mapping sensitive goods (such as avocados, strawberries, and pharmaceutical vaccines) to their exact   ideal temperature and humidity bounds.   
- Real-Time Shelf-Life Degradation: Instantly triggers mathematical decay models that scale down remaining base shelf-life days proportional to the degree and duration   of temperature excursions.   
- Automated Risk Classification: Instantly flags containers in the database as either Optimal or At-Risk (Spoilage Accelerating) based on continuous metric evaluation.   

### Spoilage Arbitrage Engine

- Market-to-Market Comparison: Compares primary destination market pricing and transport distances against alternate secondary or regional trading hubs.
- Financial Margin Recovery: Computes potential revenue preservation by evaluating the trade-off between writing off degraded cargo versus capturing slightly lower       secondary market prices closer to the current route.
- Intelligent Rerouting Logic: Generates automated actionable recommendations indicating precisely which alternate market hub minimizes total financial loss.   

### Interactive Frontend Command Consol

- Operations Control Center UI: Built using a responsive, modern dark-mode interface optimized for logistics command centers and trading desks.
- Live Fleet Risk Metrics: Features dynamic top-level summary cards tracking active container counts, compromised units, and total estimated financial arbitrage          recovery.
- One-Click Action Triggers: Provides interactive control buttons allowing operators to instantly acknowledge alerts and dispatch simulated shipment reroute              instructions. 

### Executive Power BI Integration

- Pre-Modeled Relational Exports: Automatically bundles cleaned telemetry views and master lookup tables into structured CSV exports (atmosync_powerbi_ready.csv).
- Geospatial & Trend Analytics: Optimized for immediate ingestion into Power BI to plot real-time container routes on maps and track temperature fluctuations against     critical thresholds.
- Executive Decision Support: Empowers logistics management teams with visual insights that drive immediate financial and operational decisions. 


## Technology stack

| Layer | Technologies |
| --- | --- |
| Backend & Storage | Python 3.10+, SQLite, SQL |
| Data Processing & Analytics | Pandas, NumPy, Relational Joins & Case-Based Aggregations |
| Frontend & Dashboard UI | HTML5, CSS3 |
| Visualization & BI | Power BI Desktop |


## Project Structure

Files are organized so that `frontend/`, `backend/`, and `powerbi db/` only contain the files that strictly belong to them, while shared datasets, dbt SQL models, documentation, and roadmap files live in dedicated root folders and files:

```text
atmosync/
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
## Team

| Name | Role |
| --- | --- |
| [**Elvis T. Fernandes**](https://github.com/Elvis2724) | Originator, project lead, system architecture, AI pipeline, and research |
| [**ABC**]() | Frontend and backend development & research |
| [**DEF**]() | Frontend and backend development & research |
| [**GHI**]() | Frontend and backend development & research |

---

<div align="center">
  
_Tracking the pulse inside the container to turn potential spoilage into peak profit._

</div>
