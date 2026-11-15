"""Генератор даних (seed = 42). Реальні дані: 30 співробітників, 4 посади, 4 компетенції і 2 курси з ЛР 9 (data/src/). Решту — таксономію-розширення,
курси, історію посад (SCD2), події навчання та квартальні знімки — згенеровано синтетично; параметри розподілів задокументовано в docs/star_design.md."""
import csv, random, datetime as dt, os, json, sys
SEED = 42; random.seed(SEED); HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "data"); SRC = os.path.join(D, "src")
H = "http://example.org/hr#"
# --- таксономія: (leaf, label, subclass, class, джерело)
TAX = [("pythonProgramming", "Python programming", "Programming", "HardSkill", "ЛР 9"), ("javaProgramming", "Java programming", "Programming", "HardSkill", "розширення"),
       ("hrAnalytics", "HR analytics", "Analytics", "HardSkill", "ЛР 9"), ("sqlDataAnalysis", "SQL data analysis", "Analytics", "HardSkill", "розширення"),
       ("labourLaw", "Labour law", "Compliance", "HardSkill", "розширення"), ("dataProtection", "Data protection", "Compliance", "HardSkill", "розширення"),
       ("negotiation", "Negotiation", "Communication", "SoftSkill", "ЛР 9"), ("teamCommunication", "Team communication", "Communication", "SoftSkill", "ЛР 9"),
       ("conflictResolution", "Conflict resolution", "Communication", "SoftSkill", "розширення"), ("coaching", "Coaching", "Leadership", "SoftSkill", "розширення"),
       ("delegation", "Delegation", "Leadership", "SoftSkill", "розширення")]
LABEL = {"HardSkill": "Технічні навички", "SoftSkill": "М'які навички", "Programming": "Програмування", "Analytics": "Аналітика", "Compliance": "Відповідність і право", "Communication": "Комунікація", "Leadership": "Лідерство"}
COURSES = [("negotiationCourse", "Ефективні перемовини", 16, "internal", "negotiation"), ("pythonAdvancedCourse", "Python Advanced", 40, "external", "pythonProgramming"),
           ("javaBasics", "Java Basics", 32, "external", "javaProgramming"), ("hrAnalyticsPro", "HR Analytics Pro", 24, "external", "hrAnalytics"), ("sqlForAnalysts", "SQL для аналітиків", 20, "internal", "sqlDataAnalysis"),
           ("labourLawUpdate", "Трудове право: оновлення", 8, "internal", "labourLaw"), ("gdprEssentials", "Захист даних (GDPR)", 6, "internal", "dataProtection"),
           ("teamSync", "Командна комунікація", 12, "internal", "teamCommunication"), ("conflictWorkshop", "Вирішення конфліктів", 10, "external", "conflictResolution"),
           ("coachingSkills", "Коучингові навички", 20, "external", "coaching"), ("delegationLab", "Практикум з делегування", 8, "internal", "delegation"), ("pythonBasics", "Python Basics", 24, "internal", "pythonProgramming")]
POS_COMP = {"pythonDeveloperPost": ["Programming", "Analytics", "Communication"], "hrManagerPost": ["Analytics", "Compliance", "Communication", "Leadership"],
            "recruiterPost": ["Communication", "Compliance", "Analytics"], "teamLeadPost": ["Leadership", "Communication", "Programming"]}
def rows(f): return list(csv.DictReader(open(os.path.join(SRC, f), encoding="utf-8")))
def w(name, header, data):
    with open(os.path.join(D, name), "w", newline="", encoding="utf-8") as fh: c = csv.writer(fh); c.writerow(header); c.writerows(data)
emps = rows("nodes_Employee.csv"); pos = rows("nodes_Position.csv"); occ = {r["from"]: r for r in rows("rels_OCCUPIES__Employee__Position.csv")}
pkey = {p["id"]: i + 1 for i, p in enumerate(pos)}
w("dim_position.csv", ["position_key", "position_id", "position_name", "salary_grade"], [[pkey[p["id"]], p["id"], p["name"], p["salaryGrade"]] for p in pos])
ckey = {}; comp_rows = []
for i, (leaf, lab, sub, cls, src) in enumerate(TAX, 1):
    ckey[leaf] = i; comp_rows.append([i, H + leaf, lab, H + sub, LABEL[sub], H + cls, LABEL[cls], src])
w("dim_competence.csv", ["competence_key", "competence_iri", "competence_label", "subclass_iri", "subclass_label", "class_iri", "class_label", "source"], comp_rows)
w("dim_course.csv", ["course_key", "course_id", "course_name", "default_hours", "provider_type", "competence_key"], [[i, c[0], c[1], c[2], c[3], ckey[c[4]]] for i, c in enumerate(COURSES, 1)])
START, END = dt.date(2024, 1, 1), dt.date(2026, 12, 31); dates = []; d = START
while d <= END:
    q = (d.month - 1) // 3 + 1; dates.append([int(d.strftime("%Y%m%d")), d.isoformat(), d.year, q, d.month, f"{d.year}-Q{q}", d.strftime("%Y-%m"), d.isoweekday(), int(d.isoweekday() >= 6)]); d += dt.timedelta(days=1)
w("dim_date.csv", ["date_key", "full_date", "year", "quarter", "month", "year_quarter", "year_month", "day_of_week", "is_weekend"], dates)
# --- SCD2: ~6 співробітників змінили посаду (Python-розробник -> Керівник команди / Рекрутер -> HR-менеджер) 2025-07-01
random.shuffle(emps_ := list(emps)); promo = set()
for e in emps_:
    cur = occ[e["id"]]["to"]; hd = e["hireDate"][:10]
    if len(promo) < 6 and hd < "2025-01-01" and cur in ("pythonDeveloperPost", "recruiterPost"): promo.add(e["id"])
