"""Генератор корпусу з 20 HR-документів різних жанрів (seed 13) + золота розмітка з точними офсетами.
УВАГА: тексти шаблонні/синтетичні (див. docs/gold_card.md): метрики оптимістичніші, ніж на реальних текстах."""
import csv, json, random, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); rnd = random.Random(13)
emps = {r["id"]: r["name"] for r in csv.DictReader(open(R + "/data/src/nodes_Employee.csv", encoding="utf-8"))}
poss = {r["id"]: r["name"] for r in csv.DictReader(open(R + "/data/src/nodes_Position.csv", encoding="utf-8"))}
occ = {r["from"]: r["to"] for r in csv.DictReader(open(R + "/data/src/rels_OCCUPIES__Employee__Position.csv", encoding="utf-8"))}
FEM = {"Оксана", "Христина", "Наталія", "Ірина", "Галина", "Леся", "Уляна", "Ольга", "Дарина", "Мирослава", "Тетяна", "Зоряна", "Марія", "Олена", "Софія"}
DEPS = {"dep_it": ["ІТ", "відділ ІТ"], "dep_hr": ["HR", "кадровий відділ"], "dep_fin": ["фінансів"], "dep_sales": ["продажів"], "dep_legal": ["юридичний"]}
DEPNAME = {"dep_it": "ІТ", "dep_hr": "кадрів", "dep_fin": "фінансів", "dep_sales": "продажів", "dep_legal": "юридичний"}
SK = {"python": ["Python", "програмування на Python"], "java": ["Java"], "hran": ["HR-аналітика", "HR-аналітики"], "sql": ["SQL"], "law": ["трудове право"], "gdpr": ["захист даних"],
      "negot": ["перемовини", "ведення перемовин"], "comm": ["командна комунікація"], "conf": ["вирішення конфліктів"], "coach": ["коучинг"], "deleg": ["делегування"]}
CO = {"c_neg": "Ефективні перемовини", "c_pya": "Python Advanced", "c_jb": "Java Basics", "c_hra": "HR Analytics Pro", "c_sql": "SQL для аналітиків", "c_law": "Трудове право: оновлення",
      "c_gdpr": "Захист даних (GDPR)", "c_comm": "Командна комунікація", "c_conf": "Вирішення конфліктів", "c_coach": "Коучингові навички", "c_del": "Практикум з делегування", "c_pyb": "Python Basics"}
pids = list(emps); fem = lambda i: emps[i].split()[0] in FEM
facts = {}
for i in pids:
    facts[i] = dict(pos=occ[i], dep=rnd.choice(list(DEPS)), skills=rnd.sample(list(SK), 3), courses=rnd.sample(list(CO), 2), boss=rnd.choice([j for j in pids if j != i]))
class B:
    def __init__(s): s.t = ""; s.m = []; s.last = None
    def add(s, x):
        if isinstance(x, str): s.t += x; return None
        txt, typ, cid = x; st = len(s.t); s.t += txt; s.m.append(dict(text=txt, start=st, end=st + len(txt), type=typ, id=cid)); return len(s.m) - 1
def pname(i, rnd_form=True):
    fn, sn = emps[i].split(); return rnd.choice([emps[i], emps[i], sn]) if rnd_form else emps[i]
