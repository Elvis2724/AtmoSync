/**
 * AtmoSync Executive BI & Spoilage Arbitrage Dashboard Controller (`frontend/dashboard.js`)
 * Coordinates UI state, REST API polling, table actions, and feed updates.
 */

let latestPayload = null;
let selectedContainerId = "ATMO-4091-AVO";
let activeTableFilter = "ALL";
let pollIntervalId = null;

function populateAnomalyDropdown(containers) {
  const select = document.getElementById("anomalyContainerSelect");
  if (select.options.length === containers.length) return;
  const currentVal = select.value;
  select.innerHTML = "";
  containers.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.container_id;
    opt.textContent = `${c.container_id} (${c.commodity_name.split(" ")[0]})`;
    select.appendChild(opt);
  });
  if (currentVal) select.value = currentVal;
}

function renderDashboard(data) {
  latestPayload = data;
  const { kpis, containers, markets, alerts, kafka_stream, auto_stream_enabled } = data;

  populateAnomalyDropdown(containers);

  if (!containers.some((c) => c.container_id === selectedContainerId) && containers.length > 0) {
    selectedContainerId = containers[0].container_id;
  }

  const streamBadge = document.getElementById("streamStatusBadge");
  const btnToggle = document.getElementById("btnToggleStream");
  if (auto_stream_enabled) {
    streamBadge.textContent = "LIVE STREAMING";
    streamBadge.className = "badge-pill badge-live";
    btnToggle.textContent = "Pause Stream";
  } else {
    streamBadge.textContent = "STREAM PAUSED";
    streamBadge.className = "badge-pill badge-paused";
    btnToggle.textContent = "Resume Stream";
  }

  // 1. Update KPI Strip
  document.getElementById("kpiArbitrageUsd").textContent = fmtUSD(kpis.total_arbitrage_opportunity_usd);
  document.getElementById("kpiArbitrageSub").textContent =
    kpis.total_arbitrage_opportunity_usd > 0
      ? `Net gain from immediate secondary port rerouting`
      : `All shipments currently on optimal market routes`;

  document.getElementById("kpiAtRiskCount").textContent = `${kpis.at_risk_containers} / ${kpis.active_containers}`;
  document.getElementById("kpiCriticalTag").textContent = `${kpis.critical_containers} CRITICAL`;
  document.getElementById("kpiFleetValueSub").textContent = `Total Fleet Cargo: ${fmtUSD(kpis.total_fleet_cargo_usd)}`;
  document.getElementById("kpiAvgDegradation").textContent = `${kpis.avg_degradation_multiplier.toFixed(2)}x`;
  document.getElementById("kpiEventsCount").textContent = kpis.total_events_ingested.toLocaleString();
  document.getElementById("kpiLatencyTag").textContent = `${kpis.pipeline_latency_ms} ms`;

  // 2. Render Global Map
  renderGlobalMap(containers, markets, selectedContainerId, (cid) => {
    selectedContainerId = cid;
    if (latestPayload) renderDashboard(latestPayload);
  });

  // 3. Render Selected Container Inspector
  const selectedContainer = containers.find((c) => c.container_id === selectedContainerId) || containers[0];
  if (selectedContainer) {
    renderContainerInspector(selectedContainer, data.histories[selectedContainer.container_id] || []);
  }

  // 4. Render Arbitrage Table
  renderArbitrageTable(containers);

  // 5. Render Alerts & Kafka Stream
  renderAlertsFeed(alerts);
  renderKafkaStream(kafka_stream);
}

