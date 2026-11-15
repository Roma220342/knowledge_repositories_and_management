"""Результат 4: Text-to-SPARQL з оцінкою.
Конвеєр: підказка зі схемою -> LLM (відповіді в t2s_data.py) -> парсер -> перевірка схеми -> виконання з LIMIT -> порівняння з еталоном.
Метрики (до/після покращення підказки): синтаксично коректні, «лише зі схеми», з правильним результатом.
Вихід: tests/t2s*.jsonl, docs/t2s_eval.md, results/r4_t2s.json, llm_log/llm_log.md, claims/claims.csv
"""
import json
import re
import time
from collections import Counter
from datetime import datetime

from rdflib import Graph, RDF, URIRef, OWL, RDFS
from rdflib.plugins.sparql import prepareQuery

from common import HR, PREFIX_HEADER, ROOT, add_claims, load_kb, local, md_table, term_str, write
from t2s_data import PROMPT_V1, PROMPT_V2_EXTRA, Q


def vocabulary(g):
    v = set()
    for t in g:
        for x in t:
            if isinstance(x, URIRef) and str(x).startswith(str(HR)):
                v.add(local(x))
    return v


def add_limit(q):
    if re.match(r"\s*(PREFIX[^\n]*\n)*\s*SELECT", q, re.I) and not re.search(r"\bLIMIT\s+\d+\s*$", q.strip(), re.I):
        return q.rstrip() + " LIMIT 100"
    return q


def normalize(res):
    if res.type == "ASK":
        return ("ASK", bool(res.askAnswer))
    return frozenset(tuple(term_str(b[v]) if v in b else "" for v in res.vars) for b in res.bindings)


def nrows(result):
    """ASK -> 1; SELECT -> кількість унікальних рядків."""
    return 1 if isinstance(result, tuple) else len(result)


def pipeline(g, vocab, text):
    out = {"syntax_ok": False, "schema_ok": False, "unknown": [], "executed": False, "error": "", "ms": None, "result": None}
    q = PREFIX_HEADER + text
    try:
        prepareQuery(q)
        out["syntax_ok"] = True
    except Exception as e:                                                # noqa
        out["error"] = f"syntax: {str(e)[:150]}"
        return out
    out["unknown"] = sorted(set(re.findall(r"\bhr:([A-Za-z0-9_]+)", text)) - vocab)
    out["schema_ok"] = not out["unknown"]
    if not out["schema_ok"]:
        out["error"] = "схема: невідомі терміни " + ", ".join(out["unknown"])
        return out
    try:
        t = time.perf_counter()
        out["result"] = normalize(g.query(add_limit(q)))
        out["ms"] = round((time.perf_counter() - t) * 1000, 1)
        out["executed"] = True
    except Exception as e:                                                # noqa
        out["error"] = f"виконання: {str(e)[:150]}"
    return out


def classify(item, gold_res, ans_text, res):
    if not res["syntax_ok"]:
        return "C — синтаксис/префікс"
    if not res["schema_ok"]:
        return "D — вигадані терміни (поза схемою)"
    if res["result"] == gold_res:
        return ""
    if re.search(r"reportsTo|LowPerformer", ans_text):
        return "A — залежність від виведення (немає reasoner)"
    if "subClassOf*" in item["gold"] and "subClassOf*" not in ans_text:
        return "B — ігнорування ієрархії класів"
    if re.search(r'(fullName|positionTitle|courseTitle)\s+"', ans_text):
        return "E — точні літерали (xsd:string ≠ простий рядок)"
    return "F — інша семантична відмінність (див. результат)"


