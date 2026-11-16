"""Навмисні дефекти: 3 пошкоджені копії чистого store_v1; gate має їх виявити."""
import sys, os, json, csv, shutil, subprocess, re
Q = os.path.dirname(os.path.abspath(__file__)); R = Q + "/.."; D = Q + "/demo"; shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
S = [json.loads(l) for l in open(R + "/data/store_v1.jsonl", encoding="utf-8")]; res = []
def save(name, S, graph=None):
    open(f"{D}/{name}.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(c, ensure_ascii=False) for c in S) + "\n"); g = graph or R + "/data/graph_v1"; return f"{D}/{name}.jsonl", g
import copy
a = copy.deepcopy(S); a[5]["date"] = "31.02.2025"                                     # D1: некоректна дата
b = copy.deepcopy(S); d = copy.deepcopy(b[10]); d["id"] = "D99-p01"; d["doc_id"] = "D99"; d["text"] = "Також: " + d["text"][0].lower() + d["text"][1:]; b.append(d)   # D2: майже-дублікат
G = D + "/graph_cycle"; shutil.copytree(R + "/data/graph_v1", G); f = G + "/rels_DIRECT_MANAGER__Employee__Employee.csv"; rows = list(csv.DictReader(open(f, encoding="utf-8"))); rows += [dict(rows[0], **{"from": "ivan", "to": "andriy"})]   # andriy→ivan вже є ⇒ цикл
with open(f, "w", encoding="utf-8", newline="") as fh: w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for name, (s, g) in {"D1_bad_date": save("d1", a), "D2_near_duplicate": save("d2", b), "D3_manager_cycle": save("d3", S, G)}.items():
    p = subprocess.run([sys.executable, Q + "/gate.py", name, s, g], capture_output=True, text=True); log = open(f"{Q}/logs/gate_{name}.log", encoding="utf-8").read()
    failed = re.findall(r"^FAILED quality/tests/\w+\.py::(test_\d+_\w+)", log, re.M); res.append((name, p.returncode, failed))
json.dump(res, open(Q + "/demo_defects_result.json", "w"), ensure_ascii=False, indent=1); [print(r) for r in res]
