"""Результат 2: стратегії chunking. Кожен chunk: {cid, text, covers(set frag_id), ctx_text (контекст для LLM)}.
Одиниця корпусу — фрагмент (абзац, ≈19 слів), тому chunk-и формуються з абзаців/слів документа."""
import numpy as np
from collections import defaultdict
def _by_doc(frags):
    d = defaultdict(list)
    for f in frags: d[f["doc_id"]].append(f)
    return d
def fixed_window(frags, size=60, overlap=15):
    """S1: вікно фіксованого розміру в словах з перекриттям; перетинає межі розділів."""
    out = []
    for did, fs in _by_doc(frags).items():
        words = [(w, f["id"]) for f in fs for w in f["text"].split()]
        step = size - overlap
        for i in range(0, max(1, len(words) - overlap), step):
            w = words[i:i + size]
            t = " ".join(x[0] for x in w)
            out.append(dict(cid=f"{did}-w{i//step:02d}", text=t, covers={x[1] for x in w}, ctx_text=t, doc_id=did))
    return out
def by_heading(frags):
    """S2: один chunk = розділ документа (за заголовком ##)."""
    out = []
    g = defaultdict(list)
    for f in frags: g[(f["doc_id"], f["section_idx"])].append(f)
    for (did, s), fs in g.items():
        t = f"{fs[0]['section']}. " + " ".join(f["text"] for f in fs)
        out.append(dict(cid=f"{did}-s{s}", text=t, covers={f["id"] for f in fs}, ctx_text=t, doc_id=did))
    return out
def hierarchical(frags):
    """S3: ієрархічна (parent-child): індексуємо дочірні абзаци, але в LLM повертаємо батьківський розділ."""
    sec = {}
    for f in frags: sec.setdefault((f["doc_id"], f["section_idx"]), []).append(f)
    out = []
    for f in frags:
        parent = sec[(f["doc_id"], f["section_idx"])]
        ctx = f"{f['section']}. " + " ".join(p["text"] for p in parent)
        out.append(dict(cid=f["id"], text=f["text"], covers={p["id"] for p in parent}, ctx_text=ctx, doc_id=f["doc_id"], self_id=f["id"]))
    return out
def semantic(frags, vec=None, thr=0.12, max_words=80):
    """S4: семантичний — сусідні абзаци об'єднуються, якщо косинусна схожість (TF-IDF char) > thr."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    v = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit([f["text"] for f in frags])
    out = []
    for did, fs in _by_doc(frags).items():
        X = v.transform([f["text"] for f in fs]); cur = [fs[0]]
        def flush(c, n):
            t = " ".join(x["text"] for x in c)
            out.append(dict(cid=f"{did}-m{n:02d}", text=t, covers={x["id"] for x in c}, ctx_text=t, doc_id=did))
        n = 0
        for i in range(1, len(fs)):
            sim = float((X[i] @ X[i - 1].T).toarray()[0, 0])
            if sim > thr and sum(len(x["text"].split()) for x in cur) + len(fs[i]["text"].split()) <= max_words: cur.append(fs[i])
            else: flush(cur, n); n += 1; cur = [fs[i]]
        flush(cur, n)
    return out
STRATEGIES = {"fixed_60_15": fixed_window, "by_heading": by_heading, "hierarchical": hierarchical, "semantic": semantic}
