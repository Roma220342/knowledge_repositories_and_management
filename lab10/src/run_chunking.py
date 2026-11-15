import sys, json, time, numpy as np; sys.path.insert(0, "src")
from common import *; from chunking import STRATEGIES; from index import Embedder, VectorStore
F = load_corpus(); G = {g["qid"]: g for g in load_gold()}
TEST10 = ["q02","q06","q10","q14","q18","q21","q25","q30","q33","q36"]
ALL = [g for g in G.values() if g['relevant']]
res = {}
for name, fn in STRATEGIES.items():
    chunks = fn(F); st = VectorStore(Embedder("char", 128)).build(chunks)
    rec, ctx, mrrs = [], [], []
    for q in TEST10:
        top = dedupe(st.search(G[q]["query"], 12))[:5]; rel = set(G[q]["relevant"]); cov = [c["covers"] for c, _ in top]
        rec.append(recall_at_k(cov, rel, 5)); mrrs.append(mrr(cov, rel)); ctx.append(np.mean([len(c["ctx_text"].split()) for c, _ in top]))
    ext = [dedupe(st.search(g['query'], 15))[:10] for g in ALL]
    e5 = [recall_at_k([c['covers'] for c,_ in t], set(g['relevant']), 5) for t, g in zip(ext, ALL)]
    en = [ndcg_at_k([c['covers'] for c,_ in t], set(g['relevant']), 10) for t, g in zip(ext, ALL)]
    res[name] = dict(recall5_all37=round(float(np.mean(e5)),3), ndcg10_all37=round(float(np.mean(en)),3), n_chunks=len(chunks), avg_chunk_words=round(float(np.mean([len(c["text"].split()) for c in chunks])), 1),
        recall5=round(float(np.mean(rec)), 3), mrr=round(float(np.mean(mrrs)), 3), ctx_words=round(float(np.mean(ctx)), 1), build_s=round(st.build_s, 3))
    print(name, res[name])
json.dump(res, open("results/chunking.json", "w"), indent=1, ensure_ascii=False)
