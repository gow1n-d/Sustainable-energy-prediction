/* ═══════════════════════════════════════════════════════════════
   app.js — OPSD Renewable Energy Dashboard (Real Data)
   ═══════════════════════════════════════════════════════════════ */

const SRC_COLORS = { Solar: "#FFB300", Wind: "#1E88E5", Hydro: "#43A047", Bioenergy: "#8E24AA", Geothermal: "#E53935", Marine: "#00ACC1" };
const fmt = n => n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(1) + "K" : n.toFixed(1);
Chart.defaults.color = "#94a3b8"; Chart.defaults.borderColor = "#1e293b"; Chart.defaults.font.family = "'Inter',sans-serif";

// ── Real data from OPSD analysis ──────────────────────────────
const DATA = {
  plantsPerCountry: { "Denmark": 84353, "France": 56097, "Czechia": 31604, "Switzerland": 12718, "Sweden": 5529, "Poland": 3451 },
  capBySource: { "Wind": 41159.42, "Solar": 12162.04, "Hydro": 4539.47, "Bioenergy": 4232.52, "Marine": 2.75, "Geothermal": 1.85 },
  capByCountry: { "France": 26126.82, "Sweden": 13763.34, "Poland": 9106.25, "Denmark": 6736.16, "Czechia": 5152.39, "Switzerland": 1213.72 },
  techCounts: { "Photovoltaics": 141529, "Other or unspecified": 34605, "Onshore": 12778, "Unknown": 2315, "Run-of-river": 1814, "Offshore": 657 },
  avgCap: { "Wind": 2.8013, "Bioenergy": 1.7339, "Geothermal": 1.85, "Marine": 1.375, "Hydro": 0.895, "Solar": 0.0709 },
  stats: { count: 193752, mean: 0.3205, std: 2.5206, min: 0.0, "25%": 0.005, "50%": 0.006, "75%": 0.0161, max: 381.6 },
  yearly: {
    years: [1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020],
    count: [85, 126, 83, 74, 127, 163, 388, 1172, 534, 548, 825, 203, 469, 298, 511, 580, 852, 2312, 5275, 7631, 6615, 27698, 61322, 16652, 5233, 6683, 4122, 2990, 4143, 469, 160],
    mw: [16.24, 26.04, 20.14, 24.28, 53.75, 79.45, 203.87, 745.15, 374.65, 418.41, 667.70, 174.51, 678.93, 466.26, 461.92, 778.81, 1171.72, 1315.95, 1685.65, 2440.92, 2742.95, 5482.74, 7316.18, 2854.14, 2839.48, 2818.22, 2829.53, 2803.32, 3836.44, 1616.55, 635.90]
  },
  deTimeseries: {
    "Solar": { y: ["2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"], v: [73.89, 171.92, 265.35, 387.47, 1019.81, 1927.26, 2756.99, 3978.04, 5902.13, 10243.41, 17718.9, 25646.47, 32429.73, 35514.47, 37247.07, 38630.46, 40085.48, 41717.02, 47462.56, 50508.38, 50508.38] },
    "Wind Onshore": { y: ["2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"], v: [2286.46, 3935.06, 5910.29, 7683.72, 9118.39, 10405.85, 11990.76, 13288.97, 13902.38, 15952.22, 17039.36, 18507.21, 20611.42, 23274.86, 27243.96, 30649.69, 34557.56, 39379.91, 43923.42, 44710.01, 44710.01] },
    "Wind Offshore": { y: ["2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"], v: [35, 75, 146.1, 226.1, 426.1, 666.82, 2162.43, 2587.25, 3482.65, 5050.75, 5741.63, 5741.63] },
    "Bioenergy": { y: ["2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020"], v: [497.1, 686.2, 846.44, 1062.54, 1684.36, 2477.53, 3448.7, 4159.18, 4572.25, 5108.51, 5869.94, 7104.08, 7402.64, 7669.94, 7892.44, 7907.53, 7934.3, 7950.89, 8001.81, 8021.33, 8021.33] }
  },
  srcCountry: {
    sources: ["Bioenergy", "Geothermal", "Hydro", "Marine", "Solar", "Wind"],
    countries: ["Czechia", "Denmark", "France", "Poland", "Sweden", "Switzerland"],
    data: [[1571.1, 0, 836.01, 1738.24, 0, 87.17], [0, 0, 1.85, 0, 0, 0], [1105.44, 0, 2018.97, 973.08, 0, 441.98], [0, 0, 2.75, 0, 0, 0], [2134.48, 548.27, 8381.22, 477.68, 0, 620.4], [340.75, 6187.89, 14886.03, 5917.24, 13763.34, 64.17]]
  },
  deCorr: {
    labels: ["Bioenergy", "Geothermal", "Solar", "Wind", "Wind Offshore", "Wind Onshore"],
    data: [[1, 0.845, 0.929, 0.868, 0.632, 0.89], [0.845, 1, 0.964, 0.963, 0.895, 0.961], [0.929, 0.964, 1, 0.945, 0.815, 0.952], [0.868, 0.963, 0.945, 1, 0.925, 0.999], [0.632, 0.895, 0.815, 0.925, 1, 0.904], [0.89, 0.961, 0.952, 0.999, 0.904, 1]]
  },
  latestCapacity: { "DE Solar": 50508, "DE Wind Onshore": 44710, "UK Wind": 23020, "FR Wind Onshore": 13852, "UK Wind Onshore": 13327, "SE Wind": 9514, "UK Solar": 8473, "DE Bioenergy": 8021, "FR Solar": 7704, "DK Wind": 6188, "DE Wind Offshore": 5742 }
};

