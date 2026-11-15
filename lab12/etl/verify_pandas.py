"""Незалежна перевірка двох OLAP-результатів засобами pandas (без SQL): Q1 (ROLLUP за часом) і Q6 (slice, вартість години за класом 2025)."""
import pandas as pd, json, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{R}/data"
ft = pd.read_csv(f"{D}/fact_training.csv"); dd = pd.read_csv(f"{D}/dim_date.csv"); dc = pd.read_csv(f"{D}/dim_competence.csv")
x = ft.merge(dd, on="date_key").merge(dc, on="competence_key"); out = {}
q1 = pd.read_csv(f"{R}/results/olap/q01_rollup_time.csv"); g = x.groupby(["year", "quarter"])[["hours", "cost_eur"]].sum().round(2)
leaf = q1.dropna(subset=["year", "quarter"]).set_index(["year", "quarter"])
ok1 = all(abs(leaf.loc[(float(y), float(q)), "hours"] - r.hours) < 0.1 and abs(leaf.loc[(float(y), float(q)), "cost_eur"] - r.cost_eur) < 0.01 for (y, q), r in g.iterrows())
tot = q1[q1.year.isna()].iloc[0]; ok1 = ok1 and abs(tot.hours - x.hours.sum()) < 0.1 and abs(tot.cost_eur - x.cost_eur.sum()) < 0.01 and int(tot.events) == len(x)
out["Q1"] = dict(ok=bool(ok1), pandas_total_hours=round(x.hours.sum(), 1), pandas_total_cost=round(x.cost_eur.sum(), 2), sql_total_hours=float(tot.hours), sql_total_cost=float(tot.cost_eur), cells_checked=len(g))
q6 = pd.read_csv(f"{R}/results/olap/q06_slice.csv").set_index("class_label"); s = x[x.year == 2025].groupby("class_label")[["hours", "cost_eur"]].sum(); s["cph"] = (s.cost_eur / s.hours).round(2)
ok6 = all(abs(q6.loc[k, "cost_per_hour"] - v.cph) < 0.006 and abs(q6.loc[k, "hours"] - v.hours) < 0.1 for k, v in s.iterrows())
out["Q6"] = dict(ok=bool(ok6), pandas={k: float(v.cph) for k, v in s.iterrows()}, sql={k: float(v.cost_per_hour) for k, v in q6.iterrows()})
json.dump(out, open(f"{R}/results/verify_pandas.json", "w"), indent=1, ensure_ascii=False); print(out)
