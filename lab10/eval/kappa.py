"""Узгодженість розмітки (Cohen's κ). Розмітник A — автор золотого набору; розмітник B — НЕЗАЛЕЖНИЙ розмітник.
У цій збірці B — автоматичне правило (покриття основ слів запиту у фрагменті >= 0.5), бо другої людини немає.
ЩОБ ВИКОНАТИ ВИМОГУ «ДВОЄ РОЗМІТНИКІВ»: заповніть eval/annotator_B.csv (qid, frag_id, label 0/1) і запустіть: python eval/kappa.py --human"""
import sys, json, csv, numpy as np; sys.path.insert(0, "src")
from common import *; from hybrid import Hybrid
from sklearn.metrics import cohen_kappa_score
F = load_corpus(); G = {g["qid"]: g for g in load_gold()}; H = Hybrid(F)
QS = ["q01","q02","q04","q09","q17","q18","q20","q23","q29","q31","q33","q35"]
pool = []
for q in QS:
    cands = {i for i, _ in H.bm25_rank(G[q]["query"], 5)} | {i for i, _ in H.dense_rank(G[q]["query"], 5)} | {i for i, _ in H.hybrid_rank(G[q]["query"], 5)} | set(G[q]["relevant"])
    for i in sorted(cands): pool.append((q, i))
A = [int(i in G[q]["relevant"]) for q, i in pool]
if "--human" in sys.argv:
    hb = {(r["qid"], r["frag_id"]): int(r["label"]) for r in csv.DictReader(open("eval/annotator_B.csv", encoding="utf-8"))}
    B = [hb[p] for p in pool]
else:
    B = []
    for q, i in pool:
        qs = set(stems(G[q]["query"])); fs = set(stems(H.by_id[i]["text"]))
        B.append(int(len(qs & fs) / max(1, len(qs)) >= 0.5))
    with open("eval/annotator_B.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["qid", "frag_id", "label"]); [w.writerow([q, i, b]) for (q, i), b in zip(pool, B)]
k = cohen_kappa_score(A, B); po = float(np.mean(np.array(A) == np.array(B)))
r = dict(n_queries=len(QS), n_pairs=len(pool), kappa=round(float(k), 3), observed_agreement=round(po, 3), A_pos=int(sum(A)), B_pos=int(sum(B)), annotator_B="automatic-rule" if "--human" not in sys.argv else "human")
json.dump(r, open("results/kappa.json", "w"), indent=1); print(r)