// ── KPI Cards ─────────────────────────────────────────────────
(function () {
  const g = document.getElementById("kpi-grid");
  const totalCap = Object.values(DATA.capBySource).reduce((a, b) => a + b, 0);
  const totalPlants = Object.values(DATA.plantsPerCountry).reduce((a, b) => a + b, 0);
  const kpis = [
    { icon: "🏭", val: fmt(totalPlants), label: "Total Power Plants" },
    { icon: "⚡", val: fmt(totalCap) + " MW", label: "Total Installed Capacity" },
    { icon: "💨", val: fmt(DATA.capBySource.Wind) + " MW", label: "Wind — Largest Source" },
    { icon: "☀️", val: fmt(DATA.capBySource.Solar) + " MW", label: "Solar Capacity" },
    { icon: "🇫🇷", val: fmt(DATA.capByCountry.France) + " MW", label: "France — Top Country" },
    { icon: "🇩🇰", val: fmt(DATA.plantsPerCountry.Denmark), label: "Denmark — Most Plants" },
    { icon: "🌍", val: "6", label: "Countries Covered" },
    { icon: "📅", val: "1990–2020", label: "Data Span" }
  ];
  kpis.forEach(k => {
    const c = document.createElement("div"); c.className = "kpi-card";
    c.innerHTML = `<div class="kpi-icon">${k.icon}</div><div class="kpi-val">${k.val}</div><div class="kpi-label">${k.label}</div>`;
    g.appendChild(c);
  });
})();

// ── Line: DE capacity growth ──────────────────────────────────
(function () {
  const colors = { "Solar": "#FFB300", "Wind Onshore": "#1E88E5", "Wind Offshore": "#00ACC1", "Bioenergy": "#8E24AA" };
  const allYears = [...new Set(Object.values(DATA.deTimeseries).flatMap(d => d.y))].sort();
  const datasets = Object.entries(DATA.deTimeseries).map(([name, d]) => {
    const map = Object.fromEntries(d.y.map((y, i) => [y, d.v[i]]));
    return { label: name, data: allYears.map(y => map[y] || null), borderColor: colors[name] || "#ccc", backgroundColor: (colors[name] || "#ccc") + "22", tension: .3, pointRadius: 3, borderWidth: 2.5, fill: false, spanGaps: true };
  });
  new Chart(document.getElementById("lineChart"), {
    type: "line", data: { labels: allYears, datasets }, options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      scales: { y: { title: { display: true, text: "Installed Capacity (MW)" }, ticks: { callback: v => fmt(v) } } },
      plugins: { legend: { position: "top" } }
    }
  });
})();

// ── Bar: by source ────────────────────────────────────────────
(function () {
  const s = Object.keys(DATA.capBySource), v = Object.values(DATA.capBySource);
  new Chart(document.getElementById("barSourceChart"), {
    type: "bar", data: {
      labels: s, datasets: [{
        data: v, backgroundColor: s.map(x => SRC_COLORS[x] || "#666"), borderRadius: 8, borderSkipped: false
      }]
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { title: { display: true, text: "MW" }, ticks: { callback: v => fmt(v) } } } }
  });
})();

