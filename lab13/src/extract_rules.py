"""Метод А: словники (gazetteer) + шаблони на рівні речень. Без spaCy (модель недоступна у середовищі) — лише re.
Запуск: python3 src/extract_rules.py --split dev|test [--version v0|v1]  → results/pred_rules_<split>.jsonl"""
import argparse, json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
emps = {r["id"]: r["name"] for r in csv.DictReader(open(R + "/data/src/nodes_Employee.csv", encoding="utf-8"))}
poss = {r["id"]: r["name"] for r in csv.DictReader(open(R + "/data/src/nodes_Position.csv", encoding="utf-8"))}
DEPS = {"dep_it": "ІТ", "dep_hr": "кадрів", "dep_fin": "фінансів", "dep_sales": "продажів", "dep_legal": "юридичний"}
SKILLS = {"python": ["python"], "java": ["java"], "hran": ["hr-аналітика", "hr-аналітики"], "sql": ["sql"], "law": ["трудове право"], "gdpr": ["захист даних"], "negot": ["перемовини", "ведення перемовин"], "comm": ["командна комунікація"], "conf": ["вирішення конфліктів"], "coach": ["коучинг"], "deleg": ["делегування"]}
COURSES = {"c_neg": "Ефективні перемовини", "c_pya": "Python Advanced", "c_jb": "Java Basics", "c_hra": "HR Analytics Pro", "c_sql": "SQL для аналітиків", "c_law": "Трудове право: оновлення", "c_gdpr": "Захист даних (GDPR)", "c_comm": "Командна комунікація", "c_conf": "Вирішення конфліктів", "c_coach": "Коучингові навички", "c_del": "Практикум з делегування", "c_pyb": "Python Basics"}
def mentions(s, off, v):
    out = []; low = s.lower()
    def f(txt, typ, cid):
        for m in re.finditer(re.escape(txt.lower()), low):
            out.append(dict(text=s[m.start():m.end()], start=off + m.start(), end=off + m.end(), type=typ, id=cid))
    for i, n in emps.items(): f(n, "Person", i)
    for i, n in emps.items():
        sn = n.split()[1]
        for m in re.finditer(r"\b" + re.escape(sn) + r"\b", s):
            if not any(o["start"] <= off + m.start() < o["end"] for o in out): out.append(dict(text=sn, start=off + m.start(), end=off + m.end(), type="Person", id=i))
    for i, n in poss.items(): f(n, "Position", i)
    for i, n in DEPS.items():
        for m in re.finditer(r"відділ[уі]? " + re.escape(n), s): out.append(dict(text=n, start=off + m.start() + m.group().index(n), end=off + m.end(), type="Department", id=i))
    for i, ws in SKILLS.items():
        for w in ws:
            for m in re.finditer(re.escape(w), low):
                if not any(o["type"] == "Course" and o["start"] <= off + m.start() < o["end"] for o in out): out.append(dict(text=s[m.start():m.end()], start=off + m.start(), end=off + m.end(), type="Skill", id=i))
    for i, n in COURSES.items():
        for m in re.finditer(re.escape(n), s): out.append(dict(text=n, start=off + m.start(), end=off + m.end(), type="Course", id=i))
    # конкуренція: навичка всередині назви курсу (напр. «Python Advanced») — курс має пріоритет
    out = [o for o in out if not (o["type"] == "Skill" and any(c["type"] == "Course" and c["start"] <= o["start"] and o["end"] <= c["end"] for c in out))]
    return sorted(out, key=lambda x: x["start"])
def extract(doc, version="v1"):
    t = read_doc(doc); res = []
    for m in re.finditer(r"[^.]+\.", t):
        s = m.group(); off = m.start(); ms = mentions(s, off, version); low = s.lower()
        P = [x for x in ms if x["type"] == "Person"]; by = lambda ty: [x for x in ms if x["type"] == ty]
        neg = version == "v1" and re.search(r"\bне\b|планує", low)    # v1: правило з аналізу помилок dev
        def add(rel, a, b, conf): res.append(dict(doc=doc, subj=a, rel=rel, obj=b, evidence=dict(start=off, end=off + len(s)), method="rules", version=version, model="regex+gazetteer", confidence=conf))
        if "для посади" in low and by("Position") and by("Skill"): add("REQUIRES_SKILL", by("Position")[0], by("Skill")[0], .8); continue
        if "керівник" in low and len(P) >= 2: add("REPORTS_TO", P[0], P[1], .8); continue
        if not P: continue
        if by("Position") and ("посад" in low or "—" in s) and not neg: add("HAS_POSITION", P[0], by("Position")[0], .9)
        if by("Department"): add("WORKS_IN", P[0], by("Department")[0], .9)
        if by("Skill") and not by("Course") and ("навичк" in low or "компетенц" in low): add("HAS_SKILL", P[0], by("Skill")[0], .85)
        if by("Course") and re.search(r"завершив|завершила", low) and not neg: add("COMPLETED", P[0], by("Course")[0], .85)
    return res
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--split", default="dev"); ap.add_argument("--version", default="v1"); a = ap.parse_args()
    out = [r for d in doc_ids(a.split) for r in extract(d, a.version)]
    open(f"{R}/results/pred_rules_{a.split}_{a.version}.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n"); print(len(out), "прогнозів")
