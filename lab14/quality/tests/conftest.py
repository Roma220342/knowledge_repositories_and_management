import os, sys, json, csv, glob, pytest
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); R = os.path.join(Q, "..")
sys.path[:0] = [Q, R + "/src"]
STORE = os.environ.get("QUALITY_STORE", R + "/data/store_v1.jsonl"); GRAPH = os.environ.get("QUALITY_GRAPH", R + "/data/graph_v1")
@pytest.fixture(scope="session")
def S(): return [json.loads(l) for l in open(STORE, encoding="utf-8")]
@pytest.fixture(scope="session")
def rels():
    out = {}
    for f in glob.glob(R + "/graph_data/rels_*.csv"):
        n = os.path.basename(f); p = os.path.join(GRAPH, n); out[n] = list(csv.DictReader(open(p if os.path.exists(p) else f, encoding="utf-8")))
    return out
@pytest.fixture(scope="session")
def nodes():
    ids = set()
    for f in glob.glob(R + "/graph_data/nodes_*.csv"): ids |= {r["id"] for r in csv.DictReader(open(f, encoding="utf-8"))}
    return ids