function renderContainerInspector(c, history) {
  document.getElementById("inspectorTitle").textContent = `${c.container_id} — ${c.commodity_name}`;
  document.getElementById("inspectorSubtitle").textContent =
    `Carrier: ${c.vessel_or_carrier} | Origin: ${c.origin_name} | Cargo Value: ${fmtUSD(c.base_cargo_value_usd)}`;

  const badge = document.getElementById("inspectorStatusBadge");
  badge.textContent = c.risk_status;
  badge.className = `status-chip ${getStatusClass(c.risk_status)}`;

  const tempEl = document.getElementById("insTemp");
  tempEl.textContent = `${c.temp_c.toFixed(2)} °C`;
  tempEl.style.color = c.temp_c > c.max_safe_temp_c ? "#f87171" : "#34d399";
  document.getElementById("insTempTarget").textContent = `Optimal: ${c.optimal_temp_c}°C (Max: ${c.max_safe_temp_c}°C)`;

  document.getElementById("insHumidity").textContent = `${c.humidity_pct.toFixed(1)} %`;
  document.getElementById("insHumidityTarget").textContent = `Optimal: ${c.optimal_humidity_pct}% RH`;

  document.getElementById("insVibration").textContent = `${c.vibration_g.toFixed(2)} G`;
  document.getElementById("insGasMeta").textContent = `CO2: ${c.co2_ppm} ppm | C2H4: ${c.ethylene_ppm} ppm`;

  const ttsEl = document.getElementById("insTTS");
  ttsEl.textContent = `${c.time_to_spoilage_hrs.toFixed(1)} hrs`;
  ttsEl.style.color = c.time_to_spoilage_hrs < c.primary_eta_hrs * 1.15 ? "#f87171" : "#f1f5f9";
  document.getElementById("insBurnRate").textContent = `Degradation: ${c.degradation_multiplier.toFixed(2)}x nominal`;

  document.getElementById("insCompressorTag").textContent = `Compressor: ${c.compressor_status}`;
  document.getElementById("insArbitrageGainText").textContent =
    c.spoilage_arbitrage_usd > 0
      ? `+${fmtUSD(c.spoilage_arbitrage_usd)} Spoilage Arbitrage`
      : `Primary Route Optimal`;

  const listEl = document.getElementById("insSecondaryOptionsList");
  listEl.innerHTML = (c.secondary_options || [])
    .map(
      (opt) => `
      <div class="sec-option-card">
        <div class="sec-option-top">
          <span>${opt.market_name}</span>
          <span class="text-emerald">${fmtUSD(opt.net_value_usd)}</span>
        </div>
        <div class="sec-option-meta">
          ETA: ${opt.eta_hrs}h (${opt.distance_km} km) | Arr. Quality: ${opt.arrival_quality_pct}% | Spot: ${opt.spot_multiplier}x
        </div>
      </div>
    `
    )
    .join("");

  drawDegradationCurve(c);
  drawTelemetryHistory(c, history);
}

