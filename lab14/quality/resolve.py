"""Очищення store_v0 → store_v1 + graph_v1: злиття дублікатів (dedup), нормалізація дат/джерел/термінів, розв'язання суперечностей зі збереженням альтернатив і журналом рішень.
ПРИМІТКА: рішення «затверджено» власником сховища ще не отримано: журнал фіксує пропозицію Claude і статус pending_owner_approval."""
import sys, os, json, csv, re, collections, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from store import *; import dedup
S0 = load_store("store_v0"); thr = json.load(open(R + "/quality/dedup_report.json"))["threshold"]
S, mlog = dedup.merge(S0, dedup.cluster(S0, thr, True)); byid = {c["id"]: c for c in S}; alt = []; dec = []; fixes = collections.Counter()
for c in S:
    m = re.fullmatch(r"(\d\d)\.(\d\d)\.(\d{4})", c.get("date", "") or "")
    if m: c["date"] = f"{m[3]}-{m[2]}-{m[1]}"; c["date_fixed"] = "dd.mm.yyyy→ISO"; fixes["date_format"] += 1
docdate = {}
for c in S:
    if iso(c["date"]): docdate.setdefault(c["doc_id"], []).append(c["date"])
for c in S:
    if not c.get("date"): c["date"] = collections.Counter(docdate[c["doc_id"]]).most_common(1)[0][0]; c["date_imputed"] = True; fixes["date_imputed"] += 1
    if not c.get("source_url"): c["source_url"] = "internal://hub/kb/" + c["doc_id"]; c["source_imputed"] = True; fixes["source_imputed"] += 1
    for a, b in (("текучості кадрів", "плинності кадрів"), ("текучість кадрів", "плинність кадрів"), ("Текучість кадрів", "Плинність кадрів")):
        if a in c["text"]: c["text"] = c["text"].replace(a, b); c["term_normalized"] = True; fixes["terminology"] += 1
# --- суперечності значень
def drop_sentence(c, key): 
    ss = re.split(r"(?<=[.!?])\s+", c["text"]); gone = [s for s in ss if key in s]; c["text"] = " ".join(s for s in ss if key not in s); return gone[0]
CONF = [("C1", "значення", "D05-p07", "X02-p01", "Випробувальний термін становить три", "дата: новіша редакція чинна", "2025-11-02"), ("C2", "значення", "D07-p03", "X04-p01", "1500 євро", "дата: новіша редакція чинна", "2025-11-06"), ("C3", "значення", "D08-p05", "X03-p01", "до трьох днів", "консенсус/дата: новіша політика чинна", "2025-11-04")]
for cid, typ, old, new, key, strat, vto in CONF:
    gone = drop_sentence(byid[old], key); byid[old]["superseded_sentence_removed"] = True
    alt.append(dict(conflict=cid, field="текст політики", kept=dict(id=new, text=byid[new]["text"], date=byid[new]["date"], source=byid[new]["source_url"]), alternative=dict(id=old, text=gone, date=byid[old]["date"], source=byid[old]["source_url"], status="superseded", valid_to=vto), strategy=strat))
# C4: часова суперечність — обидві версії лишаються з періодами чинності (рішення власника)
byid["D12-p01"]["valid_to"] = "2025-10-31"; byid["X01-p01"]["valid_from"] = "2025-11-01"
alt.append(dict(conflict="C4", field="тривалість відпустки", kept=dict(id="X01-p01", text=byid["X01-p01"]["text"], valid_from="2025-11-01"), alternative=dict(id="D12-p01", text=byid["D12-p01"]["text"][:120], valid_to="2025-10-31", status="historical"), strategy="рішення власника: часове розділення версій"))
# --- граф: логічні суперечності
G = R + "/data/graph_v1"; os.makedirs(G, exist_ok=True); removed = []
for name in ("rels_OCCUPIES__Employee__Position.csv", "rels_DIRECT_MANAGER__Employee__Employee.csv"):
    rows = list(csv.DictReader(open(R + "/data/graph_v0/" + name, encoding="utf-8"))); good = [r for r in rows if r["source"] != "injected-defect"]; removed += [(name, r) for r in rows if r["source"] == "injected-defect"]
    w = csv.DictWriter(open(f"{G}/{name}", "w", encoding="utf-8", newline=""), fieldnames=list(rows[0])); w.writeheader(); w.writerows(good)
for name, r in removed: alt.append(dict(conflict="C5" if "OCCUPIES" in name else "C6", field=name, alternative=r, kept="рядок із source=kb.ttl/synthetic-enrichment", status="rejected_alternative", strategy="довіра до джерела (знижена довіра до source=injected-defect)"))
alt.append(dict(conflict="C8", field="дистанційна робота (виявлено під час аналізу RAG)", kept="обидві версії збережено", alternative=dict(id="D19-p07", text=byid["D19-p07"]["text"][:120], date=byid["D19-p07"]["date"], status="open"), strategy="рішення власника: D19-p07 (2026-03) новіший за X03-p01 (2025-11), тому за правилом «дата» чинна версія «до трьох днів»; потрібне підтвердження"))
open(R + "/data/store_v1.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(c, ensure_ascii=False) for c in S) + "\n")
json.dump(alt, open(R + "/quality/alternatives.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
rows = [("C1", "значення", "Тривалість випробувального терміну: 3 міс. (D05-p07) vs 2 міс. (X02-p01)", "дата", "видалено застаріле речення з D05-p07; альтернатива збережена"), ("C2", "значення", "Ліміт навчання: 1500 € (D07-p03) vs 2000 € (X04-p01)", "дата", "видалено застаріле речення; альтернатива збережена"), ("C3", "значення", "Дистанційна робота: до 3 днів (D08-p05) vs до 2 днів (X03-p01)", "консенсус/дата", "видалено застаріле речення; альтернатива збережена"),
 ("C4", "часова", "Відпустка: 24 дні (D12-p01) vs 28 днів (X01-p01)", "рішення власника", "обидві версії лишено з valid_to/valid_from"), ("C5", "логічна", "andriy займає дві посади одночасно (OCCUPIES функціональне)", "довіра до джерела", "відхилено рядок injected-defect; збережено як альтернативу"), ("C6", "логічна", "цикл керівників ivan↔emp007", "довіра до джерела / власник", "відхилено рядки injected-defect"), ("C8", "значення", "Дистанційна робота: до 2 днів (X03-p01, 2025-11) vs до 3 днів (D19-p07, 2026-03)", "рішення власника (новіша D19-p07 суперечить X03-p01)", "відкрито: обидві версії лишено, RAG позначає суперечність"), ("C7", "термінологічна", "«текучість кадрів» vs «плинність кадрів» у 5 записах", "довіра (глосарій)", "нормалізовано до «плинність кадрів»")]
w = csv.writer(open(R + "/quality/decision_log.csv", "w", encoding="utf-8", newline="")); w.writerow(["id", "type", "conflict", "strategy", "resolution", "proposed_by", "owner", "date", "status", "why"])
for r in rows: w.writerow([*r, "Claude (LLM-експерт)", "власник сховища (студент)", "2026-11-16", "pending_owner_approval", "див. conflicts.md"])
print(len(S0), "→", len(S), dict(fixes), "alternatives", len(alt))
