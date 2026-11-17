"""Демонстрація HITL: 3 обов'язкові сценарії + додаткові. Дії «людини-рецензента» тут ІМІТОВАНО (reviewer=demo-reviewer): справжнє схвалення має виконати студент через agent/approve.py."""
import sys, os, json, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT + "/agent"]
import propose_fact as PF
res = []
def show(name, r): res.append(dict(scenario=name, **r)); print(name, "→", r["status"], r.get("risk"), r.get("reasons") or r.get("errors"))
show("H1 низький ризик (авто)", PF.propose_fact(dict(subject="emp007", relation="HAS_COMPETENCE", object="pythonProgramming", source="D02-p03", evidence="Знання Python оцінюється на щорічній атестації (D02-p03)"), actor="agent"))
m = PF.propose_fact(dict(subject="emp007", relation="OCCUPIES", object="teamLeadPost", source="D02-p03", evidence="Наказ про призначення на посаду керівника команди"), actor="agent"); show("H2 середній ризик (потрібне схвалення)", m)
time.sleep(1.2); ap = PF.approve(m["id"], "demo-reviewer", "approve", "імітація рецензента для демо"); print("  схвалення →", ap["status"]); res[-1]["after_human"] = ap["status"]
m2 = PF.propose_fact(dict(subject="emp007", relation="OCCUPIES", object="recruiterPost", source="D02-p03", evidence="Пропозиція змінити посаду на рекрутера без наказу"), actor="agent"); show("H2b середній ризик (рецензент відхиляє)", m2)
time.sleep(0.6); ap2 = PF.approve(m2["id"], "demo-reviewer", "reject", "немає наказу"); print("  відхилення →", ap2["status"]); res[-1]["after_human"] = ap2["status"]
show("H3 високий ризик (автовідмова: цикл підпорядкування)", PF.propose_fact(dict(subject="ivan", relation="DIRECT_MANAGER", object="andriy", source="D02-p03", evidence="Пропозиція зробити Андрія підлеглим Івана і навпаки"), actor="agent"))
show("H4 валідація: немає джерела", PF.propose_fact(dict(subject="emp007", relation="HAS_COMPETENCE", object="hrAnalytics", source="", evidence="Тарас має компетенцію з HR-аналітики", action="add"), actor="agent"))
show("H5 заборонена дія delete", PF.propose_fact(dict(subject="emp007", relation="OCCUPIES", object="pythonDeveloperPost", source="D02-p03", evidence="Видалити запис про посаду співробітника", action="delete"), actor="agent"))
# метрики аудиту
ev = [json.loads(l) for l in open(PF.AUDIT, encoding="utf-8")]; by = {}
for e in ev: by.setdefault(e["proposal"], []).append(e)
times = [(max(x["t"] for x in v if x["event"].startswith("human_")) - next(x["t"] for x in v if x["event"] == "queued_for_human")) for v in by.values() if any(x["event"].startswith("human_") for x in v)]
met = dict(proposals=len(by), auto_applied=sum(any(x["event"] == "auto_applied" for x in v) for v in by.values()), queued=sum(any(x["event"] == "queued_for_human" for x in v) for v in by.values()), human_approved=sum(any(x["event"] == "human_approve" for x in v) for v in by.values()), human_rejected=sum(any(x["event"] == "human_reject" for x in v) for v in by.values()), rejected_validation=sum(any(x["event"] == "rejected_validation" for x in v) for v in by.values()), rejected_high_risk=sum(any(x["event"] == "rejected_high_risk" for x in v) for v in by.values()), median_approval_seconds=round(sorted(times)[len(times) // 2], 2) if times else None, audit_events=len(ev))
met["approved_share_of_queued"] = round(met["human_approved"] / met["queued"], 2) if met["queued"] else None
json.dump(dict(scenarios=res, metrics=met), open(ROOT + "/results/hitl_demo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str); print(met)
