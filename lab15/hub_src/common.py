import json, re, os, sys, math, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 42
def load_corpus(): return [json.loads(l) for l in open(f"{ROOT}/data/corpus.jsonl", encoding="utf-8")]
def load_gold(): return [json.loads(l) for l in open(f"{ROOT}/eval/gold.jsonl", encoding="utf-8")]
STOP = set("і й та у в на з із до від за що як чи не це які який яка його її їх для при про під між або а але також ж бо щоб"
           " коли де хто скільки яких яке цей ця ці може можна має мають є був була були буде".split())
def tokens(t): return re.findall(r"[\w'’]+", t.lower().replace("’", "'"))
def stem(w): return w[:6]                      # простий префіксний стемер для української (6 символів)
def stems(t): return [stem(w) for w in tokens(t) if w not in STOP and len(w) > 1]
# ---- метрики. ranked: список множин covers (frag_id) у порядку рангу; rel: множина релевантних id
def dedupe(top):
    """Прибирає chunk-и з однаковим покриттям (напр., сусідні дочірні абзаци з одним батьківським розділом)."""
    seen, out = set(), []
    for c, s in top:
        key = frozenset(c["covers"])
        if key not in seen: seen.add(key); out.append((c, s))
    return out
def _gains(ranked_covers, rel):
    """Бінарний виграш: chunk релевантний, лише якщо покриває ще не покритий релевантний фрагмент."""
    seen, g = set(), []
    for c in ranked_covers:
        new = (c & rel) - seen; g.append(1 if new else 0); seen |= new
    return g
def recall_at_k(ranked_covers, rel, k):
    if not rel: return None
    cov = set().union(*ranked_covers[:k]) if ranked_covers[:k] else set()
    return len(cov & rel) / len(rel)
def mrr(ranked_covers, rel):
    if not rel: return None
    for i, h in enumerate(_gains(ranked_covers, rel), 1):
        if h: return 1 / i
    return 0.0
def ndcg_at_k(ranked_covers, rel, k):
    if not rel: return None
    h = _gains(ranked_covers[:k], rel)
    dcg = sum(x / math.log2(i + 1) for i, x in enumerate(h, 1))
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(rel), k) + 1))
    return dcg / ideal

# --- запасні реалізації faiss / rank_bm25, якщо пакети не встановлені (див. shims/)
sys.path.append(os.path.join(ROOT, 'shims'))
