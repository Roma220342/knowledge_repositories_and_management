"""Результат 3: векторний індекс (FAISS HNSW), дві моделі embeddings, upsert/delete."""
import time, numpy as np, faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from common import stems, SEED
class Embedder:
    """Щільні векторні представлення без завантаження зовнішніх моделей (LSA = TF-IDF + SVD).
    kind='word': стеми слів + біграми; kind='char': символьні n-грами 3–5 (стійкі до морфології української).
    У робочому середовищі з доступом до HuggingFace замініть на SentenceTransformer('intfloat/multilingual-e5-base') — інтерфейс fit/encode той самий."""
    def __init__(self, kind="char", dim=128):
        self.kind, self.dim = kind, dim
        self.v = (TfidfVectorizer(tokenizer=stems, token_pattern=None, ngram_range=(1, 2), sublinear_tf=True) if kind == "word"
                  else TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True))
    def fit(self, texts):
        X = self.v.fit_transform(texts)
        self.svd = TruncatedSVD(n_components=min(self.dim, X.shape[0] - 1, X.shape[1] - 1), random_state=SEED).fit(X)
        return self
    def encode(self, texts):
        return normalize(self.svd.transform(self.v.transform(texts))).astype("float32")
class STEmbedder:
    """Адаптер для sentence-transformers (НЕ запускався в цьому середовищі: немає доступу до HuggingFace).
    Приклад: VectorStore(STEmbedder('intfloat/multilingual-e5-base')) або 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'."""
    def __init__(self, name="intfloat/multilingual-e5-base", e5=True):
        from sentence_transformers import SentenceTransformer
        self.m, self.e5 = SentenceTransformer(name), e5
    def fit(self, texts): return self
    def encode(self, texts): return self.m.encode([("passage: " + t) if self.e5 else t for t in texts], normalize_embeddings=True).astype("float32")
    def encode_query(self, texts): return self.m.encode([("query: " + t) if self.e5 else t for t in texts], normalize_embeddings=True).astype("float32")
class VectorStore:
    """HNSW-індекс (косинус через inner product на нормованих векторах) з upsert/delete (tombstones + compact)."""
    def __init__(self, embedder, M=32, efC=80, efS=64):
        self.emb, self.M, self.efC, self.efS = embedder, M, efC, efS
        self.chunks, self.dead = [], set()
    def _new_index(self, d):
        ix = faiss.IndexHNSWFlat(d, self.M, faiss.METRIC_INNER_PRODUCT)
        ix.hnsw.efConstruction, ix.hnsw.efSearch = self.efC, self.efS; return ix
    def build(self, chunks):
        t = time.perf_counter()
        self.chunks = list(chunks); self.emb.fit([c["text"] for c in self.chunks])
        self.V = self.emb.encode([c["text"] for c in self.chunks])
        self.ix = self._new_index(self.V.shape[1]); self.ix.add(self.V); self.dead = set()
        self.build_s = time.perf_counter() - t; return self
    def search(self, q, k=10, allowed=None):
        """allowed: множина cid для pre-filter (None = без фільтра). Повертає [(chunk, score)]."""
        qv = (self.emb.encode_query if hasattr(self.emb, 'encode_query') else self.emb.encode)([q]); out = []
        if allowed is not None and len(allowed) < 0.5 * len(self.chunks):      # вузький фільтр -> точний пошук по підмножині
            idx = [i for i, c in enumerate(self.chunks) if c["cid"] in allowed and i not in self.dead]
            if not idx: return []
            s = self.V[idx] @ qv[0]; o = np.argsort(-s)[:k]
            return [(self.chunks[idx[i]], float(s[i])) for i in o]
        fetch = min(len(self.chunks), k * 6 if (allowed is not None or self.dead) else k)
        self.ix.hnsw.efSearch = max(self.efS, fetch)
        D, I = self.ix.search(qv, fetch)
        for d, i in zip(D[0], I[0]):
            if i < 0 or i in self.dead: continue
            c = self.chunks[i]
            if allowed is not None and c["cid"] not in allowed: continue
            out.append((c, float(d)))
            if len(out) == k: break
        return out
    # --- оновлення індексу
    def upsert(self, chunk):
        """Новий або змінений chunk (за cid): старий вектор помічається tombstone, новий додається в HNSW."""
        for i, c in enumerate(self.chunks):
            if c["cid"] == chunk["cid"] and i not in self.dead: self.dead.add(i)
        v = self.emb.encode([chunk["text"]]); self.ix.add(v); self.V = np.vstack([self.V, v]); self.chunks.append(chunk)
    def delete(self, cid):
        n = 0
        for i, c in enumerate(self.chunks):
            if c["cid"] == cid and i not in self.dead: self.dead.add(i); n += 1
        return n
    def compact(self):
        """Фізичне видалення tombstones: перебудова HNSW без «мертвих» вузлів (словник моделі не перенавчається)."""
        keep = [i for i in range(len(self.chunks)) if i not in self.dead]
        self.chunks = [self.chunks[i] for i in keep]; self.V = self.V[keep]
        self.ix = self._new_index(self.V.shape[1]); self.ix.add(self.V); self.dead = set()
