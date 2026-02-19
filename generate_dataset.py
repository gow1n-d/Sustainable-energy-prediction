"""
Generate a realistic Renewable Energy Dataset with intentional
data quality issues (missing values, inconsistent dates, mixed formats)
so the cleaning/preprocessing pipeline has real work to do.
"""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

# Configuration
OUTPUT = os.path.join(os.path.dirname(__file__), "renewable_energy_data.csv")
START_DATE = datetime(2022, 1, 1)
NUM_MONTHS = 36  # 3 years

SOURCES = ["Solar", "Wind", "Hydro", "Biomass", "Geothermal"]
REGIONS = ["North", "South", "East", "West", "Central"]

# Date format pool (intentional inconsistency)
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%d-%b-%Y",
    "%Y/%m/%d",
]

def seasonal_factor(month, source):
    """Return a seasonal multiplier for realism."""
    if source == "Solar":
        return [0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.4, 1.3, 1.1, 0.8, 0.6, 0.5][month - 1]
    elif source == "Wind":
        return [1.3, 1.2, 1.1, 0.9, 0.7, 0.6, 0.5, 0.6, 0.8, 1.0, 1.2, 1.4][month - 1]
    elif source == "Hydro":
        return [0.7, 0.8, 1.0, 1.2, 1.1, 1.3, 1.4, 1.3, 1.1, 0.9, 0.8, 0.7][month - 1]
    elif source == "Biomass":
        return [0.9, 0.9, 1.0, 1.0, 1.1, 1.1, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9][month - 1]
    else:  # Geothermal – steady
        return 1.0

BASE_GENERATION = {
    "Solar":       {"North": 120, "South": 200, "East": 150, "West": 170, "Central": 160},
    "Wind":        {"North": 180, "South": 110, "East": 140, "West": 160, "Central": 130},
    "Hydro":       {"North": 90,  "South": 70,  "East": 100, "West": 80,  "Central": 110},
    "Biomass":     {"North": 50,  "South": 60,  "East": 55,  "West": 45,  "Central": 65},
    "Geothermal":  {"North": 30,  "South": 40,  "East": 35,  "West": 25,  "Central": 45},
}

BASE_COST = {"Solar": 45, "Wind": 38, "Hydro": 30, "Biomass": 55, "Geothermal": 50}
EFFICIENCY = {"Solar": 22, "Wind": 35, "Hydro": 90, "Biomass": 25, "Geothermal": 15}
CO2_SAVED_PER_MWH = {"Solar": 0.5, "Wind": 0.6, "Hydro": 0.4, "Biomass": 0.3, "Geothermal": 0.35}
CAPACITY = {"Solar": 500, "Wind": 600, "Hydro": 300, "Biomass": 200, "Geothermal": 150}

rows = []
header = [
    "Date", "Region", "Energy_Source", "Energy_Generated_MWh",
    "Energy_Consumed_MWh", "Cost_USD", "Efficiency_Percent",
    "CO2_Saved_Tons", "Installed_Capacity_MW", "Revenue_USD",
    "Storage_MWh", "Grid_Feed_MWh"
]

for m in range(NUM_MONTHS):
    current = START_DATE + timedelta(days=m * 30)
    month = current.month
    year_offset = (current.year - 2022)           # gradual growth factor

    for region in REGIONS:
        for source in SOURCES:
            # Pick a random date format to create inconsistency
            fmt = random.choice(DATE_FORMATS)
            date_str = current.strftime(fmt)

            sf = seasonal_factor(month, source)
            base = BASE_GENERATION[source][region]
            growth = 1 + 0.05 * year_offset       # 5 % annual growth

            gen = round(base * sf * growth * random.uniform(0.85, 1.15), 2)
            consumed = round(gen * random.uniform(0.6, 0.95), 2)
            cost = round(BASE_COST[source] * gen / 100 * random.uniform(0.9, 1.1), 2)
            eff = round(EFFICIENCY[source] * random.uniform(0.9, 1.1), 2)
            co2 = round(gen * CO2_SAVED_PER_MWH[source] * random.uniform(0.9, 1.1), 2)
            cap = CAPACITY[source] + year_offset * 20
            revenue = round(gen * random.uniform(40, 70), 2)
            storage = round(gen * random.uniform(0.05, 0.20), 2)
            grid_feed = round(gen - consumed, 2)

            row = [
                date_str, region, source, gen, consumed, cost,
                eff, co2, cap, revenue, storage, grid_feed
            ]

            # Introduce ~5 % missing values at random positions (skip Date/Region/Source)
            for i in range(3, len(row)):
                if random.random() < 0.05:
                    row[i] = ""

            rows.append(row)

# Shuffle a little for realism
random.shuffle(rows)

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"✅ Dataset written to {OUTPUT}")
print(f"   Rows : {len(rows)}")
print(f"   Cols : {len(header)}")
