import json, os, csv, re, glob, datetime, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, R + "/src")
TODAY = datetime.date(2026, 11, 16)
def load_store(name="store_v0"): return [json.loads(l) for l in open(f"{R}/data/{name}.jsonl", encoding="utf-8")]
def load_graph(over=None):
    nodes = {}; rels = {}
    for f in glob.glob(R + "/graph_data/nodes_*.csv"):
        for r in csv.DictReader(open(f, encoding="utf-8")): nodes[r["id"]] = f.split("nodes_")[1][:-4]
    for f in glob.glob(R + "/graph_data/rels_*.csv"):
        n = os.path.basename(f)
        if over and os.path.exists(f"{over}/{n}"): f = f"{over}/{n}"
        rels[n] = list(csv.DictReader(open(f, encoding="utf-8")))
    return nodes, rels
def iso(s):
    try: return datetime.date.fromisoformat(s)
    except Exception: return None
