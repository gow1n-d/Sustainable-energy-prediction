"""
Renewable Energy Capacity Predictions → 2030
=============================================
Uses OPSD timeseries data (2000–2020) to predict installed capacity
growth through 2030 for key country+source combinations.

Models used:
  • Polynomial Regression (degree 2–3)
  • Linear Regression
  • Best fit selected per series via R² score

Outputs:
  • predictions.json  (consumed by the web dashboard)
  • prediction charts in charts/
"""

import os, json, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "opsd-renewable_power_plants-2020-08-25")
PRED_FILE = os.path.join(BASE, "predictions.json")
CHARTS = os.path.join(BASE, "charts")
os.makedirs(CHARTS, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 1. LOAD TIMESERIES
# ═══════════════════════════════════════════════════════════════
print("📥 Loading capacity timeseries ...")
ts = pd.read_csv(os.path.join(DATA_DIR, "renewable_capacity_timeseries.csv"))
ts["day"] = pd.to_datetime(ts["day"], errors="coerce")
ts = ts[ts["day"] >= "2000-01-01"].copy()
ts.sort_values("day", inplace=True)

# Get yearly snapshots (last value per year)
ts["year"] = ts["day"].dt.year
yearly = ts.groupby("year").last().reset_index()

# Define series to predict
SERIES = {
    "DE Solar":          "DE_solar_capacity",
    "DE Wind Onshore":   "DE_wind_onshore_capacity",
    "DE Wind Offshore":  "DE_wind_offshore_capacity",
    "DE Bioenergy":      "DE_bioenergy_capacity",
    "DK Solar":          "DK_solar_capacity",
    "DK Wind Onshore":   "DK_wind_onshore_capacity",
    "UK Solar":          "GB-UKM_solar_capacity",
    "UK Wind Onshore":   "GB-UKM_wind_onshore_capacity",
    "UK Wind Offshore":  "GB-UKM_wind_offshore_capacity",
    "CH Solar":          "CH_solar_capacity",
    "SE Wind Onshore":   "SE_wind_onshore_capacity",
    "FR Wind Onshore":   "FR_wind_onshore_capacity" if "FR_wind_onshore_capacity" in ts.columns else None,
    "FR Solar":          "FR_solar_capacity" if "FR_solar_capacity" in ts.columns else None,
}
SERIES = {k: v for k, v in SERIES.items() if v and v in yearly.columns}

PREDICT_TO = 2030

# ═══════════════════════════════════════════════════════════════
# 2. MODEL & PREDICT
# ═══════════════════════════════════════════════════════════════
print("\n🔮 Building prediction models ...")

predictions = {}

for label, col in SERIES.items():
    # Extract valid data
    data = yearly[["year", col]].dropna()
    data = data[data[col] > 0]

    if len(data) < 4:
        print(f"   ⚠️  {label}: Not enough data points ({len(data)}), skipping")
        continue

    X = data["year"].values.reshape(-1, 1)
    y = data[col].values

    # Try polynomial degrees 1 and 2 only (degree 3 overfits on plateau data)
    best_model = None
    best_r2 = -999
    best_degree = 1
    best_poly = None

    for degree in [1, 2]:
        poly = PolynomialFeatures(degree=degree)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)
        y_pred = model.predict(X_poly)
        r2 = r2_score(y, y_pred)

        # Penalise degree 2 slightly to prefer simpler models
        adj_r2 = r2 - (degree - 1) * 0.005

        if adj_r2 > best_r2:
            best_r2 = adj_r2
            best_model = model
            best_degree = degree
            best_poly = poly

    # Generate predictions 2000–2030
    future_years = np.arange(int(X.min()), PREDICT_TO + 1).reshape(-1, 1)
    X_future_poly = best_poly.transform(future_years)
    y_future = best_model.predict(X_future_poly)

    # Ensure predictions don't go negative
    y_future = np.maximum(y_future, 0)

    # Enforce monotonically non-decreasing forecasts
    # (installed capacity can only grow — plants aren't removed)
    last_actual_val = float(y[-1])
    last_actual_year = int(X[-1][0])
    for i, yr in enumerate(future_years.flatten()):
        if yr > last_actual_year:
            y_future[i] = max(y_future[i], last_actual_val)
            last_actual_val = max(last_actual_val, y_future[i])

    # Split into historical and forecast
    hist_mask = future_years.flatten() <= int(X.max())
    forecast_mask = future_years.flatten() > int(X.max())

    actual_years = data["year"].values.tolist()
    actual_values = [round(float(v), 2) for v in y]

    all_years = future_years.flatten().tolist()
    all_predicted = [round(float(v), 2) for v in y_future]

    forecast_years = future_years[forecast_mask].flatten().tolist()
    forecast_values = [round(float(v), 2) for v in y_future[forecast_mask]]

    # Latest actual and 2030 forecast
    latest_actual = round(float(y[-1]), 2)
    val_2030 = round(float(y_future[-1]), 2)
    growth_pct = round((val_2030 - latest_actual) / latest_actual * 100, 1) if latest_actual > 0 else 0

    predictions[label] = {
        "actual_years": actual_years,
        "actual_values": actual_values,
        "all_years": [int(y) for y in all_years],
        "all_predicted": all_predicted,
        "forecast_years": [int(y) for y in forecast_years],
        "forecast_values": forecast_values,
        "model_degree": best_degree,
        "r2_score": round(best_r2, 4),
        "latest_actual_MW": latest_actual,
        "predicted_2025_MW": round(float(y_future[all_years.index(2025)]), 2) if 2025 in all_years else None,
        "predicted_2030_MW": val_2030,
        "growth_2020_to_2030_pct": growth_pct
    }

    print(f"   ✅ {label}: degree={best_degree}, R²={best_r2:.4f}, "
          f"2020={latest_actual:,.0f} MW → 2030={val_2030:,.0f} MW ({growth_pct:+.1f}%)")