def sent(b, kind, i, f, gold, pron=False):
    """додає речення; gold — список тверджень (суб'єкт-id, rel, об'єкт-id, ind_s, ind_o)"""
    P = lambda: ("Він" if not fem(i) else "Вона", "Person", i) if pron else (pname(i), "Person", i)
    v = lambda m, w: m if not fem(i) else w; s0 = len(b.t)
    def rel(r, ms, mo): gold.append(dict(s=ms, rel=r, o=mo, sent_start=s0))
    if kind == "pos":
        t = rnd.choice([0, 1, 2]); pn = poss[f["pos"]]
        if t == 0: ms = b.add(P()); b.add(" працює на посаді "); mo = b.add((pn, "Position", f["pos"]))
        elif t == 1: ms = b.add(P()); b.add(" обіймає посаду "); mo = b.add((pn, "Position", f["pos"]))
        else: b.add("З 2025 року "); ms = b.add(P()); b.add(" — "); mo = b.add((pn, "Position", f["pos"]))
        rel("HAS_POSITION", ms, mo)
    elif kind == "dep":
        ms = b.add(P()); b.add(rnd.choice([" входить до відділу ", " працює у відділі "])); mo = b.add((rnd.choice(DEPS[f["dep"]]) if False else DEPNAME[f["dep"]], "Department", f["dep"])); rel("WORKS_IN", ms, mo)
    elif kind == "skill":
        sk = rnd.choice(f["skills"]); sf = rnd.choice(SK[sk]); t = rnd.choice([0, 1])
        if pron: b.add("Також ")
        if t == 0: ms = b.add(P()); b.add(" володіє навичкою «"); mo = b.add((sf, "Skill", sk)); b.add("»")
        else: b.add("У "); ms = b.add((emps[i].split()[1] if False else pname(i), "Person", i)) if not pron else b.add(("нього" if not fem(i) else "неї", "Person", i)); b.add(" високий рівень компетенції: "); mo = b.add((sf, "Skill", sk))
        rel("HAS_SKILL", ms, mo)
    elif kind == "course":
        c = rnd.choice(f["courses"]); ms = b.add(P()); b.add(v(" завершив курс «", " завершила курс «")); mo = b.add((CO[c], "Course", c)); b.add("»"); rel("COMPLETED", ms, mo)
    elif kind == "boss":
        j = f["boss"]; b.add("Безпосередній керівник співробітника "); ms = b.add((emps[i], "Person", i)); b.add(" — "); mo = b.add((emps[j], "Person", j)); rel("REPORTS_TO", ms, mo)
    elif kind == "neg":   # хибні тригери: у золоті немає відношення
        c = rnd.choice([k for k in CO if k not in f["courses"]]); t = rnd.choice([0, 1, 2])
        ms = b.add(P())
        if t == 0: b.add(v(" ще не завершив курс «", " ще не завершила курс «")); b.add((CO[c], "Course", c)); b.add("»")
        elif t == 1: b.add(" планує пройти курс «"); b.add((CO[c], "Course", c)); b.add("»")
        else: b.add(" не претендує на посаду "); b.add((poss[rnd.choice([p for p in poss if p != f["pos"]])], "Position", "x"))
    b.add(". ")
def req_sentence(b, pid, gold):
    sk = rnd.sample(list(SK), 1)[0]; s0 = len(b.t); b.add("Для посади "); ms = b.add((poss[pid], "Position", pid)); b.add(" потрібна навичка «"); mo = b.add((rnd.choice(SK[sk]), "Skill", sk)); b.add("». "); gold.append(dict(s=ms, rel="REQUIRES_SKILL", o=mo, sent_start=s0))
GEN = [("news", "Новини компанії"), ("review", "Оцінка ефективності"), ("jobdesc", "Опис вакансії"), ("training", "Звіт про навчання"), ("memo", "Службова записка")]
os.makedirs(R + "/data/docs", exist_ok=True); gold_rows = []; claim_id = 0; ments = []
for d in range(20):
    g, gname = GEN[d % 5]; b = B(); gold = []; b.add(f"{gname} №{d+1}. ")
    people = rnd.sample(pids, 3)
    for i in people:
        f = facts[i]
        kinds = {"news": ["pos", "dep", "course"], "review": ["pos", "skill", "skill", "boss"], "jobdesc": ["pos", "skill"], "training": ["course", "course", "dep"], "memo": ["pos", "boss", "dep"]}[g]
        for k in kinds: sent(b, k, i, f, gold)
        if rnd.random() < .8: sent(b, "skill", i, f, gold, pron=True)
        if rnd.random() < .7: sent(b, "neg", i, f, gold)
    if g in ("jobdesc", "memo"):
        for p in rnd.sample(list(poss), 2): req_sentence(b, p, gold)
    text = b.t.strip(); open(f"{R}/data/docs/doc{d+1:02d}.txt", "w", encoding="utf-8").write(b.t.rstrip())
    split = "test" if d % 10 in (3, 7, 9) else "dev"   # 6 test-документів з 20 (3 жанри), решта dev
    for gd in gold:
        ms, mo = b.m[gd["s"]], b.m[gd["o"]]; claim_id += 1
        ev = (gd["sent_start"], b.t.index(". ", ms["end"]) + 1 if gd["rel"] != "REQUIRES_SKILL" else b.t.index(". ", mo["end"]) + 1)
        gold_rows.append(dict(id=f"G{claim_id:03d}", doc=f"doc{d+1:02d}", split=split, genre=g, subj=ms, rel=gd["rel"], obj=mo, evidence=dict(start=ev[0], end=ev[1])))
    ments.append(dict(doc=f"doc{d+1:02d}", mentions=b.m))
with open(R + "/data/gold.jsonl", "w", encoding="utf-8") as f:
    for r in gold_rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
json.dump(ments, open(R + "/data/gold_mentions.json", "w", encoding="utf-8"), ensure_ascii=False)
from collections import Counter
print(len(gold_rows), Counter(r["split"] for r in gold_rows), Counter(r["rel"] for r in gold_rows), Counter(r["split"] for r in gold_rows if r["rel"] == "HAS_SKILL"))
