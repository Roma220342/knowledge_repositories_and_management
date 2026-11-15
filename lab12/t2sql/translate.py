"""Офлайн-«перекладач» питань українською в SQL через семантичний шар (правила + синоніми з metrics.yml). Замінює LLM у середовищі без API:
LLM-варіант отримав би той самий семантичний контекст (метрики, виміри, схему) — див. build_prompt()."""
import re, os, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, R + "/semantic"); from metrics import sql_for, METRICS, DIMS, CFG
DIM_WORDS = [("year", ["за роками", "по роках", "щороку", "у розрізі років"]), ("quarter", ["за кварталами", "кварталами", "по кварталах", "щокварталу"]), ("month", ["помісячно", "за місяцями", "по місяцях"]),
             ("subclass", ["за підкласами"]), ("class", ["за класами", "за класом", "за типом навичок"]), ("competence", ["за компетенціями"]), ("position", ["за посадами", "по посадах"]),
             ("provider", ["за провайдером", "за типом провайдера", "за провайдерами"]), ("employee", ["за співробітниками", "по співробітниках", "кожного співробітника"]), ("course", ["за курсами", "по курсах"])]
CLASSES = {"технічн": "Технічні навички", "м'як": "М'які навички", "м’як": "М'які навички"}
POSITIONS = {"python-розробник": "Python-розробник", "hr-менеджер": "HR-менеджер", "рекрутер": "Рекрутер", "керівник команди": "Керівник команди"}
def build_prompt(q):
    ms = "\n".join(f"- {m['name']}: {m['definition']} Формула: {m['formula']}. Синоніми: {', '.join(m['synonyms'])}" for m in CFG["metrics"])
    return ("Ти перекладаєш питання у SQL ЛИШЕ через метрики семантичного шару. Дозволено тільки SELECT. Таблиці: fact_training, dim_date, dim_competence, dim_employee, dim_position, dim_course.\n"
            f"Метрики:\n{ms}\nВиміри: {', '.join(DIMS)}\nПИТАННЯ: {q}")
def translate(q):
    ql = q.lower(); found = None; best = 0
    for name, m in METRICS.items():
        for syn in m["synonyms"] + [m["title"].lower()]:
            if syn in ql and len(syn) > best: found, best = name, len(syn)
    if not found: return dict(ok=False, reason="метрику не розпізнано", sql=None)
    by = [d for d, ws in DIM_WORDS if any(w in ql for w in ws)]; where = {}
    m = re.findall(r"\b(20\d\d)\b", ql)
    if len(m) == 1: where["year"] = int(m[0])
    elif len(m) > 1: where["year"] = [int(x) for x in m]
    for k, v in CLASSES.items():
        if k in ql: where["class"] = v
    for k, v in POSITIONS.items():
        if k in ql: where["position"] = v
    lim = re.search(r"топ[\s-]*(\d+)", ql); asc = "найменш" in ql
    if lim and not by:
        by = ["course"] if "курс" in ql else ["employee"] if "співробітник" in ql else by
    return dict(ok=True, metric=found, by=by, where=where, sql=sql_for(found, by, where, order_desc=not asc, limit=int(lim.group(1)) if lim else None))