# ═══════════════════════════════════════════════════════════════
# 3. COMMISSIONING TREND PREDICTION
# ═══════════════════════════════════════════════════════════════
print("\n📈 Predicting yearly commissioning trend ...")

# Load plant-level data for commissioning trend
report = json.load(open(os.path.join(BASE, "analysis_report.json")))
yc = report["yearly_commissioning"]

# Use data from 2005–2018 (stable growth period, avoid 2019-2020 incomplete data)
yr_data = pd.DataFrame({"year": yc["years"], "mw": yc["total_MW"]})
yr_data = yr_data[(yr_data["year"] >= 2005) & (yr_data["year"] <= 2018)]

X_yr = yr_data["year"].values.reshape(-1, 1)
y_yr = yr_data["mw"].values

poly2 = PolynomialFeatures(degree=2)
X_yr_poly = poly2.fit_transform(X_yr)
model_yr = LinearRegression()
model_yr.fit(X_yr_poly, y_yr)

future_yr = np.arange(2005, 2031).reshape(-1, 1)
y_yr_pred = np.maximum(model_yr.predict(poly2.transform(future_yr)), 0)

predictions["commissioning_forecast"] = {
    "actual_years": yc["years"],
    "actual_MW": yc["total_MW"],
    "forecast_years": future_yr.flatten().tolist(),
    "forecast_MW": [round(float(v), 2) for v in y_yr_pred]
}

# ═══════════════════════════════════════════════════════════════
# 4. SAVE PREDICTIONS
# ═══════════════════════════════════════════════════════════════
with open(PRED_FILE, "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=2, default=str)
print(f"\n💾 Predictions saved → {PRED_FILE}")

# ═══════════════════════════════════════════════════════════════
# 5. GENERATE PREDICTION CHARTS
# ═══════════════════════════════════════════════════════════════
print("\n🎨 Generating prediction charts ...")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

sns.set_theme(style="darkgrid", palette="viridis")
plt.rcParams.update({"figure.dpi": 130, "savefig.bbox": "tight"})

# Chart: Combined DE prediction
fig, ax = plt.subplots(figsize=(14, 6))
de_series = {k: v for k, v in predictions.items() if k.startswith("DE ") and "forecast_years" in v}
colors_de = {"DE Solar": "#FFB300", "DE Wind Onshore": "#1E88E5", "DE Wind Offshore": "#00ACC1", "DE Bioenergy": "#8E24AA"}

for label, d in de_series.items():
    ax.plot(d["actual_years"], d["actual_values"], "o-", color=colors_de.get(label, "#666"),
            markersize=4, linewidth=2, label=f"{label} (actual)")
    ax.plot(d["forecast_years"], d["forecast_values"], "o--", color=colors_de.get(label, "#666"),
            markersize=4, linewidth=2, alpha=0.7, label=f"{label} (forecast)")

ax.axvline(x=2020, color="#f43f5e", linestyle=":", linewidth=1.5, alpha=0.7, label="Forecast starts")
ax.set_title("Germany — Renewable Capacity Forecast to 2030", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Installed Capacity (MW)")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(fontsize=8, ncol=2)
fig.savefig(os.path.join(CHARTS, "prediction_de_combined.png"))
plt.close(fig)

# Chart: UK + other predictions
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
other_series = {k: v for k, v in predictions.items()
                if not k.startswith("DE ") and k != "commissioning_forecast" and "forecast_years" in v}
other_list = list(other_series.items())[:4]
palette = ["#06b6d4", "#f59e0b", "#10b981", "#f43f5e"]

for idx, (ax, (label, d)) in enumerate(zip(axes.flat, other_list)):
    ax.plot(d["actual_years"], d["actual_values"], "o-", color=palette[idx], markersize=4, linewidth=2, label="Actual")
    ax.plot(d["forecast_years"], d["forecast_values"], "o--", color=palette[idx], markersize=4, linewidth=2, alpha=0.7, label="Forecast")
    ax.axvline(x=max(d["actual_years"]), color="#f43f5e", linestyle=":", linewidth=1, alpha=0.5)
    ax.set_title(f"{label} — Forecast to 2030", fontsize=11, fontweight="bold")
    ax.set_ylabel("MW")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(fontsize=8)

# Hide unused subplots
for i in range(len(other_list), 4):
    axes.flat[i].set_visible(False)

fig.suptitle("Renewable Capacity Forecasts — Other Countries", fontsize=14, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "prediction_other_countries.png"))
plt.close(fig)

# Chart: 2030 projections summary bar
fig, ax = plt.subplots(figsize=(12, 6))
pred_labels = [k for k in predictions if k != "commissioning_forecast" and "predicted_2030_MW" in predictions[k]]
pred_2030 = [predictions[k]["predicted_2030_MW"] for k in pred_labels]
pred_2020 = [predictions[k]["latest_actual_MW"] for k in pred_labels]

x = np.arange(len(pred_labels))
w = 0.35
ax.bar(x - w/2, pred_2020, w, label="2020 (Actual)", color="#38bdf8", edgecolor="white")
ax.bar(x + w/2, pred_2030, w, label="2030 (Predicted)", color="#a78bfa", edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels(pred_labels, rotation=35, ha="right", fontsize=9)
ax.set_title("2020 vs 2030 — Installed Capacity Comparison", fontsize=14, fontweight="bold")
ax.set_ylabel("Capacity (MW)")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend()
fig.savefig(os.path.join(CHARTS, "prediction_2020_vs_2030.png"))
plt.close(fig)

print("   3 prediction charts saved → charts/")
print("\n✅ Predictions complete!")
