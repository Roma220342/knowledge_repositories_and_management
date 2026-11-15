"""Запасна заміна faiss.IndexHNSWFlat (точний пошук за inner product) — для середовищ без пакета faiss-cpu."""
import numpy as np
METRIC_INNER_PRODUCT = 0
class _H: efConstruction = 40; efSearch = 16
class IndexHNSWFlat:
    def __init__(self, d, M, metric=0): self.d = d; self.hnsw = _H(); self.V = np.zeros((0, d), "float32")
    def add(self, v): self.V = np.vstack([self.V, v])
    def search(self, q, k):
        s = q @ self.V.T; k = min(k, self.V.shape[0]); I = np.argsort(-s, axis=1)[:, :k]
        return np.take_along_axis(s, I, 1), I
