"""Генератор синтетичного корпусу HR-текстів (seed 42) + золотої розмітки за конструкцією. ВАЖЛИВО: тексти синтетичні (див. docs/gold_card.md)."""
import random, json, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from lexicon import *
R = random.Random(42); ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
names = [r["name"] for r in csv.DictReader(open(ROOT + "/data/nodes_Employee.csv", encoding="utf-8"))]
FEM = {"Оксана", "Христина", "Наталія", "Ірина", "Галина", "Леся", "Уляна", "Ольга", "Дарина", "Мирослава", "Тетяна", "Зоряна", "Марія", "Олена", "Софія"}
fem = lambda n: n.split()[0] in FEM
V = lambda n, m, f: f if fem(n) else m
MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
def date(): return (f"{R.randint(1,28)} {MONTHS[R.randint(0,11)]} {R.choice([2025,2026])}" if R.random() < .5 else f"{R.randint(1,28):02d}.{R.randint(1,12):02d}.{R.choice([2025,2026])}")
def pos_f(c, gen=True):
    f = POS[c]; return (f[3] if len(f) > 3 and R.random() < .22 else f[1]) if gen else f[0]
def skill_f(c): f = SKILL[c]; return f[1] if len(f) > 1 and R.random() < .4 else f[0]
E = lambda t, c, s: (t, c, s)
# профілі
prof = {}
for n in names:
    cs = set(R.sample(list(COURSE), R.choice([1, 2, 2, 3])))
    if "negotiationCourse" in cs: 
        if R.random() < .85: cs.add("conflictWorkshop")
    elif R.random() < .08: cs.add("conflictWorkshop")
    prof[n] = dict(pos=R.choice(list(POS)), courses=sorted(cs))
sents = []   # (parts, rels, kind)
for n, p in prof.items():
    P = E("PER", n, n)
    sents.append(([P, f" {R.choice(['працює на посаді', 'обіймає посаду'])} ", E("POS", p["pos"], pos_f(p["pos"])), "."], [("OCCUPIES", n, p["pos"])], "occ", ["Посаду ", E("POS", p["pos"], pos_f(p["pos"])), " посідає ", P, "."]))
    for c in p["courses"]:
        k = R.random()
        if k < .55: sents.append(([P, f" {V(n,'успішно завершив','успішно завершила')} курс «", E("COURSE", c, COURSE[c]), "»."], [("COMPLETED", n, c)], "comp", [P, f" {V(n,'склав','склала')} іспит і отримав сертифікат за курсом «", E("COURSE", c, COURSE[c]), "»."]))
        elif k < .75: sents.append(([P, f" {V(n,'пройшов','пройшла')} навчання за програмою «", E("COURSE", c, COURSE[c]), "»."], [("COMPLETED", n, c)], "comp", ["Серед випускників курсу «", E("COURSE", c, COURSE[c]), "» — ", P, "."]))
        elif k < .9:  # кореференція
            sents.append(([P, f" {R.choice(['працює над проєктом', 'бере участь у розвитку відділу'])}. {V(n,'Він','Вона')} {V(n,'пройшов','пройшла')} курс «", E("COURSE", c, COURSE[c]), "»."], [("COMPLETED", n, c)], "coref"))
        else: sents.append((["Курс «", E("COURSE", c, COURSE[c]), "» ", V(n, "закінчив", "закінчила"), " ", E("PER", n, n), "."], [("COMPLETED", n, c)], "comp_inv"))
for n in R.sample(names, 11):   # негативні (дистрактори)
    c = R.choice(list(COURSE)); P = E("PER", n, n)
    sents.append(([P, f" {R.choice(['не завершив','не завершила']) if False else V(n,'не завершив','не завершила')} курс «", E("COURSE", c, COURSE[c]), "»."], [], "neg"))
for n in R.sample(names, 3):
    c = R.choice(list(COURSE)); sents.append(([E("PER", n, n), f" {V(n,'не склав','не склала')} підсумковий тест курсу «", E("COURSE", c, COURSE[c]), "»."], [], "neg"))
