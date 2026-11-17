"""Запис знань лише через propose_fact: валідація (схема/SHACL-подібні обмеження, джерело) → оцінка ризику → low: авто-запис в оверлей з provenance;
medium: черга схвалення людиною; high: автоматична відмова. Агент НЕ має доступу до approve(); базові сховища не змінюються (запис у data/agent_facts.jsonl)."""
import os, sys, json, time, uuid, datetime
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT, ROOT + "/hub_src"]
from graph_context import Graph
PENDING, FACTS, AUDIT = ROOT + "/data/pending_facts.jsonl", ROOT + "/data/agent_facts.jsonl", ROOT + "/logs/audit_log.jsonl"
TYPES = {"HAS_COMPETENCE": ("Employee", "Competence"), "COMPLETED_COURSE": ("Employee", "Course"), "OCCUPIES": ("Employee", "Position"), "DIRECT_MANAGER": ("Employee", "Employee")}
SENS_ORDER = ["public", "internal", "confidential", "restricted"]
def now(): return datetime.datetime.now().isoformat(timespec="seconds")
def audit(ev, pid, **kw):
    os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
    with open(AUDIT, "a", encoding="utf-8") as f: f.write(json.dumps(dict(ts=now(), t=time.time(), event=ev, proposal=pid, **kw), ensure_ascii=False) + "\n")
def validate(p, G, store):
    errs = []
    if p.get("action", "add") != "add": errs.append("дозволена лише дія add (видалення/зміна заборонені)")
    rel = p.get("relation")
    if rel not in TYPES: errs.append(f"relation поза словником: {rel}")
    s, o = p.get("subject"), p.get("object")
    if rel in TYPES:
        for nid, want in zip((s, o), TYPES[rel]):
            if nid not in G.nodes: errs.append(f"вузол не існує: {nid}")
            elif G.nodes[nid]["label"] != want: errs.append(f"тип {nid} = {G.nodes[nid]['label']}, очікується {want}")
    src = p.get("source")
    if not src: errs.append("відсутнє джерело (provenance обов'язковий)")
    elif src not in store: errs.append(f"джерело не знайдено у сховищі: {src}")
    if len((p.get("evidence") or "").strip()) < 15: errs.append("відсутня цитата-доказ (≥15 символів)")
    return errs
def would_cycle(G, s, o):
    seen, st = set(), [o]
    while st:                                                  # чи досяжний s з o за DIRECT_MANAGER (тоді додавання s→o створить цикл)
        n = st.pop()
        if n == s: return True
        if n in seen: continue
        seen.add(n); st += [e[2] for e in G.out.get(n, []) if e[1] == "DIRECT_MANAGER"]
    return False
def risk(p, G, store):
    rel, s, o = p["relation"], p["subject"], p["object"]; reasons = []; lvl = 0
    if SENS_ORDER.index(store[p["source"]]["sensitivity"]) >= 2: lvl = max(lvl, 2); reasons.append("джерело конфіденційне/обмежене")
    if rel == "DIRECT_MANAGER": lvl = max(lvl, 2); reasons.append("зміна ієрархії підпорядкування")
    if would_cycle(G, s, o) and rel == "DIRECT_MANAGER": lvl = max(lvl, 2); reasons.append("створює цикл")
    if rel == "OCCUPIES" and any(e[1] == "OCCUPIES" and e[2] != o for e in G.out.get(s, [])): lvl = max(lvl, 1); reasons.append("змінює існуючу посаду (функціональне відношення)")
    if any(e[1] == rel and e[2] == o for e in G.out.get(s, [])): lvl = max(lvl, 1); reasons.append("факт уже існує (дублікат)")
    return ["low", "medium", "high"][lvl], reasons or ["нове знання з публічного/внутрішнього джерела, без конфліктів"]
def _load(): 
    G = Graph(ROOT + "/graph_ro"); store = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT + "/data/store_v1.jsonl", encoding="utf-8")}; return G, store
def propose_fact(p, actor="agent"):
    G, store = _load(); pid = "P-" + uuid.uuid4().hex[:6]; audit("proposed", pid, actor=actor, payload=p)
    errs = validate(p, G, store)
    if errs: audit("rejected_validation", pid, actor="validator", errors=errs); return dict(id=pid, status="rejected", stage="validation", errors=errs)
    lvl, why = risk(p, G, store); audit("risk_assessed", pid, actor="risk", level=lvl, reasons=why)
    rec = dict(id=pid, **{k: p[k] for k in ("subject", "relation", "object", "source", "evidence")}, risk=lvl, reasons=why, proposed_at=now())
    if lvl == "low":
        rec.update(status="applied", provenance=dict(source=p["source"], proposed_by=actor, applied_at=now(), mode="auto")); open(FACTS, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n"); audit("auto_applied", pid, actor="policy"); return dict(id=pid, status="applied", risk=lvl, reasons=why)
    if lvl == "medium":
        rec["status"] = "pending_approval"; open(PENDING, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n"); audit("queued_for_human", pid, actor="policy"); return dict(id=pid, status="pending_approval", risk=lvl, reasons=why)
    audit("rejected_high_risk", pid, actor="policy", reasons=why); return dict(id=pid, status="rejected", stage="risk", risk=lvl, reasons=why)
def approve(pid, reviewer, decision, comment=""):
    """Викликається ЛИШЕ людиною (agent/approve.py), недоступна агенту й MCP-серверу."""
    rows = [json.loads(l) for l in open(PENDING, encoding="utf-8")] if os.path.exists(PENDING) else []; r = next((x for x in rows if x["id"] == pid and x["status"] == "pending_approval"), None)
    if not r: raise KeyError(pid)
    r["status"] = "applied" if decision == "approve" else "rejected_by_human"; r["reviewer"] = reviewer; r["reviewed_at"] = now()
    open(PENDING, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
    if decision == "approve": r["provenance"] = dict(source=r["source"], proposed_by="agent", approved_by=reviewer, applied_at=now(), mode="human"); open(FACTS, "a", encoding="utf-8").write(json.dumps(r, ensure_ascii=False) + "\n")
    audit("human_" + decision, pid, actor=reviewer, comment=comment); return r