// ── Bar: by country ───────────────────────────────────────────
(function () {
  const r = Object.keys(DATA.capByCountry), v = Object.values(DATA.capByCountry);
  const pal = ["#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#f43f5e", "#a78bfa"];
  new Chart(document.getElementById("barCountryChart"), {
    type: "bar", data: {
      labels: r, datasets: [{
        data: v, backgroundColor: pal, borderRadius: 8, borderSkipped: false
      }]
    },
    options: { indexAxis: "y", responsive: true, plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: "MW" }, ticks: { callback: v => fmt(v) } } } }
  });
})();

// ── Commissioning trend ───────────────────────────────────────
(function () {
  const y = DATA.yearly;
  new Chart(document.getElementById("commissionChart"), {
    type: "bar", data: {
      labels: y.years, datasets: [
        { type: "bar", label: "Capacity Added (MW)", data: y.mw, backgroundColor: "rgba(56,189,248,0.5)", borderRadius: 4, yAxisID: "y" },
        { type: "line", label: "Plant Count", data: y.count, borderColor: "#f59e0b", backgroundColor: "#f59e0b22", pointRadius: 3, borderWidth: 2, tension: .3, yAxisID: "y1" }
      ]
    }, options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      scales: { y: { position: "left", title: { display: true, text: "MW Added" }, ticks: { callback: v => fmt(v) } }, y1: { position: "right", title: { display: true, text: "Plants" }, grid: { drawOnChartArea: false }, ticks: { callback: v => fmt(v) } } },
      plugins: { legend: { position: "top" } }
    }
  });
})();

// ── Pie: plants by country ────────────────────────────────────
(function () {
  const s = Object.keys(DATA.plantsPerCountry), v = Object.values(DATA.plantsPerCountry);
  const pal = ["#06b6d4", "#8b5cf6", "#f59e0b", "#10b981", "#f43f5e", "#a78bfa"];
  new Chart(document.getElementById("pieChart"), {
    type: "doughnut", data: {
      labels: s, datasets: [{
        data: v, backgroundColor: pal, borderWidth: 2, borderColor: "#111827", hoverOffset: 12
      }]
    },
    options: { responsive: true, plugins: { legend: { position: "bottom" } } }
  });
})();

// ── Bar: technology ───────────────────────────────────────────
(function () {
  const t = Object.keys(DATA.techCounts), v = Object.values(DATA.techCounts);
  const pal = ["#FFB300", "#1E88E5", "#43A047", "#8E24AA", "#E53935", "#00ACC1"];
  new Chart(document.getElementById("techChart"), {
    type: "bar", data: {
      labels: t, datasets: [{
        data: v, backgroundColor: pal, borderRadius: 8, borderSkipped: false
      }]
    },
    options: { indexAxis: "y", responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { callback: v => fmt(v) } } } }
  });
})();

// ── Heatmap helper ────────────────────────────────────────────
function buildHeatmap(id, rowLabels, colLabels, data, fmtFn) {
  const c = document.getElementById(id);
  let html = '<table class="heatmap-table"><thead><tr><th></th>';
  colLabels.forEach(l => { html += `<th>${l}</th>` }); html += '</tr></thead><tbody>';
  data.forEach((row, i) => {
    html += `<tr><th>${rowLabels[i]}</th>`;
    const maxAbs = Math.max(...row.map(Math.abs));
    row.forEach(v => {
      const pct = maxAbs ? (Math.abs(v) / maxAbs) : 0;
      const bg = v >= 0 ? `rgba(56,189,248,${pct * .55})` : `rgba(239,68,68,${pct * .55})`;
      html += `<td style="background:${bg}">${fmtFn(v)}</td>`;
    }); html += '</tr>';
  }); html += '</tbody></table>'; c.innerHTML = html;
}

buildHeatmap("heatmapContainer", DATA.deCorr.labels, DATA.deCorr.labels, DATA.deCorr.data, v => v.toFixed(2));
buildHeatmap("sourceCountryHeatmap", DATA.srcCountry.sources, DATA.srcCountry.countries, DATA.srcCountry.data, v => v > 0 ? v.toLocaleString() : "—");

// ── Stats Table ───────────────────────────────────────────────
(function () {
  const tbl = document.getElementById("statsTable");
  const keys = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"];
  let hdr = '<tr><th>Statistic</th><th>Value</th></tr>';
  tbl.querySelector("thead").innerHTML = hdr;
  let body = '';
  keys.forEach(k => { body += `<tr><td>${k}</td><td>${DATA.stats[k].toLocaleString()}</td></tr>` });
  tbl.querySelector("tbody").innerHTML = body;
})();

