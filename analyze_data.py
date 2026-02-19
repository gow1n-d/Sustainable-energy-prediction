"""
Renewable Energy Analysis — Using REAL OPSD CSV Data
=====================================================
Uses the actual Open Power System Data (OPSD) renewable power plant CSVs.
Combines country-level plant data + capacity timeseries.
Produces: cleaned CSV, analysis JSON, charts, and web dashboard data.
"""

import os, json, warnings, sys
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "opsd-renewable_power_plants-2020-08-25")
CLEAN = os.path.join(BASE, "cleaned_data.csv")
REPORT = os.path.join(BASE, "analysis_report.json")
CHARTS = os.path.join(BASE, "charts")
os.makedirs(CHARTS, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 1. LOAD ALL COUNTRY CSVs (smaller ones to avoid memory issues)
# ═══════════════════════════════════════════════════════════════
print("📥 Loading OPSD renewable power plant data ...")

country_files = {
    "UK": "renewable_power_plants_UK.csv",
    "Switzerland": "renewable_power_plants_CH.csv",
    "Poland": "renewable_power_plants_PL.csv",
    "Sweden": "renewable_power_plants_SE.csv",
    "Czechia": "renewable_power_plants_CZ.csv",
}

# Common columns across all country files
COMMON_COLS = [
    "electrical_capacity", "energy_source_level_1",
    "energy_source_level_2", "energy_source_level_3",
    "technology", "commissioning_date"
]

frames = []
for country, fname in country_files.items():
    fpath = os.path.join(DATA_DIR, fname)
    try:
        df = pd.read_csv(fpath, low_memory=False)
        available = [c for c in COMMON_COLS if c in df.columns]
        sub = df[available].copy()
        sub["country"] = country
        frames.append(sub)
        print(f"   ✅ {country}: {len(df)} plants loaded")
    except Exception as e:
        print(f"   ⚠️  {country}: {e}")

# Also load DK and FR (moderate size)
for country, fname in [("Denmark", "renewable_power_plants_DK.csv"), ("France", "renewable_power_plants_FR.csv")]:
    fpath = os.path.join(DATA_DIR, fname)
    try:
        df = pd.read_csv(fpath, low_memory=False)
        available = [c for c in COMMON_COLS if c in df.columns]
        sub = df[available].copy()
        sub["country"] = country
        frames.append(sub)
        print(f"   ✅ {country}: {len(df)} plants loaded")
    except Exception as e:
        print(f"   ⚠️  {country}: skipped ({e})")

plants = pd.concat(frames, ignore_index=True)
print(f"\n   Combined dataset: {plants.shape[0]} rows × {plants.shape[1]} cols")

# Also load capacity timeseries
ts = pd.read_csv(os.path.join(DATA_DIR, "renewable_capacity_timeseries.csv"))
print(f"   Timeseries loaded: {ts.shape[0]} rows × {ts.shape[1]} cols")

# ═══════════════════════════════════════════════════════════════
# 2. CLEAN
# ═══════════════════════════════════════════════════════════════
print("\n🧹 Cleaning ...")

# --- Plants data ---
initial_missing = plants.isnull().sum().to_dict()
print(f"   Initial missing values:\n{json.dumps(initial_missing, indent=4)}")

# 2a. Standardise dates
plants["commissioning_date"] = pd.to_datetime(plants["commissioning_date"], errors="coerce")

# 2b. Clean electrical_capacity
plants["electrical_capacity"] = pd.to_numeric(plants["electrical_capacity"], errors="coerce")

# 2c. Fill missing energy source levels
plants["energy_source_level_2"] = plants["energy_source_level_2"].fillna("Unknown")
plants["energy_source_level_3"] = plants["energy_source_level_3"].fillna("Unknown")
plants["technology"] = plants["technology"].fillna("Unknown")

# 2d. Drop rows with no capacity at all
before = len(plants)
plants.dropna(subset=["electrical_capacity"], inplace=True)
print(f"   Dropped {before - len(plants)} rows with no capacity data")

# 2e. Fill missing commissioning dates with median per country
plants["commissioning_date"] = plants.groupby("country")["commissioning_date"].transform(
    lambda x: x.fillna(x.median())
)

# 2f. Standardise text
plants["energy_source_level_2"] = plants["energy_source_level_2"].str.strip().str.title()
plants["country"] = plants["country"].str.strip().str.title()

# Derive year
plants["year"] = plants["commissioning_date"].dt.year

remaining = plants.isnull().sum().sum()
print(f"   Remaining NaN: {remaining}")
print(f"   Clean dataset: {plants.shape}")

# --- Timeseries data ---
ts["day"] = pd.to_datetime(ts["day"], errors="coerce")
ts.dropna(subset=["day"], inplace=True)
# Filter to year 2000+ for meaningful data
ts = ts[ts["day"] >= "2000-01-01"].copy()
ts.sort_values("day", inplace=True)
print(f"   Timeseries (2000+): {ts.shape}")

# ═══════════════════════════════════════════════════════════════
# 3. PREPROCESS
# ═══════════════════════════════════════════════════════════════
print("\n⚙️  Preprocessing ...")

from sklearn.preprocessing import MinMaxScaler, LabelEncoder

# Scale electrical_capacity
scaler = MinMaxScaler()
plants["capacity_scaled"] = scaler.fit_transform(plants[["electrical_capacity"]])

# Label encode
le_source = LabelEncoder()
le_country = LabelEncoder()
le_tech = LabelEncoder()
plants["source_encoded"] = le_source.fit_transform(plants["energy_source_level_2"])
plants["country_encoded"] = le_country.fit_transform(plants["country"])
plants["tech_encoded"] = le_tech.fit_transform(plants["technology"])

# Save cleaned data
plants.to_csv(CLEAN, index=False)
print(f"   Cleaned CSV saved → {CLEAN}")

# ═══════════════════════════════════════════════════════════════
# 4. ANALYSIS
# ═══════════════════════════════════════════════════════════════
print("\n📊 Analysing ...")
report = {}

# 4a. Basic statistics
stats = plants[["electrical_capacity"]].describe().round(4)
report["basic_statistics"] = stats.to_dict()

# 4b. Plants per country
plants_per_country = plants["country"].value_counts().to_dict()
report["plants_per_country"] = plants_per_country

# 4c. Capacity by energy source
cap_by_source = plants.groupby("energy_source_level_2")["electrical_capacity"].sum().round(2).sort_values(ascending=False).to_dict()
report["total_capacity_by_source_MW"] = cap_by_source

# 4d. Capacity by country
cap_by_country = plants.groupby("country")["electrical_capacity"].sum().round(2).sort_values(ascending=False).to_dict()
report["total_capacity_by_country_MW"] = cap_by_country

# 4e. Plants by technology
tech_counts = plants["technology"].value_counts().head(10).to_dict()
report["plants_by_technology_top10"] = tech_counts

# 4f. Average capacity by source
avg_cap = plants.groupby("energy_source_level_2")["electrical_capacity"].mean().round(4).to_dict()
report["avg_capacity_by_source_MW"] = avg_cap

# 4g. Yearly commissioning trend (how many plants commissioned per year)
yearly_plants = plants.groupby("year").agg(
    count=("electrical_capacity", "count"),
    total_MW=("electrical_capacity", "sum")
).round(2)
yearly_plants = yearly_plants[(yearly_plants.index >= 1990) & (yearly_plants.index <= 2020)]
report["yearly_commissioning"] = {
    "years": yearly_plants.index.astype(int).tolist(),
    "plant_count": yearly_plants["count"].tolist(),
    "total_MW": yearly_plants["total_MW"].round(2).tolist()
}

# 4h. Capacity by source × country cross-tab
cross = pd.crosstab(
    plants["energy_source_level_2"], plants["country"],
    values=plants["electrical_capacity"], aggfunc="sum"
).round(2).fillna(0)
report["source_country_matrix"] = {
    "sources": cross.index.tolist(),
    "countries": cross.columns.tolist(),
    "data": cross.values.tolist()
}

# 4i. Timeseries: extract monthly snapshots for key countries
# Use first-of-month values
ts["year_ts"] = ts["day"].dt.year
ts["month_ts"] = ts["day"].dt.month
ts_monthly = ts.groupby([ts["day"].dt.to_period("M")]).last().reset_index(drop=True)

# Key capacity columns for visualization
key_ts_cols = {
    "DE_solar": "DE_solar_capacity",
    "DE_wind_onshore": "DE_wind_onshore_capacity",
    "DE_wind_offshore": "DE_wind_offshore_capacity",
    "DE_bioenergy": "DE_bioenergy_capacity",
    "DK_solar": "DK_solar_capacity",
    "DK_wind_onshore": "DK_wind_onshore_capacity",
    "UK_solar": "GB-UKM_solar_capacity" if "GB-UKM_solar_capacity" in ts.columns else None,
    "UK_wind_onshore": "GB-UKM_wind_onshore_capacity" if "GB-UKM_wind_onshore_capacity" in ts.columns else None,
    "CH_solar": "CH_solar_capacity",
    "SE_wind_onshore": "SE_wind_onshore_capacity",
}
key_ts_cols = {k: v for k, v in key_ts_cols.items() if v and v in ts.columns}

ts_trend = {}
for label, col in key_ts_cols.items():
    monthly = ts.set_index("day")[col].resample("Y").last().dropna()
    monthly = monthly[monthly > 0]
    ts_trend[label] = {
        "years": monthly.index.strftime("%Y").tolist(),
        "values": monthly.round(2).tolist()
    }
report["capacity_timeseries_yearly"] = ts_trend

# 4j. Country total from timeseries (latest values)
latest = ts.iloc[-1]
country_totals_ts = {}
for col in ts.columns:
    if col != "day" and "_capacity" in col:
        val = latest[col]
        if pd.notna(val) and val > 0:
            country_totals_ts[col.replace("_capacity", "")] = round(float(val), 2)
report["latest_installed_capacity_MW"] = dict(sorted(country_totals_ts.items(), key=lambda x: -x[1])[:20])

# 4k. Correlation for timeseries (DE sources)
de_cols = [c for c in ts.columns if c.startswith("DE_") and "_capacity" in c]
if de_cols:
    corr = ts[de_cols].corr().round(3)
    short_labels = [c.replace("DE_", "").replace("_capacity", "").replace("_", " ").title() for c in de_cols]
    report["de_correlation_matrix"] = {
        "labels": short_labels,
        "data": corr.values.tolist()
    }

# Save report
with open(REPORT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, default=str)
print(f"   Report JSON saved → {REPORT}")

# ═══════════════════════════════════════════════════════════════
# 5. CHARTS
# ═══════════════════════════════════════════════════════════════
print("\n🎨 Generating charts ...")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

sns.set_theme(style="darkgrid", palette="viridis")
plt.rcParams.update({"figure.dpi": 130, "savefig.bbox": "tight"})

SRC_COLORS = {
    "Solar": "#FFB300", "Wind": "#1E88E5", "Hydro": "#43A047",
    "Bioenergy": "#8E24AA", "Geothermal": "#E53935",
    "Marine": "#00ACC1", "Unknown": "#78909C"
}

# Chart 1: Capacity by source (bar)
fig, ax = plt.subplots(figsize=(10, 5))
sources = list(cap_by_source.keys())[:8]
vals = [cap_by_source[s] for s in sources]
colors = [SRC_COLORS.get(s, "#666") for s in sources]
ax.bar(sources, vals, color=colors, edgecolor="white", linewidth=0.8)
ax.set_title("Total Installed Capacity by Energy Source", fontsize=14, fontweight="bold")
ax.set_ylabel("Capacity (MW)")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.xticks(rotation=30, ha="right")
fig.savefig(os.path.join(CHARTS, "bar_capacity_by_source.png"))
plt.close(fig)

# Chart 2: Capacity by country (bar)
fig, ax = plt.subplots(figsize=(8, 5))
countries = list(cap_by_country.keys())
vals = list(cap_by_country.values())
ax.barh(countries, vals, color=sns.color_palette("mako", len(countries)), edgecolor="white")
ax.set_title("Total Installed Capacity by Country", fontsize=14, fontweight="bold")
ax.set_xlabel("Capacity (MW)")
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
fig.savefig(os.path.join(CHARTS, "bar_capacity_by_country.png"))
plt.close(fig)

# Chart 3: Yearly commissioning trend (line)
fig, ax1 = plt.subplots(figsize=(12, 5))
yrs = report["yearly_commissioning"]["years"]
counts = report["yearly_commissioning"]["plant_count"]
mw = report["yearly_commissioning"]["total_MW"]
ax1.bar(yrs, mw, color="#38bdf8", alpha=0.6, label="Total MW")
ax1.set_xlabel("Year")
ax1.set_ylabel("Capacity Added (MW)", color="#38bdf8")
ax2 = ax1.twinx()
ax2.plot(yrs, counts, color="#f59e0b", linewidth=2, marker="o", markersize=4, label="Plant Count")
ax2.set_ylabel("Number of Plants", color="#f59e0b")
ax1.set_title("Yearly Renewable Energy Commissioning Trend", fontsize=14, fontweight="bold")
fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88))
fig.savefig(os.path.join(CHARTS, "line_yearly_commissioning.png"))
plt.close(fig)

