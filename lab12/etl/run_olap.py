"""Виконує sql/olap/*.sql; зберігає results/olap/*.csv і results/olap_summary.json (кількість рядків, час)."""
import os, sys, glob, json, time, sqlite3, pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); from load import DB, ROOT, connect
eng, con = connect(DB, ro=True); os.makedirs(f"{ROOT}/results/olap", exist_ok=True); out = {}
for f in sorted(glob.glob(f"{ROOT}/sql/olap/q*.sql")):
    name = os.path.basename(f)[:-4]; stm = [s.strip() for s in "\n".join(l for l in open(f, encoding="utf-8") if not l.startswith("--")).split(";\n") if s.strip().rstrip(";")]
    stm = [s.rstrip(";") for s in stm]; res = []
    for i, s in enumerate(stm):
        t0 = time.perf_counter(); df = pd.read_sql_query(s, con); ms = (time.perf_counter() - t0) * 1000
        suffix = f"_{'abc'[i]}" if len(stm) > 1 else ""; df.to_csv(f"{ROOT}/results/olap/{name}{suffix}.csv", index=False)
        res.append(dict(part=suffix.strip("_") or "-", rows=len(df), ms=round(ms, 2)))
    out[name] = res; print(name, res)
json.dump(out, open(f"{ROOT}/results/olap_summary.json", "w"), indent=1)
