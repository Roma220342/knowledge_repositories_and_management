"""Результат 4–5: оцінювання RAG. Метрики: faithfulness, context recall, citation accuracy, abstention rate; p50/p95 затримка, токени, вартість.
Запуск: python eval/run_rag_eval.py --k 3 --tag base"""
import sys, os, json, re, argparse, numpy as np; sys.path.insert(0, "src")
from rag import RAG, ID_RE, ABSTAIN, REFUSE, ExtractiveLLM
from common import stems, load_corpus
ap = argparse.ArgumentParser(); ap.add_argument("--k", type=int, default=3); ap.add_argument("--tag", default="base"); ap.add_argument("--rho", type=float, default=0.6); ap.add_argument("--repeats", type=int, default=5); ap.add_argument("--store", default=None)
a = ap.parse_args()
PRICE_IN, PRICE_OUT = 3.0, 15.0      # ПРИПУЩЕННЯ: умовний тариф, USD за 1 млн токенів (вхід/вихід); власний генератор в офлайні нічого не коштує
T = [json.loads(l) for l in open("eval/rag_eval.jsonl", encoding="utf-8")]; OV = [json.loads(l) for l in open("eval/overlay.jsonl", encoding="utf-8")]
LOG = f"logs/rag_eval_{a.tag}.jsonl"; open(LOG, "w").close()
if a.store:   # ЛР 14: сховище = версія store_*.jsonl (X01–X04 уже всередині; X05 — лише для тестів безпеки)
    sys.path.insert(0, "quality"); from store import load_store; ST = load_store(a.store); X5 = [o for o in OV if o["id"] == "X05-p01"]
    base = RAG(frags=ST, k=a.k, log_path=LOG, llm=ExtractiveLLM(a.rho)); over = RAG(frags=ST, extra=X5, k=a.k, log_path=LOG, thr=base.thr, llm=ExtractiveLLM(a.rho))
else:
    base = RAG(k=a.k, log_path=LOG, llm=ExtractiveLLM(a.rho)); over = RAG(extra=OV, k=a.k, log_path=LOG, thr=base.thr, llm=ExtractiveLLM(a.rho))
def faithfulness(ans, ctx):
    """Незалежний «суддя» (лексичний): частка речень відповіді, у яких ≥70 % змістових основ слів є в цитованих фрагментах."""
    ans = re.sub(r"Джерела суперечать:\s*|\s*Новішим є \[[^\]]+\]\.?|\(\d{4}-\d{2}-\d{2}\)", " ", ans)     # службові фрази шаблону конфлікту не є твердженнями
    byid = {c["id"]: c["text"] for c in ctx}; sents = [s for s in re.split(r"(?<=[.!?])\s+(?!\[)", ans) if s.strip()]; ok = []
    for s in sents:
        cited = ID_RE.findall(s); ss = set(stems(ID_RE.sub("", s)))
        if not ss: continue
        pool = set(stems(" ".join(byid.get(c, "") for c in cited)))
        ok.append(1.0 if cited and len(ss & pool) / len(ss) >= 0.7 else 0.0)
    return float(np.mean(ok)) if ok else 0.0
rows = []
for t in T:
    r = over if t["overlay"] else base
    x = r.ask(t["question"], role=t["role"], k=a.k)                      # основний запуск (пишеться в журнал)
    lat = [x["latency_ms"]]; lg = r.log_path; r.log_path = None
    for _ in range(a.repeats - 1): lat.append(r.ask(t["question"], role=t["role"], k=a.k)["latency_ms"])
    r.log_path = lg
    ans = x["answer"]; ctx = x["context"]; ids = [c["id"] for c in ctx]; abst = ans.startswith("Не знаю"); refused = ans.startswith("Запит відхилено")
    row = dict(id=t["id"], cat=t["cat"], question=t["question"], relevant=t["relevant"], answer=ans, sources=ids, cited=x["cited"], abstained=abst, refused=refused,
               quarantined=x["quarantined"], lat_ms=float(np.median(lat)), ptok=x["prompt_tokens"], ctok=x["completion_tokens"], citations_valid=x["citations_valid"])
    rel = set(t["relevant"])
    if t["cat"] in ("answer", "conflict"):
        row["ctx_recall"] = len(rel & set(ids)) / len(rel)
        row["cit_acc"] = (len(set(x["cited"]) & rel) / len(set(x["cited"]))) if x["cited"] else 0.0
        row["faith"] = None if abst else faithfulness(ans, ctx)
        row["hit"] = bool(set(x["cited"]) & rel) and not abst
    if t["cat"] == "conflict": row["flagged"] = ("суперечать" in ans) and rel <= set(x["cited"])
    if t["cat"] == "no_answer": row["abstain_ok"] = abst
    if t["cat"] == "injection": row["safe"] = not any(f.lower() in ans.lower() for f in t["forbidden"])
    rows.append(row)
def m(cat, key, skip_none=True):
    v = [r[key] for r in rows if r["cat"] in cat and key in r and (r[key] is not None or not skip_none)]; return round(float(np.mean(v)), 3) if v else None
lat = [r["lat_ms"] for r in rows]; PT = np.mean([r["ptok"] for r in rows]); CT = np.mean([r["ctok"] for r in rows])
summ = dict(k=a.k, rho=a.rho, n=len(rows), thr=round(base.thr, 4),
    faithfulness=m(("answer", "conflict"), "faith"), context_recall=m(("answer", "conflict"), "ctx_recall"), citation_accuracy=m(("answer", "conflict"), "cit_acc"),
    abstention_rate_noanswer=m(("no_answer",), "abstain_ok"), false_abstain_answerable=round(float(np.mean([r["abstained"] for r in rows if r["cat"] == "answer"])), 3),
    answer_hit_rate=m(("answer",), "hit"), conflict_flagged=m(("conflict",), "flagged"), injection_safe=m(("injection",), "safe"),
    invalid_citations=int(sum(not r["citations_valid"] for r in rows)),
    p50_ms=round(float(np.percentile(lat, 50)), 2), p95_ms=round(float(np.percentile(lat, 95)), 2), prompt_tokens=round(float(PT), 1), completion_tokens=round(float(CT), 1),
    cost_per_query_usd=round(float((PT * PRICE_IN + CT * PRICE_OUT) / 1e6), 6), price_assumption=[PRICE_IN, PRICE_OUT])
json.dump(dict(summary=summ, rows=rows), open(f"results/rag_eval_{a.tag}.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(summ, ensure_ascii=False))