# Chart 4: DE capacity growth over time
fig, ax = plt.subplots(figsize=(12, 5))
de_trends = {k: v for k, v in ts_trend.items() if k.startswith("DE_")}
for label, d in de_trends.items():
    ax.plot(d["years"], d["values"], marker="o", markersize=4, linewidth=2, label=label.replace("DE_", "").replace("_", " ").title())
ax.set_title("Germany — Renewable Capacity Growth Over Time", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Installed Capacity (MW)")
ax.legend()
plt.xticks(rotation=45)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
fig.savefig(os.path.join(CHARTS, "line_de_capacity_growth.png"))
plt.close(fig)

# Chart 5: Source × Country heatmap
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(cross, annot=True, fmt=".0f", cmap="YlOrRd", linewidths=0.5, ax=ax,
            cbar_kws={"label": "Capacity (MW)"})
ax.set_title("Installed Capacity: Source × Country (MW)", fontsize=14, fontweight="bold")
fig.savefig(os.path.join(CHARTS, "heatmap_source_country.png"))
plt.close(fig)

# Chart 6: DE correlation heatmap
if "de_correlation_matrix" in report:
    fig, ax = plt.subplots(figsize=(8, 7))
    labels = report["de_correlation_matrix"]["labels"]
    data = np.array(report["de_correlation_matrix"]["data"])
    sns.heatmap(pd.DataFrame(data, index=labels, columns=labels),
                annot=True, fmt=".2f", cmap="coolwarm", center=0,
                linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Germany — Capacity Source Correlation", fontsize=14, fontweight="bold")
    fig.savefig(os.path.join(CHARTS, "heatmap_de_correlation.png"))
    plt.close(fig)

# Chart 7: Plants per country (pie)
fig, ax = plt.subplots(figsize=(7, 7))
ax.pie(plants_per_country.values(), labels=plants_per_country.keys(),
       autopct="%1.1f%%", startangle=140,
       colors=sns.color_palette("Set2", len(plants_per_country)),
       wedgeprops={"edgecolor": "white", "linewidth": 1.5})
ax.set_title("Distribution of Plants by Country", fontsize=14, fontweight="bold")
fig.savefig(os.path.join(CHARTS, "pie_plants_by_country.png"))
plt.close(fig)

# Chart 8: Technology distribution (top 8)
fig, ax = plt.subplots(figsize=(10, 5))
techs = list(tech_counts.keys())[:8]
tvals = [tech_counts[t] for t in techs]
ax.barh(techs, tvals, color=sns.color_palette("rocket", len(techs)), edgecolor="white")
ax.set_title("Top 10 Technologies by Number of Plants", fontsize=14, fontweight="bold")
ax.set_xlabel("Number of Plants")
ax.invert_yaxis()
fig.savefig(os.path.join(CHARTS, "bar_technology_distribution.png"))
plt.close(fig)

print("   8 charts saved → charts/")
print("\n✅ All done!")
