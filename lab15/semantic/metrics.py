"""Семантичний шар: sql_for(metric, by=[...], where={...}) -> SQL; метрика та вимір описані один раз (metrics.yml)."""
import os, yaml
HERE = os.path.dirname(os.path.abspath(__file__)); CFG = yaml.safe_load(open(f"{HERE}/metrics.yml", encoding="utf-8"))
METRICS = {m["name"]: m for m in CFG["metrics"]}; DIMS = CFG["dimensions"]
JOIN = {"date": "JOIN dim_date d ON d.date_key = f.date_key", "competence": "JOIN dim_competence c ON c.competence_key = f.competence_key",
        "employee": "JOIN dim_employee e ON e.employee_sk = f.employee_sk", "position": "JOIN dim_position p ON p.position_key = e.position_key", "course": "JOIN dim_course co ON co.course_key = f.course_key"}
ORDER = ["date", "competence", "employee", "position", "course"]
REQUIRED_FIELDS = ["name", "definition", "formula", "unit", "owner", "sources", "constraints", "status", "reviewed_on"]
def lit(v): return str(v) if isinstance(v, (int, float)) else "'" + str(v).replace("'", "''") + "'"
def sql_for(metric, by=(), where=None, order_desc=True, limit=None):
    if metric not in METRICS: raise KeyError(f"невідома метрика: {metric}")
    m = METRICS[metric]; where = where or {}; need = set(m.get("joins", []))
    for d in list(by) + list(where):
        if d not in DIMS: raise KeyError(f"невідомий вимір: {d}")
        need |= set(DIMS[d]["joins"])
    if "position" in need: need.add("employee")
    joins = " ".join(JOIN[j] for j in ORDER if j in need); sel = ", ".join(f"{DIMS[d]['expr']} AS {d}" for d in by)
    conds = " AND ".join(f"{DIMS[d]['expr']} = {lit(v)}" if not isinstance(v, (list, tuple)) else f"{DIMS[d]['expr']} IN ({', '.join(lit(x) for x in v)})" for d, v in where.items())
    sql = f"SELECT {sel + ', ' if sel else ''}ROUND({m['expr']}, 4) AS {metric} FROM fact_training f {joins}" + (f" WHERE {conds}" if conds else "")
    if by: sql += " GROUP BY " + ", ".join(DIMS[d]["expr"] for d in by) + f" ORDER BY {metric} {'DESC' if order_desc else 'ASC'}, " + ", ".join(by)
    return sql + (f" LIMIT {int(limit)}" if limit else "")
def validate():
    errs = []
    for m in CFG["metrics"]:
        for k in REQUIRED_FIELDS + ["expr", "additivity", "synonyms"]:
            if not m.get(k): errs.append((m["name"], k))
    return errs
