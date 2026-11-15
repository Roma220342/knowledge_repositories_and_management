"""Результат 2: SPARQL-запити до CQ -> results/r2_sparql.json, docs/sparql_results.md
- виконує queries/*.rq (rdflib); для q12 — federated SERVICE до Wikidata (із запасним прямим HTTP-запитом);
- порівняння часу q11a (повільний) і q11b (оптимізований) на rdflib і Oxigraph на графі з +400 співробітниками;
- ручна перевірка q02, q04, q07, q09, q10 незалежним перебором триплетів без SPARQL.
"""
import json
import re
import statistics
import time
from collections import Counter, defaultdict

from rdflib import Graph, RDF, URIRef

from common import HR, LNK, ROOT, SEED, bind, enrich, load_kb, local, md_table, term_str, write

try:
    from r1_build_kb import ox, to_oxi
except Exception:        # noqa
    ox = None

UA = {"User-Agent": "LabKnowledgeHub/1.0 (student lab work; SPARQL federated test)", "Accept": "application/sparql-results+json"}


def header(text):
    meta = {}
    for line in text.splitlines():
        m = re.match(r"#\s*(\w+):\s*(.*)", line)
        if m:
            meta[m.group(1)] = m.group(2)
        elif not line.startswith("#"):
            break
    return meta


def body(text):
    return "\n".join(l for l in text.splitlines() if not l.startswith("#")).strip()


def run(g, q):
    res = g.query(q)
    if res.type == "ASK":
        return [{"answer": str(res.askAnswer).lower()}]
    if res.type == "CONSTRUCT":
        return [{"triples": len(res.graph)}]
    return [{str(v): term_str(b[v]) if v in b else "" for v in res.vars} for b in res.bindings]


def timed(fn, reps=5):
    out, ts = None, []
    for _ in range(reps):
        t = time.perf_counter(); out = fn(); ts.append((time.perf_counter() - t) * 1000)
    return out, round(statistics.median(ts), 1)


def federated(g, text):
    """q12: спершу rdflib SERVICE; при помилці — той самий запит до ендпоінта напряму (JOIN у Python)."""
    targets = [str(r[0]) for r in g.query(
        "PREFIX lnk: <http://example.org/lnk#> SELECT DISTINCT ?t WHERE { ?l lnk:target ?t ; lnk:status \"verified\" }")]
    if not targets:
        return None, "немає верифікованих зв'язків (спершу запустіть r5_links.py)", None
    values = " ".join(f"<{t}>" for t in targets)
    q = text.replace("{{VALUES}}", values)
    try:
        rows, ms = timed(lambda: run(g, q), reps=1)
        return rows, "rdflib SERVICE → query.wikidata.org", ms
    except Exception as e:                                   # noqa
        err = f"{type(e).__name__}: {str(e)[:120]}"
    import requests
    ep = ("SELECT ?wd ?label ?desc WHERE { VALUES ?wd { %s } ?wd rdfs:label ?label . FILTER(LANG(?label)='en') "
          "OPTIONAL { ?wd <https://schema.org/description> ?desc . FILTER(LANG(?desc)='en') } }" % values)
    ep = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" + ep
    t = time.perf_counter()
    r = requests.get("https://query.wikidata.org/sparql", params={"query": ep, "format": "json"}, headers=UA, timeout=60)
    r.raise_for_status()
    remote = {b["wd"]["value"]: (b["label"]["value"], b.get("desc", {}).get("value", "")) for b in r.json()["results"]["bindings"]}
    rows = []
    for l, term, rel, conf, tgt in g.query(
            "PREFIX lnk: <http://example.org/lnk#> SELECT ?l ?term ?rel ?conf ?t WHERE { ?l a lnk:Link ; lnk:source ?term ; "
            "lnk:relation ?rel ; lnk:confidence ?conf ; lnk:target ?t ; lnk:status \"verified\" }"):
        if str(tgt) in remote:
            rows.append({"term": local(term), "relation": local(rel), "conf": str(conf), "label": remote[str(tgt)][0], "desc": remote[str(tgt)][1]})
    rows.sort(key=lambda r: -float(r["conf"]))
    return rows, f"запасний режим (SERVICE через rdflib не спрацював: {err}); запит до ендпоінта виконано напряму, JOIN у Python", round((time.perf_counter() - t) * 1000, 1)


