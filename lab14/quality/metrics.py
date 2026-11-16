"""11 метрик якості за 8 вимірами. python3 quality/metrics.py store_v0 data/graph_v0 baseline"""
import sys, os, json, re, itertools, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from store import *; from common import stems
REQ = ["title", "section", "text", "date", "sensitivity", "source_url"]
GLOSS = {"текучість кадрів": "плинність кадрів", "текучості кадрів": "плинності кадрів"}
THR = dict(completeness=0.99, validity_dates=0.99, provenance=0.99, uniqueness_text=0.99, uniqueness_entities=0.95, consistency_values=0, consistency_logical=0, timeliness=0.85, accuracy=0.95, availability_graph=1.0, terminology=1.0)
def jac(a, b): return len(a & b) / len(a | b) if a | b else 0
def num(t): return set(re.findall(r"\d+(?:[.,]\d+)?", t)) | set(w for w in ["два", "три", "шість", "двох", "трьох"] if w in t.lower())
def compute(S, nodes, rels, er_unique=None, acc=None):
    n = len(S); m = {}
    m["completeness"] = sum(all(str(c.get(k, "")).strip() for k in REQ) for c in S) / n
    m["validity_dates"] = sum(iso(c.get("date", "")) is not None for c in S) / n
    m["provenance"] = sum(str(c.get("source_url", "")).startswith("internal://hub/kb/") for c in S) / n
    st = [(c["id"], set(stems(c["text"]))) for c in S]; dups = set()
    for (i, a), (j, b) in itertools.combinations(st, 2):
        if jac(a, b) >= 0.8: dups.add(j if j.startswith("DUP-") or (not i.startswith("DUP-") and j > i) else i)
    m["uniqueness_text"] = 1 - len(dups) / n
    conf = []
    for (i, a), (j, b) in itertools.combinations(st, 2):
        if any(next(c for c in S if c["id"] == z).get("valid_to") for z in (i, j)) or i.split("-")[0] == j.split("-")[0] or len(a & b) / max(1, min(len(a), len(b))) < 0.6 or i.startswith("DUP-") or j.startswith("DUP-"): continue
        ta = next(c["text"] for c in S if c["id"] == i); tb = next(c["text"] for c in S if c["id"] == j)
        if num(ta) != num(tb): conf.append((i, j))
    m["consistency_values"] = len(conf)
    pos = {}
    for r in rels["rels_OCCUPIES__Employee__Position.csv"]: pos.setdefault(r["from"], set()).add(r["to"])
    mg = {}
    for r in rels["rels_DIRECT_MANAGER__Employee__Employee.csv"]: mg.setdefault(r["from"], set()).add(r["to"])
    two = [e for e, p in pos.items() if len(p) > 1]; cyc = [(a, b) for a, bs in mg.items() for b in bs if a in mg.get(b, set()) and a < b]
    m["consistency_logical"] = len(two) + len(cyc)
    fresh = sum(1 for c in S if iso(c.get("date", "")) and (TODAY - iso(c["date"])).days <= 730) / n; m["timeliness"] = fresh
    m["accuracy"] = acc if acc is not None else None
    bad_edges = sum(1 for rs in rels.values() for r in rs if r["from"] not in nodes or r["to"] not in nodes); tot = sum(len(rs) for rs in rels.values()); m["availability_graph"] = 1 - bad_edges / tot
    var = sum(any(k in c["text"] for k in GLOSS) for c in S); m["terminology"] = 1 - var / n
    m["uniqueness_entities"] = er_unique
    return m, dict(dups=sorted(dups), conflicts=conf, two_positions=two, cycles=cyc)
if __name__ == "__main__":
    name, gdir, tag = sys.argv[1:4]; S = load_store(name); nodes, rels = load_graph(R + "/" + gdir if gdir != "-" else None)
    acc = None; p = R + f"/quality/accuracy_sample_{tag}.csv"
    if os.path.exists(p): rows = list(csv.DictReader(open(p, encoding="utf-8"))); acc = sum(r["label"] == "точний" for r in rows) / len(rows)
    er = json.load(open(R + f"/quality/er_uniqueness_{tag}.json"))["uniqueness"] if os.path.exists(R + f"/quality/er_uniqueness_{tag}.json") else None
    m, det = compute(S, nodes, rels, er, acc); m = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
    json.dump(dict(version=tag, date="2026-11-16", n_records=len(S), thresholds=THR, metrics=m, details=det), open(R + f"/quality/metrics_{tag}.json", "w"), ensure_ascii=False, indent=1); print(m); print({k: len(v) for k, v in det.items()})
