"""ELT: CSV -> СУБД (DuckDB, якщо доступний, інакше SQLite) -> перевірки якості -> Parquet (якщо є pyarrow). Запуск: python etl/generate.py && python etl/load.py"""
import os, sys, json, sqlite3, hashlib, datetime as dt
import pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{ROOT}/data"; DB = f"{ROOT}/data/hub.db"
VERSION = "1.0.0"
TABLES = ["dim_date", "dim_position", "dim_employee", "dim_competence", "dim_course", "fact_training", "fact_perf_quarter"]
def connect(path=DB, ro=False):
    try:
        import duckdb; return "duckdb", duckdb.connect(path.replace(".db", ".duckdb"), read_only=ro)
    except ImportError:
        return "sqlite", sqlite3.connect(f"file:{path}?mode=ro" if ro else path, uri=True)
def load():
    if os.path.exists(DB): os.remove(DB)
    eng, con = connect()
    ddl = open(f"{ROOT}/sql/ddl.sql", encoding="utf-8").read()
    if eng == "sqlite": con.executescript(ddl)
    else: con.execute(ddl)
    counts = {}
    for t in TABLES:
        df = pd.read_csv(f"{D}/{t}.csv"); counts[t] = len(df)
        if eng == "sqlite": df.to_sql(t, con, if_exists="append", index=False)
        else: con.execute(f"INSERT INTO {t} SELECT * FROM df")
    con.commit() if eng == "sqlite" else None
    return eng, con, counts
CHECKS = [  # (id, опис, SQL, очікувано 0 порушень)
 ("DQ1", "not null: ключі й міри факту навчання", "SELECT COUNT(*) FROM fact_training WHERE date_key IS NULL OR employee_sk IS NULL OR course_key IS NULL OR competence_key IS NULL OR hours IS NULL OR cost_eur IS NULL"),
 ("DQ2", "діапазон: 0 < hours <= 80 і cost_eur >= 0", "SELECT COUNT(*) FROM fact_training WHERE hours <= 0 OR hours > 80 OR cost_eur < 0"),
 ("DQ3", "діапазон: оцінки 0..10, score_after >= score_before, satisfaction 1..5; для незавершених оцінок немає", "SELECT COUNT(*) FROM fact_training WHERE (completed = 1 AND (score_before NOT BETWEEN 0 AND 10 OR score_after NOT BETWEEN 0 AND 10 OR score_after < score_before OR satisfaction NOT BETWEEN 1 AND 5)) OR (completed = 0 AND (score_before IS NOT NULL OR score_after IS NOT NULL))"),
 ("DQ4", "унікальність: training_key та (employee_sk, date_key, course_key) на рівні зерна", "SELECT (SELECT COUNT(*) - COUNT(DISTINCT training_key) FROM fact_training) + (SELECT COUNT(*) FROM (SELECT employee_sk, date_key, course_key FROM fact_training GROUP BY 1,2,3 HAVING COUNT(*) > 1))"),
 ("DQ5", "узгодженість SCD2: інтервали версій співробітника не перетинаються; одна поточна версія", "SELECT (SELECT COUNT(*) FROM dim_employee a JOIN dim_employee b ON a.employee_id = b.employee_id AND a.employee_sk < b.employee_sk AND a.valid_from <= b.valid_to AND b.valid_from <= a.valid_to) + (SELECT COUNT(*) FROM (SELECT employee_id FROM dim_employee WHERE is_current = 1 GROUP BY 1 HAVING COUNT(*) <> 1))"),
 ("DQ6", "подія потрапила у валідний інтервал версії співробітника (SCD2)", "SELECT COUNT(*) FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_employee e ON e.employee_sk = f.employee_sk WHERE d.full_date < e.valid_from OR d.full_date > e.valid_to"),
 ("DQ7", "узгодженість: competence_key факту = competence_key курсу", "SELECT COUNT(*) FROM fact_training f JOIN dim_course c ON c.course_key = f.course_key WHERE c.competence_key <> f.competence_key"),
 ("DQ8", "діапазон: productivity_score 0..10, headcount = 1, bonus_eur >= 0", "SELECT COUNT(*) FROM fact_perf_quarter WHERE productivity_score NOT BETWEEN 0 AND 10 OR headcount <> 1 OR bonus_eur < 0")]
ORPHANS = [("fact_training.date_key", "SELECT COUNT(*) FROM fact_training f LEFT JOIN dim_date d ON d.date_key = f.date_key WHERE d.date_key IS NULL"),
 ("fact_training.employee_sk", "SELECT COUNT(*) FROM fact_training f LEFT JOIN dim_employee d ON d.employee_sk = f.employee_sk WHERE d.employee_sk IS NULL"),
 ("fact_training.course_key", "SELECT COUNT(*) FROM fact_training f LEFT JOIN dim_course d ON d.course_key = f.course_key WHERE d.course_key IS NULL"),
 ("fact_training.competence_key", "SELECT COUNT(*) FROM fact_training f LEFT JOIN dim_competence d ON d.competence_key = f.competence_key WHERE d.competence_key IS NULL"),
 ("fact_perf_quarter.date_key", "SELECT COUNT(*) FROM fact_perf_quarter f LEFT JOIN dim_date d ON d.date_key = f.date_key WHERE d.date_key IS NULL"),
 ("fact_perf_quarter.employee_sk", "SELECT COUNT(*) FROM fact_perf_quarter f LEFT JOIN dim_employee d ON d.employee_sk = f.employee_sk WHERE d.employee_sk IS NULL"),
 ("dim_employee.position_key", "SELECT COUNT(*) FROM dim_employee f LEFT JOIN dim_position d ON d.position_key = f.position_key WHERE d.position_key IS NULL"),
 ("dim_course.competence_key", "SELECT COUNT(*) FROM dim_course f LEFT JOIN dim_competence d ON d.competence_key = f.competence_key WHERE d.competence_key IS NULL")]
def run_checks(con):
    q = lambda s: con.execute(s).fetchone()[0]
    return [dict(id=i, check=d, violations=q(s), ok=q(s) == 0) for i, d, s in CHECKS], [dict(fk=n, orphans=q(s), ok=q(s) == 0) for n, s in ORPHANS]
def to_parquet():
    try: import pyarrow  # noqa
    except ImportError: return "pyarrow недоступний: збережено лише CSV (data/*.csv)"
    for t in TABLES: pd.read_csv(f"{D}/{t}.csv").to_parquet(f"{D}/{t}.parquet", index=False)
    return "збережено data/*.parquet"
if __name__ == "__main__":
    eng, con, counts = load(); dq, orph = run_checks(con); pq = to_parquet()
    sha = {t: hashlib.sha256(open(f"{D}/{t}.csv", "rb").read()).hexdigest()[:12] for t in TABLES}
    rep = dict(version=VERSION, engine=eng, loaded=dt.datetime.now().strftime("%Y-%m-%d %H:%M"), counts=counts, dq=dq, orphans=orph, storage=pq, sha256_12=sha, generator=json.load(open(f"{D}/generator_manifest.json")))
    json.dump(rep, open(f"{ROOT}/results/dq_report.json", "w"), indent=1, ensure_ascii=False); open(f"{D}/VERSION", "w").write(f"{VERSION}\nseed=42\n" + "\n".join(f"{t} {h}" for t, h in sha.items()) + "\n")
    print(eng, counts); [print(x) for x in dq]; [print(x) for x in orph]; print(pq)
