/**
 * AtmoSync SVG Global Route Map & HTML5 Canvas Telemetry Charts (`frontend/charts.js`)
 */

// Convert lat/lon (-60..70, -180..180) to SVG 1000x460 coordinates
function projectLatLon(lat, lon) {
  const x = ((lon + 180) / 360) * 940 + 30;
  const clampedLat = Math.max(-55, Math.min(72, lat));
  const y = ((72 - clampedLat) / 127) * 410 + 25;
  return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 };
}

function getStatusClass(riskStatus) {
  if (riskStatus === "CRITICAL ARBITRAGE") return "chip-critical";
  if (riskStatus === "ELEVATED DRIFT") return "chip-elevated";
  if (riskStatus && riskStatus.startsWith("REROUTED")) return "chip-rerouted";
  return "chip-optimal";
}

function getStatusColor(riskStatus) {
  if (riskStatus === "CRITICAL ARBITRAGE") return "#ef4444";
  if (riskStatus === "ELEVATED DRIFT") return "#f59e0b";
  if (riskStatus && riskStatus.startsWith("REROUTED")) return "#06b6d4";
  return "#10b981";
}

function renderGlobalMap(containers, markets, selectedId, onSelectContainer) {
  const svg = document.getElementById("worldRouteMap");
  const marketLookup = {};
  markets.forEach((m) => (marketLookup[m.market_id] = m));

  const continentsSvg = `
    <defs>
      <pattern id="oceanGrid" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(30, 45, 74, 0.38)" stroke-width="0.8"/>
      </pattern>
    </defs>
    <rect width="1000" height="460" fill="url(#oceanGrid)" />
    <g fill="#122038" stroke="#1f355c" stroke-width="1">
      <polygon points="95,60 245,55 290,130 240,195 195,220 140,175 95,115" />
      <polygon points="225,235 305,255 335,315 295,415 255,410 235,310" />
      <polygon points="445,65 565,55 585,125 520,155 450,145" />
      <polygon points="445,165 555,165 605,245 560,365 495,365 450,255" />
      <polygon points="575,65 865,65 895,185 805,245 715,240 615,195 585,130" />
      <polygon points="775,305 895,300 910,375 805,390 770,350" />
    </g>
  `;

  let routesSvg = "";
  let portsSvg = "";
  let containersSvg = "";

  markets.forEach((m) => {
    const pt = projectLatLon(m.lat, m.lon);
    portsSvg += `
      <g transform="translate(${pt.x}, ${pt.y})">
        <circle r="4" fill="#94a3b8" stroke="#ffffff" stroke-width="1.2" />
        <text x="7" y="3" fill="#94a3b8" font-size="9.5" font-family="Inter, sans-serif">${m.name.split(" ")[0]}</text>
      </g>
    `;
  });

  containers.forEach((c) => {
    const curPt = projectLatLon(c.current_lat, c.current_lon);
    const primMkt = marketLookup[c.primary_market_id];
    const secMkt = marketLookup[c.recommended_secondary_id];
    const isSelected = c.container_id === selectedId;
    const color = getStatusColor(c.risk_status);

    if (primMkt) {
      const primPt = projectLatLon(primMkt.lat, primMkt.lon);
      routesSvg += `
        <line x1="${curPt.x}" y1="${curPt.y}" x2="${primPt.x}" y2="${primPt.y}"
          stroke="${c.spoilage_arbitrage_usd > 0 ? "rgba(239,68,68,0.45)" : "rgba(16,185,129,0.5)"}"
          stroke-width="${isSelected ? 2.4 : 1.3}"
          stroke-dasharray="${c.spoilage_arbitrage_usd > 0 ? "4,4" : "none"}" />
      `;
    }

    if (secMkt && c.spoilage_arbitrage_usd > 0 && !c.rerouted_to_market_id) {
      const secPt = projectLatLon(secMkt.lat, secMkt.lon);
      routesSvg += `
        <line x1="${curPt.x}" y1="${curPt.y}" x2="${secPt.x}" y2="${secPt.y}"
          stroke="#10b981" stroke-width="${isSelected ? 2.8 : 1.8}" stroke-dasharray="6,3" />
      `;
    }

    containersSvg += `
      <g class="map-container-node" data-cid="${c.container_id}" transform="translate(${curPt.x}, ${curPt.y})" style="cursor:pointer;">
        ${
          c.risk_status === "CRITICAL ARBITRAGE"
            ? `<circle r="14" fill="rgba(239, 68, 68, 0.22)" stroke="#ef4444" stroke-width="1" />`
            : ""
        }
        ${
          isSelected
            ? `<circle r="11" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="3,2" />`
            : ""
        }
        <circle r="6.5" fill="${color}" stroke="#070b14" stroke-width="1.8" />
        <rect x="-42" y="-24" width="84" height="14" rx="3" fill="rgba(7,11,20,0.85)" stroke="${color}" stroke-width="0.8" />
        <text x="0" y="-14" text-anchor="middle" fill="#f8fafc" font-size="8.8" font-family="JetBrains Mono, monospace" font-weight="700">
          ${c.container_id.replace("ATMO-", "")} (${c.temp_c.toFixed(1)}°C)
        </text>
      </g>
    `;
  });

  svg.innerHTML = continentsSvg + routesSvg + portsSvg + containersSvg;

  svg.querySelectorAll(".map-container-node").forEach((node) => {
    node.addEventListener("click", () => {
      const cid = node.getAttribute("data-cid");
      if (onSelectContainer) onSelectContainer(cid);
    });
  });
}

