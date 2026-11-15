"""Перевірка узгодженості: те саме питання різними шляхами (семантичний шар vs «ручний» SQL/OLAP-запит vs pandas) дає однаковий результат."""
import os, sys, json, pandas as pd
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, R + "/etl"); sys.path.insert(0, R + "/semantic")
from load import DB, connect; from metrics import sql_for, validate, METRICS
eng, con = connect(DB, ro=True); q = lambda s: pd.read_sql_query(s, con); out = []
def cmp(name, a, b, tol=1e-6): out.append(dict(check=name, path_a=a if not isinstance(a, float) else round(a, 4), path_b=b if not isinstance(b, float) else round(b, 4), ok=abs(float(a) - float(b)) <= max(tol, 1e-4)))
# 1. cost_per_hour 2025: метрика vs Q6 (ручний SQL) vs pandas
a = q(sql_for("cost_per_hour", by=["class"], where={"year": 2025})).set_index("class").cost_per_hour; b = pd.read_csv(R + "/results/olap/q06_slice.csv").set_index("class_label").cost_per_hour
for k in a.index: cmp(f"cost_per_hour, {k}, 2025: метрика vs Q6", float(a[k]), float(b[k]), 0.006)
# 2. training_hours за класами: метрика vs Q2 (ROLLUP, рівень класів)
a = q(sql_for("training_hours", by=["class"])).set_index("class").training_hours; q2 = pd.read_csv(R + "/results/olap/q02_rollup_taxonomy.csv"); b = q2[q2.subclass_label.isna() & q2.class_label.notna()].set_index("class_label").hours
for k in a.index: cmp(f"training_hours, {k}: метрика vs Q2 (ROLLUP)", float(a[k]), float(b[k]), 0.1)
# 3. загальна вартість: метрика vs Q1 (загальний підсумок) vs pandas
tot = float(q(sql_for("training_cost")).iloc[0, 0]); q1 = pd.read_csv(R + "/results/olap/q01_rollup_time.csv"); cmp("training_cost, всього: метрика vs Q1", tot, float(q1[q1.year.isna()].cost_eur.iloc[0]), 0.01)
cmp("training_cost, всього: метрика vs pandas", tot, float(pd.read_csv(R + "/data/fact_training.csv").cost_eur.sum()), 0.01)
# 4. hours_per_learner = training_hours / active_learners (через складову метрику)
h = float(q(sql_for("training_hours")).iloc[0, 0]); n = float(q(sql_for("active_learners")).iloc[0, 0]); cmp("hours_per_learner = training_hours / active_learners", float(q(sql_for("hours_per_learner")).iloc[0, 0]), h / n, 0.001)
# 5. вимірна згортка: сума cost по підкласах = cost по класах
a = float(q(sql_for("training_cost", by=["subclass"])).training_cost.sum()); b = float(q(sql_for("training_cost", by=["class"])).training_cost.sum()); cmp("сума за підкласами = сума за класами", a, b, 0.05)
res = dict(metadata_errors=validate(), checks=out, all_ok=all(c["ok"] for c in out) and not validate(), n_metrics=len(METRICS))
json.dump(res, open(R + "/results/semantic_consistency.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(res, ensure_ascii=False)[:900]); print("all_ok", res["all_ok"])
