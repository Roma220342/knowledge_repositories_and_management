import json, os, sys, sqlite3
R = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, R); sys.path.insert(0, R + "/../etl")
from guard import execute, check, Rejected
from translate import translate, build_prompt
from load import DB
def gold(sql):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); r = con.execute(sql).fetchall(); con.close(); return r
def norm(rows): return sorted([tuple(round(x, 2) if isinstance(x, float) else x for x in r) for r in rows], key=repr)
out = []; ok_n = nl_n = safe_n = un_n = 0; tok = 0
for line in open(R + "/../tests/t2sql.jsonl", encoding="utf-8"):
    t = json.loads(line)
    if t["kind"] == "nl":
        nl_n += 1; tr = translate(t["question"]); tok += len(build_prompt(t["question"])) // 3
        if not tr["ok"]: out.append(dict(id=t["id"], correct=False, reason=tr["reason"])); continue
        res = execute(tr["sql"]); g = gold(t["gold_sql"])
        c = res["status"] == "ok" and norm(res["rows"]) == norm(g)
        ok_n += c; out.append(dict(id=t["id"], q=t["question"], correct=c, status=res["status"], generated=tr["sql"][:400] if not c else "", got=res["rows"][:3] if res["rows"] and not c else None, gold=g[:3] if not c else None))
    else:
        un_n += 1; q = t["question"]
        res = execute(q) if q.split()[0].upper() in ("SELECT", "WITH", "DELETE", "PRAGMA", "DROP") else dict(status="rejected", reason="не SQL")
        if q.startswith("Видали"):
            tr = translate(q); res = dict(status="rejected", reason="NL: метрику не розпізнано") if not tr["ok"] else execute(tr["sql"])
        safe = (res["status"] != "ok") if t["expect"] == "not_executed" else res["status"] == "ok"
        safe_n += safe; out.append(dict(id=t["id"], safe=safe, status=res["status"], reason=res.get("reason", ""), ms=res.get("ms")))
rep = dict(nl=nl_n, correct=ok_n, correct_share=round(ok_n / nl_n, 3), unsafe=un_n, safe=safe_n, safe_share=round(safe_n / un_n, 3), est_prompt_tokens=tok, est_cost_usd=round(tok * 3 / 1e6, 4), items=out)
json.dump(rep, open(R + "/../results/t2sql_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v for k, v in rep.items() if k != "items"})
for o in out:
    if not o.get("correct", o.get("safe")): print(o)
