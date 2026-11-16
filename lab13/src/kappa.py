"""κ Коена між золотом (розмітник 1) і data/annot2_template.csv (розмітник 2 — заповнює студент незалежно, не дивлячись у gold)."""
import csv, json, sys, os, collections
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); a = json.load(open(R + "/data/annot2_gold_labels.json"))
b = [r[-1].strip() for r in list(csv.reader(open(R + "/data/annot2_template.csv", encoding="utf-8")))[1:]]
if not all(b): sys.exit("Колонку розмітника 2 не заповнено: κ не обчислено")
n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; ca, cb = collections.Counter(a), collections.Counter(b); pe = sum(ca[k] * cb[k] for k in ca) / n ** 2
print("n =", n, "agreement =", round(po, 3), "kappa =", round((po - pe) / (1 - pe), 3))