def manual_checks(g, res):
    n = lambda x: str(x)
    out = []
    # q02
    mgr = g.value(HR.petro, HR.directManager)
    exp = n(g.value(mgr, HR.fullName))
    out.append(("q02", exp, res["q02"][0]["manager"], exp == res["q02"][0]["manager"]))
    # q04: кількість індивідів із типом Employee / Manager / Recruiter
    emp = {s for c in (HR.Employee, HR.Manager, HR.Recruiter) for s in g.subjects(RDF.type, c)}
    out.append(("q04", str(len(emp)), res["q04"][0]["n"], str(len(emp)) == res["q04"][0]["n"]))
    # q07: транзитивне замикання directManager
    boss = defaultdict(set)
    for e, m in g.subject_objects(HR.directManager):
        boss[e].add(m)
    def chain(e, seen=None):
        seen = seen or set()
        for m in boss.get(e, ()):
            if m not in seen:
                seen.add(m); chain(m, seen)
        return seen
    subs = sorted(local(e) for e in set(boss) if HR.olena in chain(e))
    got = sorted(r["e"] for r in res["q07"])
    out.append(("q07", f"{len(subs)} підлеглих", f"{len(got)} підлеглих", subs == got))
    # q09
    exp9 = sorted((n(g.value(e, HR.fullName)), int(g.value(e, HR.tenureMonths))) for e in g.subjects(HR.tenureMonths, None)
                  if int(g.value(e, HR.tenureMonths)) > 60)
    got9 = sorted((r["name"], int(r["months"])) for r in res["q09"])
    out.append(("q09", f"{len(exp9)} осіб", f"{len(got9)} осіб", exp9 == got9))
    # q10
    cnt = Counter(g.value(m, HR.fullName) for e, m in g.subject_objects(HR.directManager))
    exp10 = sorted((n(k), v) for k, v in cnt.items() if v >= 5)
    got10 = sorted((r["manager"], int(r["team"])) for r in res["q10"])
    out.append(("q10", "; ".join(f"{a} {b}" for a, b in exp10), "; ".join(f"{a} {b}" for a, b in got10), exp10 == got10))
    return [{"запит": q[0], "очікування (перебір триплетів)": q[1], "результат SPARQL": q[2], "збіг": "так" if q[3] else "НІ"} for q in out]


def main():
    g = load_kb(links=True)
    files = sorted((ROOT / "queries").glob("q*.rq"))
    results, report = {}, {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        meta, q = header(text), body(text)
        qid = meta["id"]
        if qid == "q12":
            rows, mode, ms = federated(g, q)
            report[qid] = {"meta": meta, "rows": rows or [], "ms": ms, "mode": mode}
            results[qid] = rows or []
            print(f"{qid}: {len(rows or [])} рядків ({mode[:60]})")
            continue
        if qid in ("q11a", "q11b"):
            continue
        rows, ms = timed(lambda: run(g, q))
        results[qid] = rows
        report[qid] = {"meta": meta, "rows": rows, "ms": ms, "query": q}
        print(f"{qid}: {len(rows)} рядків, {ms} мс")

    # --- оптимізація q11a/q11b
    big = Graph(); bind(big)
    for t in load_kb(links=False):
        big.add(t)
    enrich(big, n=120, start=1000, seed=SEED)
    qa, qb = (body((ROOT / "queries" / f"{x}.rq").read_text(encoding="utf-8")) for x in ("q11a", "q11b"))
    ra, ta = timed(lambda: run(big, qa), reps=1)
    rb, tb = timed(lambda: run(big, qb), reps=2)
    opt = [{"Варіант": "q11a (FILTER наприкінці, декартів добуток)", "Рушій": "rdflib", "Час, мс": ta, "Пар": ra[0]["pairs"]},
           {"Варіант": "q11b (селективні підзапити першими)", "Рушій": "rdflib", "Час, мс": tb, "Пар": rb[0]["pairs"]}]
    if ox:
        store = ox.Store()
        for s, p, o in big:
            store.add(ox.Quad(to_oxi(s), to_oxi(p), to_oxi(o)))
        def oxi(q):
            return int(next(iter(store.query(q)))["pairs"].value)
        for name, q in (("q11a (FILTER наприкінці, декартів добуток)", qa), ("q11b (селективні підзапити першими)", qb)):
            v, t = timed(lambda: oxi(q), reps=2)
            opt.append({"Варіант": name, "Рушій": "Oxigraph", "Час, мс": t, "Пар": v})
    same = len({r["Пар"] for r in opt if r["Рушій"] == "rdflib"}) == 1
    print("оптимізація:", opt, "| однакова відповідь:", same)

    # --- ручна перевірка
    man = manual_checks(g, results)
    print("ручна перевірка:", man)

    (ROOT / "results").mkdir(exist_ok=True)
    with open(ROOT / "results" / "r2_sparql.json", "w", encoding="utf-8") as fh:
        json.dump({"queries": report, "optimization": opt, "same_answer": same, "triples_big": len(big), "manual": man},
                  fh, ensure_ascii=False, indent=2, default=str)

    md = ["# Результати SPARQL-запитів\n"]
    summary = [{"id": k, "конструкція": v["meta"].get("construct"), "рядків": len(v["rows"]), "мс": v["ms"]} for k, v in report.items()]
    md.append(md_table(summary))
    for k, v in report.items():
        md.append(f"\n## {k}\n**CQ:** {v['meta'].get('CQ')}  \n**Конструкція:** {v['meta'].get('construct')}  \n**Інтерпретація:** {v['meta'].get('interp')}\n")
        if "query" in v:
            md.append(f"```sparql\n{v['query']}\n```\n")
        if v.get("mode"):
            md.append(f"Режим: {v['mode']}\n")
        md.append(f"Час: {v['ms']} мс; рядків: {len(v['rows'])}\n\n" + md_table(v["rows"][:10]))
    md.append("\n## Оптимізація q11a → q11b\n" + md_table(opt) + f"\nВідповіді однакові: **{same}**\n")
    md.append("\n## Ручна перевірка\n" + md_table(man))
    write(ROOT / "docs" / "sparql_results.md", "\n".join(md))
    print("docs/sparql_results.md записано")


if __name__ == "__main__":
    main()
