import json
p = json.load(open("predictions.json"))
for k, v in p.items():
    if k != "commissioning_forecast":
        a = v.get("latest_actual_MW", "")
        f = v.get("predicted_2030_MW", "")
        g = v.get("growth_2020_to_2030_pct", "")
        r = v.get("r2_score", "")
        d = v.get("model_degree", "")
        print(f"{k}: {a} MW -> 2030={f} MW ({g}%) R2={r} deg={d}")
