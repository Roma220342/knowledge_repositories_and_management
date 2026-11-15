import sys, json, time, numpy as np; sys.path.insert(0, "src")
from common import *; from hybrid import Hybrid
F = load_corpus(); G = load_gold(); H = Hybrid(F)
CFG = {"BM25": lambda q: H.bm25_rank(q, 30), "Dense (LSA-word)": lambda q: H.dense_rank(q, 30),
       "Hybrid (RRF k=60)": lambda q: H.hybrid_rank(q, 30), "Hybrid + rerank": lambda q: H.hybrid_rerank(q, 10)}
H2 = Hybrid(F, "char"); CFG["Dense (LSA-char)"] = lambda q: H2.dense_rank(q, 30)
ans = [g for g in G if g["relevant"]]; noans = [g for g in G if not g["relevant"]]
res, per_q = {}, {}
for name, fn in CFG.items():
    R5, R10, M, N, lat = [], [], [], [], []; bytype = {}
    for g in ans:
        ts = []
        for _ in range(5): t = time.perf_counter(); out = fn(g["query"]); ts.append((time.perf_counter() - t) * 1000)
        lat.append(np.median(ts)); cov = [{i} for i, _ in out]; rel = set(g["relevant"])
        r5, r10, m, n = recall_at_k(cov, rel, 5), recall_at_k(cov, rel, 10), mrr(cov, rel), ndcg_at_k(cov, rel, 10)
        R5.append(r5); R10.append(r10); M.append(m); N.append(n); bytype.setdefault(g["type"], []).append(m)
        per_q.setdefault(g["qid"], {})[name] = dict(mrr=m, r5=r5, top=[i for i, _ in out[:5]])
    res[name] = dict(recall5=round(float(np.mean(R5)), 3), recall10=round(float(np.mean(R10)), 3), mrr=round(float(np.mean(M)), 3),
        ndcg10=round(float(np.mean(N)), 3), lat_ms=round(float(np.mean(lat)), 2), lat_p95_ms=round(float(np.percentile(lat, 95)), 2),
        mrr_by_type={k: round(float(np.mean(v)), 3) for k, v in bytype.items()},
        recall5_ci95=[round(float(x), 3) for x in np.percentile([np.mean(np.random.default_rng(SEED + b).choice(R5, len(R5))) for b in range(1000)], [2.5, 97.5])])
    print(name, {k: v for k, v in res[name].items() if k != "mrr_by_type"})
# ---- запити без відповіді: найвищий бал топ-1 reranker-а (для порогу відсікання)
top_ans = [H.hybrid_rerank(g["query"], 1)[0][1] for g in ans]; top_no = [H.hybrid_rerank(g["query"], 1)[0][1] for g in noans]
thr = float(np.median(top_ans) * 0.5)
res["_no_answer"] = dict(top1_answerable_mean=round(float(np.mean(top_ans)), 3), top1_noanswer_mean=round(float(np.mean(top_no)), 3),
    threshold=round(thr, 3), rejected_noans=int(sum(s < thr for s in top_no)), n_noans=len(noans), kept_answerable=int(sum(s >= thr for s in top_ans)), n_ans=len(ans))
print(res["_no_answer"])
# ---- приклади виграшу/програшу гібриду
diff = []
for q, d in per_q.items():
    best_single = max(d["BM25"]["mrr"], d["Dense (LSA-word)"]["mrr"]); diff.append((d["Hybrid (RRF k=60)"]["mrr"] - best_single, q))
diff.sort()
ex_lose = [q for s, q in diff if s < 0][:1]
# виграш: гібрид кращий за ОБИДВА окремі методи (за MRR), далі — кращий за найгірший з двох із максимальним відривом
gq = {g["qid"]: g for g in G}
win = sorted([(d["Hybrid (RRF k=60)"]["mrr"] - max(d["BM25"]["mrr"], d["Dense (LSA-word)"]["mrr"]), d["Hybrid (RRF k=60)"]["mrr"] - min(d["BM25"]["mrr"], d["Dense (LSA-word)"]["mrr"]), q) for q, d in per_q.items()], reverse=True)
ex_win = [q for a, b, q in win if (a > 0 or b > 0)][:3]
res["_examples"] = dict(win=ex_win, lose=ex_lose, detail={q: dict(query=gq[q]["query"], relevant=gq[q]["relevant"], per_method=per_q[q]) for q in ex_win + ex_lose})
json.dump(dict(summary=res, per_q=per_q), open("results/eval.json", "w"), indent=1, ensure_ascii=False)
print("wins", ex_win, "lose", ex_lose, [(round(a,2),round(b,2),q) for a,b,q in win[:6]], diff[:3])
