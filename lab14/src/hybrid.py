"""Результат 4: BM25 + dense, злиття RRF (k=60), reranker (топ-30 -> топ-5/10), pre-filter за метаданими."""
import numpy as np, time
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from common import stems
from chunking import hierarchical
from index import Embedder, VectorStore
SENS = ["public", "internal", "confidential", "restricted"]
class Hybrid:
    def __init__(self, frags, dense_kind="word", rrf_k=60, pool=30):
        self.F = frags; self.by_id = {f["id"]: f for f in frags}; self.rrf_k, self.pool = rrf_k, pool
        self.ids = [f["id"] for f in frags]
        self.bm25 = BM25Okapi([stems(f["text"]) for f in frags], k1=1.5, b=0.75)
        ch = hierarchical(frags)
        for c in ch: c["covers"] = {c["cid"]}
        self.store = VectorStore(Embedder(dense_kind, 128), M=32, efC=80, efS=64).build(ch)
        self.cv = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit([f["text"] for f in frags])
        self.CV = self.cv.transform([f["text"] for f in frags]); self.idx = {i: n for n, i in enumerate(self.ids)}
    # ---- pre-filter: повертає множину дозволених id (None = без фільтра)
    def allowed(self, types=None, max_sensitivity=None, date_from=None, date_to=None):
        if not any([types, max_sensitivity, date_from, date_to]): return None
        ok = set()
        for f in self.F:
            if types and f["type"] not in types: continue
            if max_sensitivity and SENS.index(f["sensitivity"]) > SENS.index(max_sensitivity): continue
            if date_from and f["date"] < date_from: continue
            if date_to and f["date"] > date_to: continue
            ok.add(f["id"])
        return ok
    def bm25_rank(self, q, k=30, allowed=None):
        s = self.bm25.get_scores(stems(q))
        order = np.argsort(-s)
        out = [(self.ids[i], float(s[i])) for i in order if s[i] > 0 and (allowed is None or self.ids[i] in allowed)]
        return out[:k]
    def dense_rank(self, q, k=30, allowed=None):
        return [(c["cid"], s) for c, s in self.store.search(q, k, allowed)]
    def rrf(self, lists, k=None):
        k = k or self.rrf_k; sc = {}
        for lst in lists:
            for r, (i, _) in enumerate(lst, 1): sc[i] = sc.get(i, 0) + 1 / (k + r)
        return sorted(sc.items(), key=lambda x: -x[1])
    def hybrid_rank(self, q, k=30, allowed=None):
        return self.rrf([self.bm25_rank(q, self.pool, allowed), self.dense_rank(q, self.pool, allowed)])[:k]
    # ---- reranker: легка оцінка пари (запит, фрагмент) замість cross-encoder (немає доступу до HuggingFace у середовищі)
    def rerank(self, q, cands, k=10):
        qs = stems(q); qb = set(zip(qs, qs[1:])); qv = self.cv.transform([q])
        out = []
        for i, _ in cands:
            fs = stems(self.by_id[i]["text"]); fset = set(fs); fb = set(zip(fs, fs[1:]))
            cos = float((self.CV[self.idx[i]] @ qv.T).toarray()[0, 0])
            cov = sum(1 for w in set(qs) if w in fset) / max(1, len(set(qs)))
            bi = len(qb & fb) / max(1, len(qb))
            out.append((i, 0.4 * cos + 0.4 * cov + 0.2 * bi))
        return sorted(out, key=lambda x: -x[1])[:k]
    def hybrid_rerank(self, q, k=10, allowed=None):
        return self.rerank(q, self.hybrid_rank(q, self.pool, allowed), k)
