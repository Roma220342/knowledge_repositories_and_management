import json, sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
RELS = ["HAS_POSITION", "WORKS_IN", "HAS_SKILL", "COMPLETED", "REPORTS_TO", "REQUIRES_SKILL"]
def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0; return round(p, 3), round(r, 3), round(2 * p * r / (p + r), 3) if p + r else 0.0
def score(pred, gold, docs=None):
    P = {key(r) for r in pred if docs is None or r["doc"] in docs}; G = {key(r) for r in gold if docs is None or r["doc"] in docs}; out = {}
    for rel in RELS + ["ALL"]:
        p = {k for k in P if rel == "ALL" or k[2] == rel}; g = {k for k in G if rel == "ALL" or k[2] == rel}
        out[rel] = dict(zip(("P", "R", "F1"), prf(len(p & g), len(p - g), len(g - p))), tp=len(p & g), fp=len(p - g), fn=len(g - p), n_gold=len(g))
    return out, P, G
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("pred"); ap.add_argument("--split", default="dev"); a = ap.parse_args()
    pred = [json.loads(l) for l in open(a.pred, encoding="utf-8") if l.strip()]; s, _, _ = score(pred, load_gold(a.split), set(doc_ids(a.split)))
    for k, v in s.items(): print(k, v)
