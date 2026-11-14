# AtmoSync REST API Reference

Base URL: `http://127.0.0.1:8050`

---

## `GET /api/state`
Returns the complete real-time fleet snapshot, executive KPIs, container telemetry histories, market coordinates, alerts, and recent Kafka stream events.

---

## `POST /api/step`
Advances the IoT telemetry simulator by 1 tick, persists records to `powerbi db/database/atmosync.db`, refreshes the Star-Schema CSVs in `powerbi db/datasets/`, and returns the updated dashboard payload.

---

## `POST /api/toggle-stream`
Pauses or resumes the background 3-second IoT telemetry streaming thread.

---

## `POST /api/inject-anomaly`
Injects a simulated micro-climate anomaly into a specific container.
- **Request Body**:
  ```json
  {
    "container_id": "ATMO-1190-WAG",
    "anomaly_type": "HUMIDITY_TEMP_SPIKE"
  }
  ```

---

## `POST /api/reroute`
Executes a commercial diversion order to lock a container onto its highest-value secondary port route.
- **Request Body**:
  ```json
  {
    "container_id": "ATMO-8824-BIO",
    "target_market_id": "MKT-ALG"
  }
  ```

---

## `POST /api/reset`
Resets all containers, histories, and route locks back to the initial baseline defined in `data/fleet_containers.json`.

---

## `GET /api/export-powerbi`
Forces an immediate export of the 4 Star-Schema CSV files in `powerbi db/datasets/`.