emp_rows = []; sk = 0; ver = {}   # ver[(emp_id)] = [(sk, pos_id, from, to)]
for e in emps:
    cur = occ[e["id"]]["to"]; hd = e["hireDate"][:10]; start = max(hd, "2024-01-01")
    if e["id"] in promo:
        old = cur; new = "teamLeadPost" if cur == "pythonDeveloperPost" else "hrManagerPost"
        sk += 1; emp_rows.append([sk, e["employeeId"], e["name"], hd, pkey[old], start, "2025-06-30", 0]); ver[e["id"]] = [(sk, old, start, "2025-06-30")]
        sk += 1; emp_rows.append([sk, e["employeeId"], e["name"], hd, pkey[new], "2025-07-01", "9999-12-31", 1]); ver[e["id"]].append((sk, new, "2025-07-01", "9999-12-31"))
    else:
        sk += 1; emp_rows.append([sk, e["employeeId"], e["name"], hd, pkey[cur], start, "9999-12-31", 1]); ver[e["id"]] = [(sk, cur, start, "9999-12-31")]
w("dim_employee.csv", ["employee_sk", "employee_id", "employee_name", "hire_date", "position_key", "valid_from", "valid_to", "is_current"], emp_rows)
# --- факт навчання: ~85 подій на співробітника на період; курси за профілем посади; дати 2024-01 .. 2026-10
ctoc = {i: c for i, c in enumerate(COURSES, 1)}; sub_of = {c[0]: c[2] for c in TAX}; byc = {}
for i, c in ctoc.items(): byc.setdefault(sub_of[c[4]], []).append(i)
def version_at(eid, day):
    for s, p, f, t in ver[eid]:
        if f <= day <= t: return s, p
    return None
cls_of = {c[0]: c[3] for c in TAX}; ft = []; k = 0; seen = set(); last = dt.date(2026, 10, 31)
for e in emps:
    hd = dt.date.fromisoformat(e["hireDate"][:10]); lo = max(hd, START); n = 0
    span = (last - lo).days
    if span <= 0: continue
    n_ev = max(2, int(span / 365 * random.uniform(24, 32)))        # ≈ 24–32 навчальних подій на рік на співробітника
    for _ in range(n_ev):
        day = lo + dt.timedelta(days=random.randint(0, span))
        if day.isoweekday() >= 6: day += dt.timedelta(days=8 - day.isoweekday())
        if day > last: continue
        sk_, pid = version_at(e["id"], day.isoformat())
        sub = random.choice(POS_COMP[pid]) if random.random() < 0.8 else random.choice(list(byc))
        cid = random.choice(byc[sub]); c = ctoc[cid]; hours = float(c[2]) * random.choice([1.0, 1.0, 1.0, 0.5]); cost = round(hours * (45 if c[3] == "external" else 18) * random.uniform(0.85, 1.25), 2)
        if (sk_, int(day.strftime('%Y%m%d')), cid) in seen: continue       # дедуплікація на рівні зерна (перша версія без неї мала 13 колізій, виявлених DQ4)
        seen.add((sk_, int(day.strftime('%Y%m%d')), cid))
        done = 1 if random.random() < (0.9 if c[3] == "internal" else 0.82) else 0
        sb = sa = sat = None
        if done:
            sb = round(random.uniform(3.5, 7.5), 1); sa = round(min(10.0, sb + random.uniform(0.3, 2.8) + (0.4 if c[3] == "external" else 0)), 1); sat = random.choice([3, 4, 4, 5, 5, 2])
        k += 1; ft.append([k, int(day.strftime("%Y%m%d")), sk_, cid, ckey[c[4]], hours, cost, done, sb, sa, sat])
w("fact_training.csv", ["training_key", "date_key", "employee_sk", "course_key", "competence_key", "hours", "cost_eur", "completed", "score_before", "score_after", "satisfaction"], ft)
# --- квартальні знімки
fp = []; k = 0
for e in emps:
    base = float(e["productivityScore"]); hd = e["hireDate"][:10]
    for y in (2024, 2025, 2026):
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: continue
            qend = dt.date(y, q * 3, 1) + dt.timedelta(days=31); qend = dt.date(qend.year, qend.month, 1) - dt.timedelta(days=1)
            if hd > qend.isoformat(): continue
            s, p = version_at(e["id"], qend.isoformat()) or (None, None)
            if s is None: continue
            k += 1; sc = round(max(1.0, min(10.0, base + random.gauss(0, 0.6) - 0.2 * (2026 - y))), 1); fp.append([k, int(qend.strftime("%Y%m%d")), s, 1, sc, round(max(0, (sc - 5)) * 120 * random.uniform(0.8, 1.2), 2)])
w("fact_perf_quarter.csv", ["perf_key", "date_key", "employee_sk", "headcount", "productivity_score", "bonus_eur"], fp)
json.dump(dict(seed=SEED, employees=len(emps), scd2_changes=len(promo), fact_training=len(ft), fact_perf_quarter=len(fp), dim_date=len(dates), dim_course=len(COURSES), dim_competence=len(TAX)), open(os.path.join(D, "generator_manifest.json"), "w"), indent=1)
print(open(os.path.join(D, "generator_manifest.json")).read())
