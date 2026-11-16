"""Інструмент: pytest (інваріанти на Python)."""
import re, datetime, metrics, dedup, json, os
def test_02_unique_ids(S): ids = [c["id"] for c in S]; assert len(ids) == len(set(ids))
def test_03_completeness(S): bad = [c["id"] for c in S if not all(str(c.get(k, "")).strip() for k in metrics.REQ)]; assert not bad, bad[:8]
def test_04_valid_dates(S):
    bad = []
    for c in S:
        try: datetime.date.fromisoformat(c["date"])
        except Exception: bad.append((c["id"], c["date"]))
    assert not bad, bad[:8]
def test_05_provenance(S): bad = [c["id"] for c in S if not str(c.get("source_url", "")).startswith("internal://hub/kb/")]; assert not bad, bad[:8]
def test_06_terminology(S): bad = [c["id"] for c in S if any(k in c["text"] for k in metrics.GLOSS)]; assert not bad, bad[:8]
def test_07_restricted_not_public(S): bad = [c["id"] for c in S if c.get("restricted") and c.get("sensitivity") == "public"]; assert not bad, bad
def test_08_no_near_duplicates(S):
    thr = json.load(open(os.path.join(os.path.dirname(dedup.__file__), "dedup_report.json")))["threshold"]; f = dedup.features(S); pairs = [p for p in dedup.blocks(S) if f(*sorted(p))["score"] >= thr]; assert not pairs, [sorted(p) for p in pairs[:5]]
def test_09_no_unresolved_value_conflicts(S, rels, nodes):
    m, det = metrics.compute(S, {n: "x" for n in nodes}, rels); assert m["consistency_values"] == 0, det["conflicts"]