function drawDegradationCurve(c) {
  const canvas = document.getElementById("degradationCurveCanvas");
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padL = 42, padR = 18, padT = 16, padB = 26;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const maxHours = Math.max(80, c.primary_eta_hrs * 1.25, c.time_to_spoilage_hrs * 1.15);

  const xForHr = (hr) => padL + (Math.min(maxHours, hr) / maxHours) * plotW;
  const yForQual = (q) => padT + ((100 - Math.max(40, Math.min(100, q))) / 60) * plotH;

  ctx.strokeStyle = "rgba(148, 163, 184, 0.14)";
  ctx.lineWidth = 1;
  [100, 80, 55].forEach((q) => {
    const y = yForQual(q);
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(W - padR, y);
    ctx.stroke();
    ctx.fillStyle = q === 55 ? "#f87171" : "#64748b";
    ctx.font = "10px JetBrains Mono, monospace";
    ctx.fillText(`${q}%`, 6, y + 3);
  });

  const ySpoil = yForQual(55);
  ctx.strokeStyle = "rgba(239, 68, 68, 0.65)";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(padL, ySpoil);
  ctx.lineTo(W - padR, ySpoil);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = c.spoilage_arbitrage_usd > 0 ? "#f59e0b" : "#38bdf8";
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  for (let i = 0; i <= 40; i++) {
    const hr = (maxHours * i) / 40;
    const q = c.quality_remaining_pct - hr * c.burn_rate_pct_per_hr;
    const x = xForHr(hr);
    const y = yForQual(q);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  if (c.secondary_eta_hrs && c.secondary_eta_hrs < maxHours) {
    const sx = xForHr(c.secondary_eta_hrs);
    const sy = yForQual(c.secondary_arrival_quality_pct);
    ctx.fillStyle = "#10b981";
    ctx.beginPath();
    ctx.arc(sx, sy, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = "bold 10px Inter, sans-serif";
    ctx.fillText(`2nd ETA (${c.secondary_eta_hrs}h: ${c.secondary_arrival_quality_pct}%)`, Math.min(W - 155, sx + 6), Math.max(14, sy - 6));
  }

  if (c.primary_eta_hrs) {
    const px = xForHr(c.primary_eta_hrs);
    const py = yForQual(c.primary_arrival_quality_pct);
    ctx.fillStyle = c.primary_arrival_quality_pct < 68 ? "#ef4444" : "#3b82f6";
    ctx.beginPath();
    ctx.arc(px, py, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = "bold 10px Inter, sans-serif";
    ctx.fillText(`Primary ETA (${c.primary_eta_hrs}h: ${c.primary_arrival_quality_pct}%)`, Math.max(padL + 6, Math.min(W - 165, px - 60)), Math.min(H - 8, py + 14));
  }
}

function drawTelemetryHistory(c, history) {
  const canvas = document.getElementById("telemetryHistoryCanvas");
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  if (!history || history.length < 2) return;

  const padL = 42, padR = 18, padT = 14, padB = 20;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const temps = history.map((h) => h.temp_c);
  const minT = Math.min(...temps, c.optimal_temp_c - 2);
  const maxT = Math.max(...temps, c.max_safe_temp_c + 2);
  const rangeT = Math.max(2, maxT - minT);

  const xForIdx = (i) => padL + (i / (history.length - 1)) * plotW;
  const yForTemp = (t) => padT + ((maxT - t) / rangeT) * plotH;

  const ySafe = yForTemp(c.max_safe_temp_c);
  ctx.strokeStyle = "rgba(239, 68, 68, 0.5)";
  ctx.setLineDash([3, 3]);
  ctx.beginPath();
  ctx.moveTo(padL, ySafe);
  ctx.lineTo(W - padR, ySafe);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#f87171";
  ctx.font = "9.5px JetBrains Mono, monospace";
  ctx.fillText(`Max ${c.max_safe_temp_c}°C`, 2, ySafe + 3);

  const yOpt = yForTemp(c.optimal_temp_c);
  ctx.strokeStyle = "rgba(16, 185, 129, 0.4)";
  ctx.beginPath();
  ctx.moveTo(padL, yOpt);
  ctx.lineTo(W - padR, yOpt);
  ctx.stroke();
  ctx.fillStyle = "#34d399";
  ctx.fillText(`Opt ${c.optimal_temp_c}°C`, 2, yOpt + 3);

  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  history.forEach((pt, idx) => {
    const x = xForIdx(idx);
    const y = yForTemp(pt.temp_c);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
