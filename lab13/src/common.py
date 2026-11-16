import json, os, re, csv
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def load_gold(split=None): return [r for r in map(json.loads, open(R + "/data/gold.jsonl", encoding="utf-8")) if split in (None, r["split"])]
def doc_ids(split):
    g = {r["doc"] for r in load_gold(split)}; return sorted(g)
def read_doc(d): return open(f"{R}/data/docs/{d}.txt", encoding="utf-8").read()
def key(r): return (r["doc"], r["subj"]["id"], r["rel"], r["obj"]["id"])