for n in R.sample(names, 6):
    p2 = R.choice(list(POS)); P = E("PER", n, n)
    sents.append(([P, f" {R.choice(['переведено','призначено'])} на посаду ", E("POS", p2, pos_f(p2)), " з ", E("DATE", "d", date()), "."], [("PROMOTED_TO", n, p2)], "prom"))
for c, pp in R.sample(list(POS.items()), 4):
    for s in R.sample(list(SKILL), 2): sents.append((["Для посади ", E("POS", c, pos_f(c)), " потрібна навичка: ", E("SKILL", s, skill_f(s)), "."], [("REQUIRES", c, s)], "req", ["Кандидат на посаду ", E("POS", c, pos_f(c)), " має вміти: ", E("SKILL", s, skill_f(s)), "."]))
for i, c in enumerate(R.sample(list(POS), 4)):
    s = R.choice(list(SKILL)); code = f"VAC-2026-{R.randint(1,99):03d}"
    sents.append((["Вакансія ", E("CODE", code, code), ": ", E("POS", c, pos_f(c)), ", вимагається навичка: ", E("SKILL", s, skill_f(s)), "."], [("REQUIRES", c, s)], "code"))
for c in COURSE:
    sents.append((["Курс «", E("COURSE", c, COURSE[c]), "» розвиває навичку: ", E("SKILL", COURSE_SKILL[c], skill_f(COURSE_SKILL[c])), "."], [("TEACHES", c, COURSE_SKILL[c])], "teach"))
    sents.append((["Курс «", E("COURSE", c, COURSE[c]), "» проводить ", E("ORG", COURSE_ORG[c], ORG[COURSE_ORG[c]]), "."], [("PROVIDED_BY", c, COURSE_ORG[c])], "prov"))
for n in R.sample(names, 14):
    s = R.choice(list(SKILL)); sents.append(([f"За результатами атестації ", E("PER", n, n), f" {V(n,'підтвердив','підтвердила')} компетенцію: ", E("SKILL", s, skill_f(s)), "."], [("HAS_SKILL", n, s)], "has", [E("PER", n, n), f" {V(n,'продемонстрував','продемонструвала')} високий рівень: ", E("SKILL", s, skill_f(s)), "."]))
R.shuffle(sents)
DT = ["Наказ", "Вакансія", "Протокол атестації", "Новина", "Внутрішній лист", "Звіт відділу"]
N = 24; docs = []
for i in range(N):
    chunk = sents[i::N]
    parts, rels = [E("DATE", "d", date()), f" — {DT[i % 6]} №{i+1}. "], []
    spans = []
    R2 = random.Random(7 + i)
    for item in chunk:
        pp, rr, kind = item[:3]
        if len(item) > 3 and i % 3 == 2 and R2.random() < .6: pp = item[3]; kind += "_para"
        parts += pp + [" "]; rels += [(r, s, o, kind) for r, s, o in rr]
    text = ""; ents = []; pos_ = 0
    for p in parts:
        if isinstance(p, tuple): ents.append(dict(start=len(text), end=len(text) + len(p[2]), type=p[0], text=p[2], canon=p[1] if p[0] != "DATE" else p[2])); text += p[2]
        else: text += p
    docs.append(dict(doc_id=f"D{i+1:02d}", source_type=DT[i % 6], split="test" if i % 3 == 2 else "dev", text=text.strip(), entities=ents, relations=[dict(rel=r, subj=s, obj=o, kind=k) for r, s, o, k in rels]))
# контроль: один і той самий факт може повторитися; прибираємо дублікати у межах документа
with open(ROOT + "/data/gold.jsonl", "w", encoding="utf-8") as f:
    for d in docs: f.write(json.dumps(d, ensure_ascii=False) + "\n")
os.makedirs(ROOT + "/data/corpus", exist_ok=True)
for d in docs: open(ROOT + f"/data/corpus/{d['doc_id']}.txt", "w", encoding="utf-8").write(d["text"])
nr = sum(len(d["relations"]) for d in docs); ne = sum(len(d["entities"]) for d in docs)
print(len(docs), "docs; relations", nr, "entities", ne, "test docs", sum(d["split"] == "test" for d in docs), "test rels", sum(len(d["relations"]) for d in docs if d["split"] == "test"))
