# Лабораторна 12 — OLAP-куб на основі таксономії (HR-навчання)
Seed: 42. Рушій: SQLite (DuckDB/Parquet використовуються автоматично, якщо встановлені).
Команди:
    python3 etl/generate.py && python3 etl/load.py
    python3 etl/run_olap.py && python3 etl/verify_pandas.py
    python3 semantic/check_consistency.py
    python3 t2sql/run_tests.py
Структура: sql/ddl.sql, sql/olap/*.sql, semantic/, t2sql/, tests/t2sql.jsonl, dashboard/index.html, docs/, results/, llm_log/, claims/.
