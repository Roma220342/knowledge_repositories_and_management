"""Будує baseline-версію сховища (store_v0) = корпус ЛР 11 + оновлені редакції X01–X04 + ЗАДОКУМЕНТОВАНІ введені дефекти (seed 14).
Дефекти СИНТЕТИЧНІ (у реальному сховищі ЛР 8–11 дублікатів і т. п. не було): вони моделюють багатоджерельний імпорт; маніфест — data/defects_manifest.json."""
import json, random, csv, os, re, copy
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); rnd = random.Random(14)
C = [json.loads(l) for l in open(R + "/data/corpus.jsonl", encoding="utf-8")]
OV = [json.loads(l) for l in open(R + "/eval/overlay.jsonl", encoding="utf-8")]
X = [o for o in OV if o["id"] != "X05-p01"]        # X05 — навмисна ін'єкція: лишається лише в тестах безпеки ЛР 11
store = copy.deepcopy(C) + copy.deepcopy(X); man = dict(seed=14, duplicates=[], missing_date=[], bad_date=[], missing_source=[], term_variant=[])
# 1) майже-дублікати (імпорт тих самих абзаців з іншої системи): пара (dup, оригінал)
for c in rnd.sample([c for c in C if len(c["text"]) > 80], 14):
    d = copy.deepcopy(c); d["id"] = "DUP-" + c["id"]; t = c["text"]; mode = len(man["duplicates"]) % 3                  # 3 режими: маркер / синоніми+втрата речення / перестановка речень
    ss = re.split(r"(?<=[.!?])\s+", t)
    if mode == 1:
        for a, b in (("потрібно", "необхідно"), ("має", "повинен"), ("працівник", "співробітник"), ("компані", "організаці"), ("керівник", "менеджер"), ("кожн", "будь-який")): t = t.replace(a, b)
        if len(ss) > 2: t = " ".join(ss[:-1])
    elif mode == 2 and len(ss) > 1: t = " ".join(ss[1:] + ss[:1])
    d["text"] = rnd.choice(["Крім того, ", "Також: ", "Зауважимо: "]) + t[0].lower() + t[1:]; d["source_url"] = "import://legacy-wiki/" + c["id"]
    if mode: d["date"] = ""                                                                                           # імпорт без дати для частини дублікатів
    store.append(d); man["duplicates"].append([d["id"], c["id"]])
base_ids = [c["id"] for c in store if not c["id"].startswith("DUP-") and not c["id"].startswith("X")]
for i in rnd.sample(base_ids, 6): next(c for c in store if c["id"] == i)["date"] = ""; man["missing_date"].append(i)
for i in rnd.sample(base_ids, 4): c = next(c for c in store if c["id"] == i); y, m, d = c["date"].split("-") if c["date"] else ("2025", "01", "01"); c["date"] = f"{d}.{m}.{y}"; man["bad_date"].append(i)
for i in rnd.sample(base_ids, 8): next(c for c in store if c["id"] == i)["source_url"] = ""; man["missing_source"].append(i)
# 2) термінологічні варіанти: «плинність» → «текучість кадрів» у 4 абзацах
for c in [c for c in store if "плинн" in c["text"].lower() and c["id"] in base_ids][:5]:
    c["text"] = re.sub("плинності", "текучості кадрів", c["text"]); c["text"] = re.sub("плинність", "текучість кадрів", c["text"]); c["text"] = re.sub("Плинність", "Текучість кадрів", c["text"]); man["term_variant"].append(c["id"])
with open(R + "/data/store_v0.jsonl", "w", encoding="utf-8") as f:
    for c in store: f.write(json.dumps(c, ensure_ascii=False) + "\n")
# 3) граф: логічні дефекти у копії відношень
G = R + "/graph_data/"; occ = list(csv.DictReader(open(G + "rels_OCCUPIES__Employee__Position.csv", encoding="utf-8"))); mgr = list(csv.DictReader(open(G + "rels_DIRECT_MANAGER__Employee__Employee.csv", encoding="utf-8")))
occ.append(dict(occ[0], **{"to": "recruiterPost", "source": "injected-defect"}))                                   # співробітник із двома посадами одночасно
mgr.append(dict(mgr[0], **{"from": "ivan", "to": "emp007", "source": "injected-defect"})); mgr.append(dict(mgr[0], **{"from": "emp007", "to": "ivan", "source": "injected-defect"}))   # цикл підпорядкування
os.makedirs(R + "/data/graph_v0", exist_ok=True)
for name, rows in (("rels_OCCUPIES__Employee__Position.csv", occ), ("rels_DIRECT_MANAGER__Employee__Employee.csv", mgr)):
    w = csv.DictWriter(open(R + "/data/graph_v0/" + name, "w", encoding="utf-8", newline=""), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
man["graph_injected"] = ["andriy має другу посаду recruiterPost", "цикл керівників ivan↔emp007"]
json.dump(man, open(R + "/data/defects_manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(len(store), {k: len(v) for k, v in man.items() if isinstance(v, list)})
