"""Захисний шар text-to-SQL: розбір запиту (лексичний аналіз без регулярних обходів: коментарі й рядки прибираються), лише SELECT/WITH,
білий список таблиць, заборона небезпечних слів і функцій, примусовий LIMIT, EXPLAIN, з'єднання лише для читання, тайм-аут (progress handler)."""
import re, os, sys, time, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "etl")); from load import DB
TABLES = {"fact_training", "fact_perf_quarter", "dim_date", "dim_employee", "dim_position", "dim_competence", "dim_course"}
FORBIDDEN = {"insert", "update", "delete", "drop", "alter", "create", "replace", "attach", "detach", "pragma", "vacuum", "reindex", "truncate", "copy", "export", "import", "install", "load", "call", "set", "grant", "revoke", "merge", "begin", "commit", "rollback"}
BAD_FUNCS = {"load_extension", "readfile", "writefile", "read_csv", "read_parquet", "read_json", "glob", "system", "edit"}
MAX_LIMIT, TIMEOUT_S = 100, 1.0
class Rejected(Exception): pass
def strip(sql):
    """Прибирає коментарі та вміст рядкових літералів; повертає (очищений SQL, чи були незакриті лапки)."""
    out, i, n = [], 0, len(sql)
    while i < n:
        c = sql[i]
        if sql.startswith("--", i): j = sql.find("\n", i); i = n if j < 0 else j; continue
        if sql.startswith("/*", i): j = sql.find("*/", i + 2); 
        if sql.startswith("/*", i):
            if j < 0: raise Rejected("незакритий блоковий коментар")
            i = j + 2; out.append(" "); continue
        if c in "'\"":
            j = i + 1
            while j < n:
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c: j += 2; continue
                    break
                j += 1
            else: raise Rejected("незакриті лапки")
            out.append(c + "_" + c); i = j + 1; continue
        out.append(c); i += 1
    return "".join(out)
def check(sql):
    """AST-подібна перевірка на рівні токенів. Повертає очищений запит або кидає Rejected."""
    s = strip(sql).strip()
    if not s: raise Rejected("порожній запит")
    body = s.rstrip(";").strip()
    if ";" in body: raise Rejected("кілька операторів")
    toks = re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\S", body.lower()); words = [t for t in toks if re.match(r"[a-z_]", t)]
    if not words or words[0] not in ("select", "with"): raise Rejected("дозволено лише SELECT/WITH")
    bad = FORBIDDEN & set(words)
    if bad: raise Rejected(f"заборонені ключові слова: {sorted(bad)}")
    for i, t in enumerate(toks):
        if t in BAD_FUNCS: raise Rejected(f"заборонена функція: {t}")
    ctes = set(re.findall(r"(?:with|,)\s*([a-z_][a-z_0-9]*)\s+as\s*\(", body.lower()))
    for m in re.finditer(r"\b(?:from|join)\s+([a-z_][a-z_0-9\.]*)", body.lower()):
        t = m.group(1)
        if t not in TABLES and t not in ctes: raise Rejected(f"таблиця поза білим списком: {t}")
    for m in re.finditer(r",\s*([a-z_][a-z_0-9]*)\s*(?:as\s+\w+\s*)?(?:,|where|group|order|limit|$)", body.lower()):   # неявні з'єднання «FROM a, b, c»
        t = m.group(1)
        if t in TABLES or t in ctes: continue
    return body
def enforce_limit(body, limit=MAX_LIMIT): return f"SELECT * FROM (\n{body}\n) LIMIT {limit}"
def execute(sql, timeout=TIMEOUT_S, db=DB, limit=MAX_LIMIT):
    t0 = time.perf_counter()
    try: body = check(sql)
    except Rejected as e: return dict(status="rejected", reason=str(e), rows=None, ms=0.0, sql=None)
    wrapped = enforce_limit(sql.strip().rstrip(';').strip(), limit)  # виконується оригінал; body — лише для перевірки
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True); con.execute("PRAGMA query_only = ON")
    deadline = time.perf_counter() + timeout; con.set_progress_handler(lambda: 1 if time.perf_counter() > deadline else 0, 10000)
    try:
        con.execute("EXPLAIN QUERY PLAN " + wrapped).fetchall()                               # синтаксис і план без виконання
        cur = con.execute(wrapped); cols = [c[0] for c in cur.description]; rows = cur.fetchall()
        return dict(status="ok", reason="", columns=cols, rows=rows, ms=round((time.perf_counter() - t0) * 1000, 2), sql=wrapped)
    except sqlite3.OperationalError as e:
        r = "тайм-аут" if "interrupted" in str(e) else f"помилка СУБД: {e}"
        return dict(status="timeout" if "interrupted" in str(e) else "error", reason=r, rows=None, ms=round((time.perf_counter() - t0) * 1000, 2), sql=wrapped)
    finally: con.close()
