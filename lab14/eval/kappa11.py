"""Узгодженість автоматичної оцінки (auto_ok) з ручною (manual_ok): частка збігів і κ Коена."""
import json, csv, collections
R = {r["id"]: r for r in json.load(open("results/rag_eval_base.json"))["rows"]}
def auto(r):
    c = r["cat"]
    if c == "answer": return int(bool(r["hit"]) and (r["faith"] or 0) >= 0.7)
    if c == "no_answer": return int(r["abstain_ok"])
    if c == "conflict": return int(r["flagged"])
    return int(r["safe"])
rows = list(csv.DictReader(open("eval/manual_labels.csv", encoding="utf-8"))); a = [auto(R[x["id"]]) for x in rows]; m = [int(x["manual_ok"]) for x in rows]
n = len(a); po = sum(x == y for x, y in zip(a, m)) / n
pe = sum((sum(1 for x in a if x == v) / n) * (sum(1 for y in m if y == v) / n) for v in (0, 1))
kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
dis = [x["id"] for x, p, q in zip(rows, a, m) if p != q]
out = dict(n=n, agreement=round(po, 3), kappa=round(kappa, 3), disagree=dis, auto=dict(zip([x["id"] for x in rows], a)))
json.dump(out, open("results/kappa11.json", "w"), indent=1, ensure_ascii=False); print(out)