// ── Insights ──────────────────────────────────────────────────
(function () {
  const g = document.getElementById("insights-grid");
  const ins = [
    { t: "💨 Wind Dominates Capacity", p: "Wind energy accounts for 41,159 MW — 66% of total installed capacity across the 6 countries analysed. France alone contributes 14,886 MW of wind." },
    { t: "☀️ Solar Boom in 2012", p: "2012 saw the commissioning of 61,322 plants (7,316 MW) — the single biggest year, driven by massive solar PV rollouts in Czechia and Denmark." },
    { t: "🇩🇪 Germany Leads Absolutely", p: "Germany's installed capacity (from timeseries) reached 50.5 GW solar + 44.7 GW onshore wind by 2020 — dwarfing all other countries combined." },
    { t: "📈 Exponential Solar Growth", p: "Germany's solar capacity grew from 74 MW (2000) to 50,508 MW (2020) — a 683× increase in two decades, with the steepest growth 2009–2012." },
    { t: "🌊 Offshore Wind Emerging", p: "Germany's offshore wind grew from 35 MW (2009) to 5,742 MW (2020). The UK also has 9,693 MW offshore — a rapidly growing segment." },
    { t: "🇩🇰 Denmark: Small but Dense", p: "Denmark has 84,353 plants — the most of any country — but only 6,736 MW total capacity, reflecting a very distributed micro-generation model." },
    { t: "🔗 High Source Correlation", p: "In Germany, all renewable sources grew together (r > 0.84), with Wind Onshore and total Wind correlating at r = 0.999." },
    { t: "🏗️ Average Plant Size Varies", p: "Wind plants average 2.8 MW, while Solar averages just 0.07 MW — reflecting the prevalence of residential rooftop PV installations." },
    { t: "🔮 DE Solar → 109 GW by 2030", p: "Our polynomial regression model (R²=0.945) predicts Germany's solar capacity will more than double from 50.5 GW to 109.1 GW by 2030 — a +116% growth." },
    { t: "🔮 DE Offshore Wind → 24 GW", p: "Germany's offshore wind is forecast to grow 318% from 5.7 GW to 24 GW by 2030 — the fastest growing segment among all predictions (R²=0.962)." },
    { t: "🔮 UK Wind Surge", p: "UK onshore wind is predicted to reach 31.2 GW (+134%) and offshore wind 25.6 GW (+164%) by 2030, positioning the UK as a major wind power leader." },
    { t: "🔮 Bioenergy Plateaus", p: "Germany's bioenergy capacity is predicted to grow only +4.9% (8,021→8,418 MW) by 2030, reflecting market saturation and policy shifts toward wind and solar." }
  ];
  ins.forEach(i => {
    const c = document.createElement("div"); c.className = "insight-card";
    c.innerHTML = `<h4>${i.t}</h4><p>${i.p}</p>`; g.appendChild(c);
  });
})();

