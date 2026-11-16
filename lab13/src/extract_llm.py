"""Метод Б: LLM + JSON-схема + закритий словник + обов'язкова evidence-цитата + валідація + ≥2 повтори.
Бекенди: --backend anthropic (потрібен ANTHROPIC_API_KEY у середовищі; ключ у коді не зберігається) | --backend replay (читає сирі виходи з llm_log/raw_<split>.jsonl,
створені в сесії Claude без API). Запуск: python3 src/extract_llm.py --split test --backend replay"""
import argparse, json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
PROMPT_VERSION = "p1"; MODEL = "claude-sonnet-5-5"; RELS = {"HAS_POSITION": ("Person", "Position"), "WORKS_IN": ("Person", "Department"), "HAS_SKILL": ("Person", "Skill"), "COMPLETED": ("Person", "Course"), "REPORTS_TO": ("Person", "Person"), "REQUIRES_SKILL": ("Position", "Skill")}
SCHEMA = {"type": "object", "properties": {"claims": {"type": "array", "items": {"type": "object", "required": ["subject", "relation", "object", "evidence"], "properties": {"subject": {"type": "string"}, "relation": {"enum": list(RELS)}, "object": {"type": "string"}, "evidence": {"type": "string"}}}}}}
FEWSHOT = "Приклад: «Іван Шевчук працює на посаді Рекрутер.» → {\"claims\":[{\"subject\":\"Іван Шевчук\",\"relation\":\"HAS_POSITION\",\"object\":\"Рекрутер\",\"evidence\":\"Іван Шевчук працює на посаді Рекрутер.\"}]}. Негативні/планові/гіпотетичні речення («не завершив», «планує») НЕ дають тверджень."
def prompt(text): return f"Витягни твердження зі схемою {json.dumps(SCHEMA, ensure_ascii=False)}. Дозволені відношення: {list(RELS)}. Суб'єкт і об'єкт — рядки з тексту; зайвого не вигадуй; evidence — дослівна цитата з тексту. Відповідай лише JSON.\n{FEWSHOT}\nТЕКСТ:\n{text}"
def call_api(text):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(dict(model=MODEL, max_tokens=2000, temperature=0, messages=[{"role": "user", "content": prompt(text)}])).encode(), headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["content"][0]["text"]
def link(name, typ, table):   # нормалізація на id у закритому словнику
    n = name.strip().lower()
    for cid, forms in table.get(typ, {}).items():
        if any(n == f.lower() or (len(f) > 3 and f.lower() in n) for f in forms): return cid
    return None
def vocab():
    import csv; t = {"Person": {}, "Position": {}, "Skill": {}, "Course": {}, "Department": {}}
    for r in csv.DictReader(open(R + "/data/src/nodes_Employee.csv", encoding="utf-8")): t["Person"][r["id"]] = [r["name"], r["name"].split()[1]]
    for r in csv.DictReader(open(R + "/data/src/nodes_Position.csv", encoding="utf-8")): t["Position"][r["id"]] = [r["name"]]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import extract_rules as X
    t["Skill"] = {k: v + [v2 for v2 in v] for k, v in X.SKILLS.items()}; t["Skill"]["python"].append("програмування на python"); t["Course"] = {k: [v] for k, v in X.COURSES.items()}; t["Department"] = {k: [v] for k, v in X.DEPS.items()}; return t
def validate(raw, text):
    """повертає (claims, відхилені із причиною)"""
    try: d = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception as e: raise ValueError("невалідний JSON: " + str(e))
    V = vocab(); ok, bad = [], []
    for c in d.get("claims", []):
        if c.get("relation") not in RELS: bad.append((c, "relation поза словником")); continue
        ts, to = RELS[c["relation"]]; s, o = link(c["subject"], ts, V), link(c["object"], to, V)
        if not s or not o: bad.append((c, "сутність не зіставлена зі словником")); continue
        ev = c.get("evidence", ""); pos = text.find(ev) if ev else -1
        if pos < 0: bad.append((c, "evidence відсутня в тексті (можлива вигадка)")); continue
        ok.append(dict(subj=dict(id=s), rel=c["relation"], obj=dict(id=o), evidence=dict(start=pos, end=pos + len(ev)), evidence_text=ev))
    return ok, bad
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--split", default="test"); ap.add_argument("--backend", default="replay"); a = ap.parse_args()
    raws = {}
    if a.backend == "replay":
        for l in open(f"{R}/llm_log/raw_{a.split}.jsonl", encoding="utf-8"): r = json.loads(l); raws[r["doc"]] = r
    out, rej = [], []
    for d in doc_ids(a.split):
        text = read_doc(d)
        for attempt in range(3):   # перша спроба + 2 повтори
            try:
                raw = raws[d]["raw"] if a.backend == "replay" else call_api(text); ok, bad = validate(raw, text); break
            except Exception as e:
                if attempt == 2: ok, bad = [], [({}, f"3 невдалі спроби: {e}")]; 
                time.sleep(0 if a.backend == "replay" else 2 ** attempt)
        for c in ok: c.update(doc=d, method="llm", model=MODEL, version=PROMPT_VERSION, confidence=None); out.append(c)
        rej += [dict(doc=d, claim=c, reason=r) for c, r in bad]
    open(f"{R}/results/pred_llm_{a.split}.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
    json.dump(rej, open(f"{R}/results/llm_rejected_{a.split}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(len(out), "прийнято,", len(rej), "відхилено валідацією")
