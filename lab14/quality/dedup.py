"""Entity resolution для абзаців сховища: нормалізація → blocking (рідкісні основи слів) → порівняння (рядки + embeddings + атрибути) → рішення (поріг) → [LLM-суддя на спірних] → злиття з provenance + unmerge.
Команди:  python3 quality/dedup.py eval | detect <store> <tag> | merge <store_in> <store_out> | demo_unmerge"""
import sys, os, re, json, csv, random, difflib, itertools, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from store import *; from common import stems
from index import Embedder
MARK = re.compile(r"^(крім того|також|зауважимо)[,:]\s*", re.I)
def norm(t): return re.sub(r"[^\w\s]", " ", MARK.sub("", t.strip().lower())).split() and " ".join(re.sub(r"[^\w\s]", " ", MARK.sub("", t.strip().lower())).split())
def blocks(S, max_df=15):
    df = collections.Counter(w for c in S for w in set(stems(c["text"]))); B = collections.defaultdict(set)
    for c in S:
        for w in sorted(set(stems(c["text"])), key=lambda w: (df[w], w))[:6]:
            if df[w] <= max_df: B[w].add(c["id"])
    return {frozenset(p) for ids in B.values() for p in itertools.combinations(sorted(ids), 2)}
def features(S):
    byid = {c["id"]: c for c in S}; E = Embedder("char", 96).fit([norm(c["text"]) for c in S]); V = dict(zip([c["id"] for c in S], E.encode([norm(c["text"]) for c in S])))
    def f(a, b):
        ca, cb = byid[a], byid[b]; s = difflib.SequenceMatcher(None, norm(ca["text"]), norm(cb["text"])).ratio(); e = float(V[a] @ V[b])
        at = float(ca["title"] == cb["title"]) * .5 + float(ca["section"] == cb["section"]) * .3 + float(ca["date"] == cb["date"]) * .2
        return dict(s_str=round(s, 4), s_emb=round(e, 4), s_attr=round(at, 4), score=round(.4 * s + .4 * e + .2 * at, 4))
    return f
def pair_key(a, b): return tuple(sorted((a, b)))
def prf(tp, fp, fn): p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0; return round(p, 3), round(r, 3), round(2 * p * r / (p + r), 3) if p + r else 0.0
def judge_replay(a, b):
    p = R + "/llm_log/judge_raw.jsonl"; d = {}
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"): r = json.loads(l); d[pair_key(r["a"], r["b"])] = r
    return d.get(pair_key(a, b))
def cluster(S, thr, use_judge=False, f=None):
    f = f or features(S); keep = []
    for p in blocks(S):
        a, b = sorted(p); sc = f(a, b)["score"]
        if sc >= thr: keep.append((a, b, sc))
        elif use_judge and sc >= thr - 0.08:
            j = judge_replay(a, b)
            if j and j["verdict"] == "duplicate": keep.append((a, b, sc))
    return keep
def merge(S, pairs, logp=R + "/quality/merge_log.jsonl"):
    byid = {c["id"]: c for c in S}; drop = {}; log = []
    for a, b, sc in pairs:                                                       # залишаємо запис з внутрішнім джерелом і без префікса DUP-
        keep, rm = (a, b) if (not a.startswith("DUP-") and (b.startswith("DUP-") or a < b)) else (b, a)
        if rm in drop or keep in drop: continue
        drop[rm] = keep; byid[keep].setdefault("merged_from", []).append(dict(id=rm, source_url=byid[rm]["source_url"], date=byid[rm]["date"], score=sc)); log.append(dict(removed=byid[rm], kept=keep, score=sc, merged_on="2026-11-16"))
    out = [c for c in S if c["id"] not in drop]; open(logp, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in log) + ("\n" if log else "")); return out, log
def unmerge(S, rid, logp=R + "/quality/merge_log.jsonl"):
    for l in open(logp, encoding="utf-8"):
        x = json.loads(l)
        if x["removed"]["id"] == rid:
            k = next(c for c in S if c["id"] == x["kept"]); k["merged_from"] = [m for m in k.get("merged_from", []) if m["id"] != rid] or k.pop("merged_from", None) and []; 
            if not k.get("merged_from"): k.pop("merged_from", None)
            return S + [x["removed"]]
    raise KeyError(rid)
