import sys, json, time, numpy as np; sys.path.insert(0, "src")
from common import *; from chunking import hierarchical; from index import Embedder, VectorStore
F = load_corpus(); G = {g["qid"]: g for g in load_gold()}
CH = hierarchical(F)
for c in CH: c["covers"] = {c["cid"]}           # строга оцінка на рівні фрагмента
TEST20 = ["q01","q03","q05","q07","q09","q11","q13","q15","q16","q17","q19","q21","q23","q25","q27","q29","q31","q33","q35","q37"]
EN = [("turnover rate formula", ["D04-p03"]), ("probation period length", ["D05-p07"]), ("annual leave days", ["D12-p01"])]
def evaluate(st, qs, reps=5):
    rec, mr, lat = [], [], []
    for q, rel in qs:
        rel = set(rel); ts = []
        for _ in range(reps):
            t = time.perf_counter(); top = st.search(q, 10); ts.append((time.perf_counter() - t) * 1000)
        lat.append(np.median(ts)); cov = [c["covers"] for c, _ in top]
        rec.append(recall_at_k(cov, rel, 5)); mr.append(mrr(cov, rel))
    return dict(recall5=round(float(np.mean(rec)), 3), mrr=round(float(np.mean(mr)), 3), lat_mean_ms=round(float(np.mean(lat)), 3), lat_p95_ms=round(float(np.percentile(lat, 95)), 3))
qs20 = [(G[q]["query"], G[q]["relevant"]) for q in TEST20]
res = {"models": {}, "hnsw_sweep": [], "english": {}}
for kind in ["word", "char"]:
    st = VectorStore(Embedder(kind, 128), M=32, efC=80, efS=64).build(CH)
    r = evaluate(st, qs20); r.update(build_s=round(st.build_s, 3), dim=int(st.V.shape[1]), n=len(CH), mem_kb=round(st.V.nbytes / 1024, 1), M=32, efC=80, efS=64)
    res["models"][f"lsa-{kind}"] = r; print(kind, r)
    res["english"][f"lsa-{kind}"] = evaluate(st, EN)
for M, efS in [(16, 16), (16, 64), (32, 16), (32, 64), (32, 128)]:
    st = VectorStore(Embedder("char", 128), M=M, efC=80, efS=efS).build(CH)
    r = evaluate(st, qs20); r.update(M=M, efSearch=efS, build_s=round(st.build_s, 3)); res["hnsw_sweep"].append(r)
# ---- upsert / delete на 5 документах
st = VectorStore(Embedder("char", 128), M=32, efC=80, efS=64).build(CH)
TITLE = {f['doc_id']: f['title'] for f in F}
DOCS = ["D03", "D07", "D12", "D15", "D20"]; log = []
for d in DOCS:
    target = next(c for c in CH if c["doc_id"] == d and c["cid"].endswith("p05"))
    new = dict(target); marker = f"Додаткове положення: {TITLE[d].lower()} переглядається щороку."
    new["text"] = marker + " Зміни набувають чинності з наступного кварталу."   # фрагмент перезаписано редакцією
    new["ctx_text"] = new["text"]
    t = time.perf_counter(); st.upsert(new); up_ms = (time.perf_counter() - t) * 1000
    top = st.search(marker, 5)
    old_q = [c["text"] for c, _ in st.search(target["text"], 5)]
    texts = [c["text"] for c, _ in top]
    log.append(dict(doc=d, cid=target["cid"], upsert_ms=round(up_ms, 2), new_top1=top[0][0]["cid"] == target["cid"] and top[0][0]["text"] == new["text"],
                    old_version_absent=all(t_ != target["text"] for t_ in texts) and all(t_ != target["text"] for t_ in old_q)))
live = lambda: len(st.chunks) - len(st.dead)
n_before_del = live()
dl = []
for d in DOCS:
    t = time.perf_counter(); n = sum(st.delete(c["cid"]) for c in CH if c["doc_id"] == d); ms = (time.perf_counter() - t) * 1000
    rels = [g for g in G.values() if any(r.startswith(d) for r in g["relevant"])][:3]
    leak = sum(1 for g in rels for c, _ in st.search(g["query"], 10) if c["doc_id"] == d)
    dl.append(dict(doc=d, deleted=n, delete_ms=round(ms, 2), leaked_in_top10=leak))
t = time.perf_counter(); before = len(st.chunks); st.compact(); comp_ms = (time.perf_counter() - t) * 1000
res["update"] = dict(upsert=log, delete=dl, live_before_delete=n_before_del, live_after_delete=live(), index_size_before_compact=before, index_size_after_compact=len(st.chunks), compact_ms=round(comp_ms, 1))
print(json.dumps(res["update"], ensure_ascii=False, indent=1))
json.dump(res, open("results/index.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(res["english"]), json.dumps(res["hnsw_sweep"]))