def main():
    g = load_kb()
    vocab = vocabulary(g)
    classes = sorted(local(s) for s in g.subjects(RDF.type, OWL.Class) if str(s).startswith(str(HR)))
    props = sorted(local(s) for t in (OWL.ObjectProperty, OWL.DatatypeProperty) for s in g.subjects(RDF.type, t) if str(s).startswith(str(HR)))
    p1 = PROMPT_V1.format(classes=", ".join(classes), props=", ".join(props))
    p2 = p1 + PROMPT_V2_EXTRA

    # еталони
    for it in Q:
        r = pipeline(g, vocab, it["gold"])
        assert r["executed"], (it["id"], r["error"])
        it["_gold"] = r["result"]
        it["_gold_n"] = nrows(r["result"])

    results = []
    for it in Q:
        row = {"id": it["id"], "difficulty": it["difficulty"], "category": it["category"], "heldout": it["heldout"], "question": it["question"],
               "gold_rows": it["_gold_n"]}
        for ver in ("v1", "v2"):
            text = it[ver]
            if text is None:
                row[ver] = None
                continue
            res = pipeline(g, vocab, text)
            correct = res["executed"] and res["result"] == it["_gold"]
            row[ver] = {"text": text, "syntax_ok": res["syntax_ok"], "schema_ok": res["schema_ok"], "executed": res["executed"], "correct": bool(correct),
                        "rows": nrows(res["result"]) if res["result"] is not None else None,
                        "error": res["error"], "ms": res["ms"], "class": "" if correct else classify(it, it["_gold"], text, res)}
        results.append(row)

    def metric(rows, ver):
        rs = [r[ver] for r in rows if r.get(ver)]
        n = len(rs)
        pct = lambda k: f"{sum(1 for r in rs if r[k])}/{n} ({100 * sum(1 for r in rs if r[k]) / n:.0f} %)" if n else "—"
        return {"n": n, "syntax": pct("syntax_ok"), "schema": pct("schema_ok"), "correct": pct("correct")}

    main_rows = [r for r in results if not r["heldout"]]
    held_rows = [r for r in results if r["heldout"]]
    m = [{"Набір / версія": f"основний (n={len(main_rows)}), v1", **{k: v for k, v in metric(main_rows, "v1").items() if k != "n"}},
         {"Набір / версія": f"основний (n={len(main_rows)}), v2", **{k: v for k, v in metric(main_rows, "v2").items() if k != "n"}},
         {"Набір / версія": f"контрольний (n={len(held_rows)}), v2", **{k: v for k, v in metric(held_rows, "v2").items() if k != "n"}}]
    m = [{"Набір / версія": x["Набір / версія"], "синтаксично коректні": x["syntax"], "лише зі схеми": x["schema"], "правильний результат": x["correct"]} for x in m]
    print(md_table(m))

    errs = [{"питання": r["id"], "категорія": r["category"], "клас помилки": r["v1"]["class"],
             "що пішло не так": r["v1"]["error"] or f"рядків {r['v1']['rows']} проти еталонних {r['gold_rows']}",
             "виправлення у v2": "так" if r["v2"] and r["v2"]["correct"] else "ні"}
            for r in main_rows if not r["v1"]["correct"]]
    cls = Counter(e["клас помилки"] for e in errs)

    detail = [{"id": r["id"], "складність": r["difficulty"], "v1": "✓" if r["v1"] and r["v1"]["correct"] else "✗",
               "v2": ("✓" if r["v2"]["correct"] else "✗") if r["v2"] else "—", "рядків (еталон)": r["gold_rows"]} for r in results]

    # файли тестів
    (ROOT / "tests").mkdir(exist_ok=True)
    def dump(path, items):
        write(path, "\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n")
    dump(ROOT / "tests" / "t2s.jsonl", [{"id": it["id"], "difficulty": it["difficulty"], "category": it["category"], "question": it["question"],
                                         "gold_sparql": it["gold"], "gold_rows": it["_gold_n"]} for it in Q if not it["heldout"]])
    dump(ROOT / "tests" / "t2s_heldout.jsonl", [{"id": it["id"], "difficulty": it["difficulty"], "question": it["question"],
                                                 "gold_sparql": it["gold"], "gold_rows": it["_gold_n"]} for it in Q if it["heldout"]])
    dump(ROOT / "tests" / "t2s_llm_v1.jsonl", [{"id": it["id"], "sparql": it["v1"]} for it in Q if it["v1"]])
    dump(ROOT / "tests" / "t2s_llm_v2.jsonl", [{"id": it["id"], "sparql": it["v2"]} for it in Q])

    (ROOT / "results").mkdir(exist_ok=True)
    json.dump({"metrics": m, "errors": errs, "results": results, "prompt_v1": p1, "prompt_v2": p2},
              open(ROOT / "results" / "r4_t2s.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)

    md = ["# Оцінка text-to-SPARQL\n",
          "## Конвеєр\nпідказка зі схемою (класи й властивості з графа) → LLM → парсер (rdflib `prepareQuery`; префікси додає конвеєр) → перевірка схеми "
          "(усі `hr:`-терміни існують у графі) → виконання на rdflib з `LIMIT 100` → порівняння множини рядків з еталоном.\n",
          "## Метрики\n" + md_table(m),
          "\n## Результати по питаннях\n" + md_table(detail),
          "\n## Аналіз помилок v1 (клас → кількість)\n" + md_table([{"клас": k, "кількість": v} for k, v in cls.most_common()]),
          md_table(errs),
          "\n## Підказки\n### v1\n```\n" + p1 + "\n```\n### v2 (покращена)\n```\n" + p2 + "\n```\n",
          "\n## Обмеження оцінки\nВідповіді LLM згенеровано в чат-сесії, а не через API; еталони складено автором, тому v2 (складена після аналізу помилок v1) — "
          "оптимістична оцінка. Для чесної перевірки слугує контрольний набір H01–H04, не використаний при покращенні підказки.\n"]
    write(ROOT / "docs" / "t2s_eval.md", "\n".join(md))

    # протокол LLM-експерт
    n_ok = sum(1 for r in results if r["v2"] and r["v2"]["correct"])
    write(ROOT / "llm_log" / "llm_log.md",
          f"# Журнал взаємодії з LLM (ЛР 8)\n\n- Дата: {datetime.now():%Y-%m-%d}\n- Модель і версія: Claude (чат-сесія Claude Code)\n"
          "- Параметри: temperature — за замовчуванням, seed не підтримується\n- Версії підказки: v1 (схема), v2 (схема + 5 правил)\n"
          "- Сирий вихід: tests/t2s_llm_v1.jsonl, tests/t2s_llm_v2.jsonl\n"
          f"- Рішення людини: v2 підтверджено {n_ok} із {len(results)} відповідей; відхилені й причини — docs/t2s_eval.md\n\n## Підказка v1\n```\n{p1}\n```\n\n## Підказка v2\n```\n{p2}\n```\n")
    add_claims([[f"t2s-{r['id']}", f"{r['question']} → {r['v2']['text']}", "факт", "LLM (чат-сесія, підказка v2)", "V4",
                 "verified" if r["v2"]["correct"] else "rejected",
                 "результат збігається з еталоном" if r["v2"]["correct"] else (r["v2"]["error"] or "результат відрізняється від еталона")] for r in results])
    print("docs/t2s_eval.md, tests/*.jsonl, llm_log/, claims/ записано")


if __name__ == "__main__":
    main()