if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "eval":
        S = load_store("store_v0"); man = json.load(open(R + "/data/defects_manifest.json")); pos = {pair_key(a, b) for a, b in man["duplicates"]}; f = features(S); cand = sorted(blocks(S), key=lambda p: tuple(sorted(p)))
        feats = {pair_key(*p): f(*sorted(p)) for p in cand}; rnd = random.Random(14)
        neg = [k for k in feats if k not in pos]; hard = sorted(neg, key=lambda k: -feats[k]["score"])[:60]; rest = [k for k in neg if k not in hard]; neg_sel = hard + rnd.sample(rest, 100 - len(pos) - 60)
        P = [(k, 1) for k in sorted(pos)] + [(k, 0) for k in neg_sel]; rnd.shuffle(P)
        posl = [x for x in P if x[1]]; negl = [x for x in P if not x[1]]; split = {}
        for lst in (posl, negl):
            for i, (k, y) in enumerate(lst): split[k] = "dev" if i % 2 == 0 else "test"
        rows = [dict(a=k[0], b=k[1], label="duplicate" if y else "not_duplicate", split=split[k], **feats[k]) for k, y in P]
        w = csv.DictWriter(open(R + "/quality/pairs_gold.csv", "w", encoding="utf-8", newline=""), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        dev = [r for r in rows if r["split"] == "dev"]; test = [r for r in rows if r["split"] == "test"]
        def ev(rs, t, judge=False):
            tp = fp = fn = 0
            for r in rs:
                pred = r["score"] >= t or (judge and r["score"] >= t - .08 and (judge_replay(r["a"], r["b"]) or {}).get("verdict") == "duplicate"); y = r["label"] == "duplicate"
                tp += pred and y; fp += pred and not y; fn += (not pred) and y
            return prf(tp, fp, fn)
        ths = [round(x / 100, 2) for x in range(30, 100, 1)]; mx = max(ev(dev, t)[2] for t in ths); tie = [t for t in ths if ev(dev, t)[2] == mx]; best = tie[len(tie) // 2];     # медіана інтервалу найкращих порогів
        rep = dict(n_pairs=len(rows), dev=len(dev), test=len(test), pos_dev=sum(r["label"] == "duplicate" for r in dev), pos_test=sum(r["label"] == "duplicate" for r in test), threshold=best, dev_prf=ev(dev, best), test_prf=ev(test, best), test_prf_with_judge=ev(test, best, True),
            per_feature_test={k: max((ev(test, t) for t in [x / 100 for x in range(30, 100)]), key=lambda z: z[2]) for k in ()})
        grey = [r for r in rows if best - .08 <= r["score"] < best]; rep["grey_zone_pairs"] = [(r["a"], r["b"], r["label"], r["score"]) for r in grey]
        json.dump(rep, open(R + "/quality/dedup_report.json", "w"), ensure_ascii=False, indent=1); print(json.dumps({k: v for k, v in rep.items() if k != "grey_zone_pairs"}, ensure_ascii=False)); print("grey", rep["grey_zone_pairs"])
    elif cmd == "detect":
        name, tag = sys.argv[2:4]; S = load_store(name); thr = json.load(open(R + "/quality/dedup_report.json"))["threshold"]; pairs = cluster(S, thr, True); out, _ = merge(S, pairs, R + f"/quality/merge_log_{tag}_dry.jsonl")
        json.dump(dict(uniqueness=round(len(out) / len(S), 4), pairs=[p[:2] for p in pairs], threshold=thr), open(R + f"/quality/er_uniqueness_{tag}.json", "w"), indent=1); print(len(S), len(out), len(pairs))
    elif cmd == "merge":
        S = load_store(sys.argv[2]); thr = json.load(open(R + "/quality/dedup_report.json"))["threshold"]; out, log = merge(S, cluster(S, thr, True)); open(R + f"/data/{sys.argv[3]}.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(c, ensure_ascii=False) for c in out) + "\n"); print(len(S), "→", len(out), "злито", len(log))
    elif cmd == "demo_unmerge":
        S = load_store("store_v0_merged") if os.path.exists(R + "/data/store_v0_merged.jsonl") else None; S = load_store(sys.argv[2]); rid = sys.argv[3]; n0 = len(S); S2 = unmerge(S, rid); print("до unmerge", n0, "після", len(S2), "відновлено", rid in {c["id"] for c in S2})