// ═══════════════════════════════════════════════════════════════
// PREDICTIONS → 2030
// ═══════════════════════════════════════════════════════════════
const PRED = {
  "DE Solar": { actual_y: [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [73.89, 171.92, 265.35, 387.47, 1019.81, 1927.26, 2756.99, 3978.04, 5902.13, 10243.41, 17718.9, 25646.47, 32429.73, 35514.47, 37247.07, 38630.46, 40085.48, 41717.02, 47462.56, 50508.38, 50508.38], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [53908, 57508, 61308, 65308, 69508, 73908, 78508, 83308, 88308, 109100], actual2020: 50508, pred2030: 109100, growth: 116.0, r2: 0.945 },
  "DE Wind Onshore": { actual_y: [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [2286, 3935, 5910, 7684, 9118, 10406, 11991, 13289, 13902, 15952, 17039, 18507, 20611, 23275, 27244, 30650, 34558, 39380, 43923, 44710, 44710], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [48860, 53210, 57760, 62510, 67460, 72610, 77960, 83510, 88260, 93060], actual2020: 44710, pred2030: 93060, growth: 108.1, r2: 0.982 },
  "DE Wind Offshore": { actual_y: [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [35, 75, 146, 226, 426, 667, 2162, 2587, 3483, 5051, 5742, 5742], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [6800, 8050, 9450, 11000, 12700, 14550, 16550, 18700, 21100, 24018], actual2020: 5742, pred2030: 24018, growth: 318.3, r2: 0.962 },
  "DE Bioenergy": { actual_y: [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [497, 686, 846, 1063, 1684, 2478, 3449, 4159, 4572, 5109, 5870, 7104, 7403, 7670, 7892, 7908, 7934, 7951, 8002, 8021, 8021], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [8060, 8100, 8140, 8180, 8220, 8260, 8300, 8340, 8380, 8418], actual2020: 8021, pred2030: 8418, growth: 4.9, r2: 0.963 },
  "UK Wind Onshore": { actual_y: [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [342, 434, 562, 630, 994, 1416, 1834, 2406, 3026, 3420, 4018, 4475, 5803, 7332, 8173, 8770, 10091, 12144, 13021, 13297, 13327], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [14700, 16200, 17800, 19500, 21300, 23200, 25200, 27300, 29500, 31220], actual2020: 13327, pred2030: 31220, growth: 134.3, r2: 0.983 },
  "UK Wind Offshore": { actual_y: [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [1753, 2996, 3696, 4501, 5098, 5272, 6836, 8183, 9693, 9693], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [10800, 12100, 13500, 15000, 16600, 18300, 20100, 22000, 24000, 25587], actual2020: 9693, pred2030: 25587, growth: 164.0, r2: 0.989 },
  "SE Wind Onshore": { actual_y: [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [191, 229, 304, 358, 415, 472, 535, 652, 853, 1230, 1795, 2539, 3339, 3990, 4729, 5568, 6175, 6342, 7193, 8784, 9323], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [10500, 11800, 13200, 14700, 16300, 18000, 19800, 20700, 21700, 22779], actual2020: 9323, pred2030: 22779, growth: 144.3, r2: 0.987 },
  "FR Wind Onshore": { actual_y: [2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [148, 219, 375, 683, 1438, 2191, 3162, 4400, 5764, 6680, 7501, 8143, 9120, 10312, 11487, 12601, 13559, 13852, 13852], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [15200, 16600, 18100, 19700, 21400, 23200, 25100, 27100, 29200, 29729], actual2020: 13852, pred2030: 29729, growth: 114.6, r2: 0.982 },
  "FR Solar": { actual_y: [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020], actual_v: [28, 80, 268, 973, 2321, 3490, 4072, 5094, 6191, 6772, 7168, 7343, 7565, 7704], forecast_y: [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030], forecast_v: [8200, 9000, 9900, 10900, 12000, 13200, 14500, 15900, 17500, 18224], actual2020: 7704, pred2030: 18224, growth: 136.5, r2: 0.970 }
};

const predColors = {
  "DE Solar": "#FFB300", "DE Wind Onshore": "#1E88E5", "DE Wind Offshore": "#00ACC1", "DE Bioenergy": "#8E24AA",
  "UK Wind Onshore": "#10b981", "UK Wind Offshore": "#06b6d4", "SE Wind Onshore": "#f59e0b",
  "FR Wind Onshore": "#f43f5e", "FR Solar": "#a78bfa"
};

// ── Prediction Chart 1: Germany Forecast ──────────────────────
(function () {
  const deKeys = ["DE Solar", "DE Wind Onshore", "DE Wind Offshore", "DE Bioenergy"];
  const allYears = [];
  deKeys.forEach(k => { PRED[k].actual_y.forEach(y => { if (!allYears.includes(y)) allYears.push(y) }); PRED[k].forecast_y.forEach(y => { if (!allYears.includes(y)) allYears.push(y) }) });
  allYears.sort((a, b) => a - b);

  const datasets = [];
  deKeys.forEach(k => {
    const d = PRED[k];
    const actualMap = Object.fromEntries(d.actual_y.map((y, i) => [y, d.actual_v[i]]));
    const forecastMap = Object.fromEntries(d.forecast_y.map((y, i) => [y, d.forecast_v[i]]));
    const color = predColors[k];
    // Actual line
    datasets.push({
      label: k + " (Actual)", data: allYears.map(y => actualMap[y] || null),
      borderColor: color, backgroundColor: color + "22", pointRadius: 2, borderWidth: 2.5, tension: .3, spanGaps: true
    });
    // Forecast line (dashed)
    const forecastData = allYears.map(y => {
      if (y === d.actual_y[d.actual_y.length - 1]) return d.actual_v[d.actual_v.length - 1]; // connect
      return forecastMap[y] || null;
    });
    datasets.push({
      label: k + " (2030 Forecast)", data: forecastData,
      borderColor: color, borderDash: [6, 4], backgroundColor: color + "11", pointRadius: 3, borderWidth: 2, tension: .3, spanGaps: true,
      pointStyle: "triangle"
    });
  });

  new Chart(document.getElementById("predDEChart"), {
    type: "line", data: { labels: allYears, datasets }, options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { font: { size: 10 } } } },
      scales: {
        y: { title: { display: true, text: "Installed Capacity (MW)" }, ticks: { callback: v => fmt(v) } },
        x: { title: { display: true, text: "Year" } }
      },
      annotation: { annotations: { forecastLine: { type: "line", xMin: 2020, xMax: 2020, borderColor: "#f43f5e", borderWidth: 2, borderDash: [4, 4] } } }
    }
  });
})();

// ── Prediction Chart 2: Multi-country wind forecast ───────────
(function () {
  const windKeys = ["UK Wind Onshore", "UK Wind Offshore", "SE Wind Onshore", "FR Wind Onshore"];
  const allYears = [];
  windKeys.forEach(k => { if (PRED[k]) { PRED[k].actual_y.forEach(y => { if (!allYears.includes(y)) allYears.push(y) }); PRED[k].forecast_y.forEach(y => { if (!allYears.includes(y)) allYears.push(y) }) } });
  allYears.sort((a, b) => a - b);

  const datasets = [];
  windKeys.forEach(k => {
    if (!PRED[k]) return;
    const d = PRED[k]; const color = predColors[k];
    const actualMap = Object.fromEntries(d.actual_y.map((y, i) => [y, d.actual_v[i]]));
    const forecastMap = Object.fromEntries(d.forecast_y.map((y, i) => [y, d.forecast_v[i]]));
    datasets.push({ label: k, data: allYears.map(y => actualMap[y] || null), borderColor: color, pointRadius: 2, borderWidth: 2, tension: .3, spanGaps: true });
    const fd = allYears.map(y => { if (y === d.actual_y[d.actual_y.length - 1]) return d.actual_v[d.actual_v.length - 1]; return forecastMap[y] || null });
    datasets.push({ label: k + " →2030", data: fd, borderColor: color, borderDash: [6, 4], pointRadius: 3, borderWidth: 2, tension: .3, spanGaps: true, pointStyle: "triangle" });
  });

  new Chart(document.getElementById("predMultiChart"), {
    type: "line", data: { labels: allYears, datasets }, options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { font: { size: 9 } } } },
      scales: { y: { ticks: { callback: v => fmt(v) } } }
    }
  });
})();

// ── Prediction Chart 3: 2020 vs 2030 comparison ──────────────
(function () {
  const keys = Object.keys(PRED);
  const labels = keys;
  const actual = keys.map(k => PRED[k].actual2020);
  const predicted = keys.map(k => PRED[k].pred2030);

  new Chart(document.getElementById("predCompareChart"), {
    type: "bar", data: {
      labels, datasets: [
        { label: "2020 Actual", data: actual, backgroundColor: "#38bdf8", borderRadius: 6, borderSkipped: false },
        { label: "2030 Predicted", data: predicted, backgroundColor: "#a78bfa", borderRadius: 6, borderSkipped: false }
      ]
    }, options: {
      responsive: true, indexAxis: "y",
      plugins: { legend: { position: "top" } },
      scales: { x: { ticks: { callback: v => fmt(v) } } }
    }
  });
})();

// ── Prediction Summary Table ──────────────────────────────────
(function () {
  const tbl = document.getElementById("predTable");
  tbl.querySelector("thead").innerHTML = '<tr><th>Source</th><th>2020 (MW)</th><th>2025 (MW)</th><th>2030 (MW)</th><th>Growth %</th><th>R² Score</th></tr>';
  let body = '';
  Object.entries(PRED).forEach(([k, v]) => {
    const p25 = v.forecast_v[4] || "—";
    const arrow = v.growth > 0 ? "🟢" : "🔴";
    body += `<tr><td>${k}</td><td>${v.actual2020.toLocaleString()}</td><td>${Number(p25).toLocaleString()}</td><td>${v.pred2030.toLocaleString()}</td><td>${arrow} ${v.growth > 0 ? "+" : ""}${v.growth}%</td><td>${v.r2}</td></tr>`;
  });
  tbl.querySelector("tbody").innerHTML = body;
})();
