"""Мінімальна реалізація BM25Okapi (формули rank_bm25) — запасний варіант, якщо пакет rank_bm25 недоступний."""
import math, numpy as np
class BM25Okapi:
    def __init__(self, corpus, k1=1.5, b=0.75, epsilon=0.25):
        self.k1, self.b = k1, b; self.N = len(corpus); self.tf = [dict() for _ in corpus]; self.dl = np.array([len(d) for d in corpus], float)
        self.avgdl = self.dl.mean(); df = {}
        for i, d in enumerate(corpus):
            for w in d: self.tf[i][w] = self.tf[i].get(w, 0) + 1
            for w in set(d): df[w] = df.get(w, 0) + 1
        self.idf = {w: math.log((self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        avg = np.mean(list(self.idf.values())); self.idf = {w: (v if v >= 0 else epsilon * avg) for w, v in self.idf.items()}
    def get_scores(self, q):
        s = np.zeros(self.N)
        for w in q:
            if w not in self.idf: continue
            for i in range(self.N):
                f = self.tf[i].get(w, 0)
                if f: s[i] += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
        return s