function renderArbitrageTable(containers) {
  const tbody = document.getElementById("arbitrageTableBody");
  const filtered = containers.filter((c) => {
    if (activeTableFilter === "AT_RISK") {
      return c.spoilage_arbitrage_usd > 0 || c.risk_status === "CRITICAL ARBITRAGE" || c.risk_status === "ELEVATED DRIFT";
    }
    if (activeTableFilter === "REROUTED") {
      return Boolean(c.rerouted_to_market_id);
    }
    return true;
  });

  tbody.innerHTML = filtered
    .map((c) => {
      const isSelected = c.container_id === selectedContainerId;
      const tempWarn = c.temp_c > c.max_safe_temp_c ? "text-crimson" : "text-emerald";
      const arbClass = c.spoilage_arbitrage_usd > 0 ? "text-emerald" : "mono";

      return `
        <tr class="${isSelected ? "selected-row" : ""}" data-cid="${c.container_id}">
          <td>
            <div class="mono" style="font-weight:700;color:#fff;">${c.container_id}</div>
            <div style="font-size:0.69rem;color:#64748b;">${c.vessel_or_carrier}</div>
          </td>
          <td>
            <div style="font-weight:600;">${c.commodity_name}</div>
            <div style="font-size:0.68rem;color:#64748b;">Base: ${fmtUSD(c.base_cargo_value_usd)}</div>
          </td>
          <td class="mono">
            <span class="${tempWarn}">${c.temp_c.toFixed(1)}°C</span> /
            <span>${c.humidity_pct.toFixed(0)}%</span> /
            <span>${c.vibration_g.toFixed(2)}G</span>
          </td>
          <td class="mono ${c.degradation_multiplier >= 1.8 ? "text-amber" : ""}">
            ${c.degradation_multiplier.toFixed(2)}x
          </td>
          <td class="mono">${c.quality_remaining_pct.toFixed(1)}%</td>
          <td class="mono ${c.time_to_spoilage_hrs < c.primary_eta_hrs * 1.15 ? "text-crimson" : ""}">
            ${c.time_to_spoilage_hrs.toFixed(1)} hrs
          </td>
          <td>
            <div>${c.primary_market_name}</div>
            <div class="mono" style="font-size:0.68rem;color:#94a3b8;">
              ETA: ${c.primary_eta_hrs}h | Arr. Qual: ${c.primary_arrival_quality_pct}%
            </div>
          </td>
          <td class="mono">${fmtUSD(c.primary_expected_value_usd)}</td>
          <td>
            <div>${c.recommended_secondary_market}</div>
            <div class="mono" style="font-size:0.68rem;color:#94a3b8;">
              ETA: ${c.secondary_eta_hrs}h | Arr. Qual: ${c.secondary_arrival_quality_pct}%
            </div>
          </td>
          <td class="mono">${fmtUSD(c.secondary_net_value_usd)}</td>
          <td class="mono ${arbClass}" style="font-size:0.86rem;">
            ${c.spoilage_arbitrage_usd > 0 ? `+${fmtUSD(c.spoilage_arbitrage_usd)}` : "$0"}
          </td>
          <td>
            <span class="status-chip ${getStatusClass(c.risk_status)}">${c.risk_status}</span>
          </td>
          <td>
            ${
              c.spoilage_arbitrage_usd > 0 && !c.rerouted_to_market_id
                ? `<button class="btn-reroute" data-action="reroute" data-cid="${c.container_id}" data-mkt="${c.recommended_secondary_id}">
                     Execute Reroute &rarr;
                   </button>`
                : c.rerouted_to_market_id
                ? `<span class="mono text-cyan" style="font-size:0.71rem;">&#10003; Dispatched</span>`
                : `<button class="btn-table-sub" data-action="spike" data-cid="${c.container_id}">
                     Simulate Drift
                   </button>`
            }
          </td>
        </tr>
      `;
    })
    .join("");

  tbody.querySelectorAll("tr").forEach((row) => {
    row.addEventListener("click", (e) => {
      if (e.target.closest("button")) return;
      selectedContainerId = row.getAttribute("data-cid");
      if (latestPayload) renderDashboard(latestPayload);
    });
  });

  tbody.querySelectorAll("button[data-action='reroute']").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const cid = btn.getAttribute("data-cid");
      const mkt = btn.getAttribute("data-mkt");
      if (standaloneMode && latestPayload) {
        const target = latestPayload.containers.find((x) => x.container_id === cid);
        if (target) {
          latestPayload.kpis.total_arbitrage_opportunity_usd = Math.max(
            0,
            latestPayload.kpis.total_arbitrage_opportunity_usd - target.spoilage_arbitrage_usd
          );
          target.rerouted_to_market_id = mkt;
          target.primary_market_name = target.recommended_secondary_market;
          target.spoilage_arbitrage_usd = 0;
          target.risk_status = "REROUTED (LOCKED)";
          renderDashboard(latestPayload);
          showToast(`Order Dispatched: ${cid} rerouted to capture Spoilage Arbitrage!`);
        }
        return;
      }
      const res = await fetch("/api/reroute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ container_id: cid, target_market_id: mkt }),
      });
      if (res.ok) {
        const data = await res.json();
        selectedContainerId = cid;
        renderDashboard(data);
        showToast(`Order Dispatched: ${cid} rerouted to capture Spoilage Arbitrage!`);
      }
    });
  });

  tbody.querySelectorAll("button[data-action='spike']").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const cid = btn.getAttribute("data-cid");
      if (standaloneMode && latestPayload) {
        const target = latestPayload.containers.find((x) => x.container_id === cid);
        if (target) {
          target.temp_c = +(target.max_safe_temp_c + 2.8).toFixed(1);
          target.degradation_multiplier = 2.95;
          target.spoilage_arbitrage_usd = 84500;
          target.risk_status = "CRITICAL ARBITRAGE";
          latestPayload.kpis.total_arbitrage_opportunity_usd += 84500;
          selectedContainerId = cid;
          renderDashboard(latestPayload);
          showToast(`Micro-Climate Anomaly injected on ${cid} — Spoilage Arbitrage recalculated!`);
        }
        return;
      }
      const res = await fetch("/api/inject-anomaly", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ container_id: cid, anomaly_type: "HUMIDITY_TEMP_SPIKE" }),
      });
      if (res.ok) {
        const data = await res.json();
        selectedContainerId = cid;
        renderDashboard(data);
        showToast(`Micro-Climate Anomaly injected on ${cid} — Spoilage Arbitrage recalculated!`);
      }
    });
  });
}

function renderAlertsFeed(alerts) {
  const el = document.getElementById("alertsFeedList");
  if (!alerts || alerts.length === 0) {
    el.innerHTML = `<div class="alert-item">No high-value arbitrage alerts triggered yet.</div>`;
    return;
  }
  el.innerHTML = alerts
    .map(
      (a) => `
      <div class="alert-item alert-${a.severity}">
        <div class="alert-top">
          <span><strong>${a.alert_id}</strong> &bull; ${a.channel}</span>
          <span>${a.timestamp.slice(11, 19)} UTC</span>
        </div>
        <div>${a.message}</div>
      </div>
    `
    )
    .join("");
}

function renderKafkaStream(stream) {
  const el = document.getElementById("kafkaStreamList");
  if (!stream || stream.length === 0) return;
  el.innerHTML = stream
    .map(
      (ev) => `
      <div class="kafka-item">
        <div class="kafka-meta">
          topic=${ev.topic} | part=${ev.partition} | offset=${ev.offset} | ts=${ev.timestamp.slice(11, 19)}Z
        </div>
        <div>${JSON.stringify(ev.payload)}</div>
      </div>
    `
    )
    .join("");
}

document.addEventListener("DOMContentLoaded", () => {
  fetchDashboardState();
  pollIntervalId = setInterval(fetchDashboardState, 3000);

  document.getElementById("btnStepTick").addEventListener("click", async () => {
    if (standaloneMode) {
      fetchDashboardState();
      showToast("Advanced IoT telemetry stream by +1 tick.");
      return;
    }
    const res = await fetch("/api/step", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      renderDashboard(data);
      showToast("Advanced IoT telemetry stream by +1 tick and refreshed dbt/Power BI tables.");
    }
  });

  document.getElementById("btnToggleStream").addEventListener("click", async () => {
    if (standaloneMode && latestPayload) {
      latestPayload.auto_stream_enabled = !latestPayload.auto_stream_enabled;
      renderDashboard(latestPayload);
      return;
    }
    const res = await fetch("/api/toggle-stream", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      renderDashboard(data);
    }
  });

  document.getElementById("btnInjectAnomaly").addEventListener("click", async () => {
    const cid = document.getElementById("anomalyContainerSelect").value;
    if (standaloneMode && latestPayload) {
      const target = latestPayload.containers.find((x) => x.container_id === cid);
      if (target) {
        target.temp_c = +(target.max_safe_temp_c + 2.8).toFixed(1);
        target.degradation_multiplier = 3.1;
        target.spoilage_arbitrage_usd = Math.max(target.spoilage_arbitrage_usd, 92000);
        target.risk_status = "CRITICAL ARBITRAGE";
        selectedContainerId = cid;
        renderDashboard(latestPayload);
        showToast(`Simulated micro-climate spike inside ${cid}. Check Spoilage Arbitrage Desk!`);
      }
      return;
    }
    const res = await fetch("/api/inject-anomaly", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ container_id: cid, anomaly_type: "HUMIDITY_TEMP_SPIKE" }),
    });
    if (res.ok) {
      const data = await res.json();
      selectedContainerId = cid;
      renderDashboard(data);
      showToast(`Simulated micro-climate spike inside ${cid}. Check Spoilage Arbitrage Desk!`);
    }
  });

  document.getElementById("btnExportPowerBI").addEventListener("click", async () => {
    if (standaloneMode) {
      showToast("Power BI Star-Schema CSVs are ready in /powerbi db/datasets/!");
      return;
    }
    const res = await fetch("/api/export-powerbi");
    if (res.ok) {
      showToast("Power BI Star-Schema CSVs & SQLite warehouse synced in /powerbi db/datasets/!");
    }
  });

  document.getElementById("btnResetFleet").addEventListener("click", async () => {
    if (standaloneMode) {
      latestPayload = createStandaloneState();
      renderDashboard(latestPayload);
      showToast("Fleet telemetry and route states reset to baseline.");
      return;
    }
    const res = await fetch("/api/reset", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      renderDashboard(data);
      showToast("Fleet telemetry and route states reset to baseline.");
    }
  });

  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeTableFilter = btn.getAttribute("data-filter");
      if (latestPayload) renderArbitrageTable(latestPayload.containers);
    });
  });
});
