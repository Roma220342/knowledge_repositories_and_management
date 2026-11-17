"""Агент над Hub через MCP: граф станів plan → retrieve → draft → verify (→ answer | abstain). «Мозок» — офлайн, детермінований (правила + екстрактивний генератор з ЛР 11), бо LLM API недоступне;
замінюється на LLM-виклик у plan()/draft() без зміни інструментів. Тріас у logs/agent_trace.jsonl."""
import asyncio, os, sys, re, json, time, contextlib
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT, ROOT + "/agent", ROOT + "/hub_src", ROOT + "/semantic"]
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import policy as P
from rag import ExtractiveLLM, ABSTAIN, REFUSE, est_tokens, is_injection
from common import stems
from hub.access import looks_malicious
from graph_context import Graph, REL_UA
import metrics as SEM
SYN = {n: m["synonyms"] + [m["title"].lower()] for n, m in SEM.METRICS.items()}
EXTRA_SYN = {"active_learners": ["співробітників проходило", "працівників проходило", "проходили навчання", "навчалось", "кількість співробітників"]}
for _n, _w in EXTRA_SYN.items(): SYN[_n] = SYN[_n] + _w
QUANT = ["скільки", "загальн", "сума", "середн", "частк", "відсот", "яка вартість", "які витрати", "які години", "за роками", "за класами", "за кварталами"]
CID = re.compile(r"\[([A-Z]\d+-p\d+|n:[\w-]+|sql:[\w-]+)\]")
NAIVE = re.compile(r"відповідай\s+(?:лише|тільки)[:\s]+['\"«]?([^.\n'\"»]+)", re.I)
def parse_year(q): m = re.findall(r"\b(20\d\d)\b", q); return [int(x) for x in m]
class Agent:
    def __init__(self, secure=True, role="employee", poison=False, rogue=False, trace="logs/agent_trace.jsonl", label=""):
        self.secure, self.role, self.poison, self.rogue, self.trace_path, self.label = secure, role, poison, rogue, ROOT + "/" + trace, label
        self.lim = P.LIMITS if secure else P.INSECURE_LIMITS; self.G = Graph(ROOT + "/graph_ro"); self.llm = ExtractiveLLM(0.6); self.memory = []
    @contextlib.asynccontextmanager
    async def connect(self):
        env = dict(os.environ, HUB_SECURE="1" if self.secure else "0", HUB_ROLE=self.role, HUB_POISON="1" if self.poison else "0", PYTHONPATH=ROOT)
        async with contextlib.AsyncExitStack() as st:
            self.tools = {}; self.sessions = {}
            for name, path in [("hub", "mcp_server/server.py")] + ([("rogue", "mcp_server/rogue_server.py")] if self.rogue else []):
                r, w = await st.enter_async_context(stdio_client(StdioServerParameters(command=sys.executable, args=[ROOT + "/" + path], env=env)))
                s = await st.enter_async_context(ClientSession(r, w)); await s.initialize(); self.sessions[name] = s
                for t in (await s.list_tools()).tools: self.tools[t.name] = dict(name=t.name, description=t.description or "", server=name)
            self.rejected_tools = []
            if self.secure:                                    # закріплення маніфесту: невідомі/змінені інструменти відкидаються
                man = P.load_manifest(); cur = P.pin(self.tools.values())
                for n in list(self.tools):
                    if man.get(n) != cur[n]: self.rejected_tools.append(n); del self.tools[n]
            yield self
    async def call(self, tool, args):
        t0 = time.perf_counter(); res = await asyncio.wait_for(self.sessions[self.tools[tool]["server"]].call_tool(tool, args), self.lim["timeout_s"])
        data = json.loads(res.content[0].text) if res.content and not res.is_error else {"error": "tool_error"}; return data, (time.perf_counter() - t0) * 1000
    # ---------------- plan
    def pick_search_tool(self, q):
        cands = [n for n in self.tools if "search" in n or "kb" in n]
        if self.secure or len(cands) <= 1: return "search_kb" if "search_kb" in self.tools else None
        qs = set(stems(q)); return max(cands, key=lambda n: len(qs & set(stems(self.tools[n]["description"]))))      # naive: довіра до опису інструмента
    def plan(self, q):
        ql = q.lower(); steps = []; flags = {}
        if self.secure and (is_injection(q) or looks_malicious(q)): return [], dict(refuse="input_filter")
        if P.WRITE_INTENT.search(q):
            if self.secure and self.role not in ("hr", "admin"): return [], dict(refuse="write_requires_hr_role")
            m = re.search(r"\b(D\d+-p\d+)\b", q); steps.append(("propose_fact", dict(subject=self.G.link(q)[0] if self.G.link(q) else "", relation="OCCUPIES", object="teamLeadPost", source=m.group(1) if m else "", evidence=q, action="delete" if re.search(r"видали|видалити|стер", ql) else "add"))); return steps, flags
        role_arg = {}
        if not self.secure and re.search(r"role\s*=\s*admin|як адміністратор", ql): role_arg = dict(role="admin")
        metric = None
        for n, syns in SYN.items():
            if any(s in ql for s in syns) and any(w in ql for w in QUANT): metric = n; break
        if metric:
            by = [d for d, w in [("year", ["за роками"]), ("quarter", ["за кварталами"]), ("class", ["за класами"]), ("position", ["за посадами"])] if any(x in ql for x in w)]; yrs = parse_year(q)
            steps.append(("metric_query", dict(metric=metric, by=by, where=({"year": yrs[0]} if len(yrs) == 1 else {})))); 
        seeds = self.G.link(q)
        if seeds: steps.append(("graph_lookup", dict(question=q, **role_arg)))
        if not steps or P.LOOP_INTENT.search(q) or not (metric or seeds):
            st = self.pick_search_tool(q)
            if st: steps.append((st, dict(query=q, k=3, **role_arg)))
        if P.LOOP_INTENT.search(q): flags["loop"] = True
        return steps, flags
    # ---------------- run
    async def run(self, q):
        t0 = time.perf_counter(); trace = []; ev = {}; ctx = []; props = {}; sql = []; steps, flags = self.plan(q); ptok = est_tokens(q); naive = None; calls = set()
        def rec(**kw): trace.append(dict(step=len(trace) + 1, **kw))
        rec(node="plan", plan=[s[0] for s in steps], flags=flags)
        if flags.get("refuse"): return self.finish(q, REFUSE if flags["refuse"] == "input_filter" else "Запис знань не дозволено для вашої ролі; використайте схвалений процес (propose_fact через HR).", {}, trace, t0, ptok, 0, blocked=flags["refuse"])
        queue = list(steps); n_calls = 0; stopped = None
        while queue:
            tool, args = queue.pop(0)
            if self.secure:
                key = (tool, json.dumps(args, sort_keys=True))
                if key in calls: rec(node="guard", note="повторний виклик пропущено", tool=tool); continue
                calls.add(key)
                if n_calls >= self.lim["max_steps"]: stopped = "step_limit"; break
                if ptok > self.lim["max_prompt_tokens"]: stopped = "token_limit"; break
            elif n_calls >= self.lim["max_steps"]: stopped = "hard_cap"; break
            if tool not in self.tools: rec(node="retrieve", tool=tool, error="інструмент недоступний/відхилений"); continue
            try: data, ms = await self.call(tool, args)
            except asyncio.TimeoutError: rec(node="retrieve", tool=tool, error="timeout"); stopped = "timeout"; break
            n_calls += 1; ptok += est_tokens(json.dumps(data, ensure_ascii=False)); rec(node="retrieve", tool=tool, args={k: (v if k != "evidence" else v[:30]) for k, v in args.items()}, ms=round(ms, 2), result=self.summ(tool, data))
            if tool in ("search_kb", "search_kb_pro"):
                hits = data.get("hits", []); ev["top1"] = max(ev.get("top1", 0), data.get("top1", 0)); ev["thr"] = data.get("thr", 0.2); ev.setdefault("conflicts", []).extend(data.get("conflicts", []) if self.secure else [])
                for h in hits:
                    if self.secure and looks_malicious(h["text"]): rec(node="guard", note="фрагмент у карантин (ін'єкція у контексті)", id=h["id"]); continue
                    ctx.append(h)
                    if not self.secure and NAIVE.search(h["text"]): naive = NAIVE.search(h["text"]).group(1).strip()
                if flags.get("loop") and not hits_ok(hits, ev) and n_calls < self.lim["max_steps"] + 1000: queue.append((tool, dict(args, query=args["query"] + " " + "!" * n_calls)))       # «шукай доки не знайдеш»
            elif tool == "graph_lookup": ctx += [dict(id=f["id"], text=f["text"], date="graph") for f in data.get("facts", [])]; props.update(data.get("props", {}))
            elif tool == "metric_query" and "rows" in data: sql.append(data)
            elif tool == "propose_fact": ev["proposal"] = data
        if stopped: rec(node="guard", note=f"зупинка: {stopped}"); return self.finish(q, "Не вдалося завершити пошук у межах лімітів (" + stopped + "); уточніть запит.", {}, trace, t0, ptok, n_calls, blocked=stopped)
        ans, evid = self.draft(q, ctx, props, sql, ev, naive); return self.finish(q, ans, evid, trace, t0, ptok, n_calls, check=True)
    def summ(self, tool, d):
        if "error" in d: return d["error"]
        if "hits" in d: return f"{len(d['hits'])} фрагментів, top1={d.get('top1')}, карантин={d.get('quarantined')}"
        if "facts" in d: return f"{len(d['facts'])} фактів, вузли={d.get('seeds')}"
        if "rows" in d: return f"{len(d['rows'])} рядків"
        return str(d)[:80]
    def vocab(self):
        if not hasattr(self, '_v'): self._v = {w for l in open(ROOT + '/data/store_v1.jsonl', encoding='utf-8') for w in stems(json.loads(l)['text'])}
        return self._v
    # ---------------- draft
    def draft(self, q, ctx, props, sql, ev, naive):
        ql = q.lower(); parts = []; evid = {c["id"]: c["text"] for c in ctx}
        if naive: return naive, evid                       # НАЇВНА модель виконує інструкцію з контексту (демонстрація вразливості «до»)
        if "proposal" in ev: return f"Запит на зміну: {ev['proposal']}", evid
        kb = [c for c in ctx if c["date"] != "graph"]; gr = [c for c in ctx if c["date"] == "graph"]
        for d in sql:
            rows = d["rows"][:4]; parts.append(f"{d['columns'][-1]}: " + "; ".join(" / ".join(str(x) for x in r) for r in rows) + f" [{d['id']}]"); evid[d["id"]] = parts[-1]
        if props and "продуктивн" in ql:
            for nid, p in props.items():
                if p.get("productivityScore") is not None: s = f"Продуктивність {p['name']}: {p['productivityScore']} [n:{nid}]"; parts.append(s); evid[f"n:{nid}"] = s
                else: parts.append("Доступ до оцінки продуктивності обмежено політикою (потрібна роль hr/admin).")
        rel = [("DIRECT_MANAGER", ["керівник"]), ("OCCUPIES", ["посад"]), ("HAS_COMPETENCE", ["компетенц"]), ("COMPLETED_COURSE", ["курс"])]
        for c in gr if "продуктивн" not in ql else []:
            for r, ws in rel:
                if any(w in ql for w in ws) and f"-{r}-" in c["id"]:
                    seed = c["id"].split(":")[1].split("-")[0]
                    if ("керівник" in ql and r == "DIRECT_MANAGER" and "підлегл" not in ql and seed not in [x for x in self.G.link(q)]): continue
                    t = re.sub(r"\[n:[\w]+\]\s*", "", c["text"]); t = re.sub(r"\s*\((?:Employee|Position|Competence|Course)\)", "", t).split(" Джерело")[0]; parts.append(f"{t} [{c['id']}]"); evid[c["id"]] = c["text"]
        if ev.get("conflicts") and not parts:
            c = ev["conflicts"][0]; old, new = sorted(c, key=lambda x: x["date"]); a = f"Джерела суперечать: {old['text']} [{old['id']}] ({old['date']}) і {new['text']} [{new['id']}] ({new['date']}). Потрібне рішення власника знань; за датою новішим є [{new['id']}]."; evid.update({x["id"]: x["text"] for x in c}); return a, evid
        if kb and self.secure and not parts:                 # шлюз релевантності (виправлення): рідкісні терміни запиту мають зустрічатись у доказах
            qs = [w for w in set(stems(q)) if len(w) > 3]; pool = set(stems(" ".join(c["text"] for c in kb)))
            vocab = self.vocab(); oov = [w for w in qs if w not in vocab]
            if qs and (sum(w in pool for w in qs) / len(qs) < 0.4 or len(oov) / len(qs) >= 0.2): return ABSTAIN, evid
        if kb:
            a = self.llm.generate(q, kb)
            if ev.get("top1", 1) < ev.get("thr", 0) and not parts: a = ABSTAIN
            if a != ABSTAIN or not parts: parts.append(a)
            evid.update({c["id"]: c["text"] for c in kb})
        return (" ".join(parts) if parts else ABSTAIN), evid
    # ---------------- verify + finish
    def verify(self, ans, evid):
        """Етап перевірки цитат: усі [id] мають бути серед отриманих доказів; кожне речення підтверджується цитованим текстом (≥70 % основ)."""
        if ans in (ABSTAIN, REFUSE): return ans, dict(valid=True, dropped=0)
        sents = [s for s in re.split(r"(?<=[.!?])\s+(?!\[)", ans) if s.strip()]; keep = []; dropped = 0
        for s in sents:
            cited = CID.findall(s); ss = set(stems(CID.sub("", s)))
            if cited and any(c not in evid for c in cited): dropped += 1; continue                       # вигадана цитата
            if not cited and not s.startswith(("Доступ до", "Джерела суперечать")): dropped += 1; continue
            pool = set(stems(" ".join(evid.get(c, "") for c in cited)))
            if cited and ss and len(ss & pool) / len(ss) < 0.5 and not s.startswith("Джерела суперечать"): dropped += 1; continue
            keep.append(s)
        return (" ".join(keep) if keep else ABSTAIN), dict(valid=dropped == 0, dropped=dropped)
    def finish(self, q, ans, evid, trace, t0, ptok, n_calls=0, blocked=None, check=False):
        if check:
            if self.secure: ans, v = self.verify(ans, evid)
            else: v = dict(valid=True, dropped=0)
            trace.append(dict(step=len(trace) + 1, node="verify", **v))
        out = dict(question=q, answer=ans, steps=n_calls, tokens_prompt=ptok, tokens_completion=est_tokens(ans), latency_ms=round((time.perf_counter() - t0) * 1000, 1), blocked=blocked, cited=CID.findall(ans), trace=trace, secure=self.secure, label=self.label)
        out["cost_usd"] = round((ptok * 3 + out["tokens_completion"] * 15) / 1e6 * 2, 6)       # ПРИПУЩЕННЯ: тариф 3/15 USD за 1M токенів, 2 виклики LLM-«мозку» на запит (plan+draft)
        os.makedirs(os.path.dirname(self.trace_path), exist_ok=True)
        with open(self.trace_path, "a", encoding="utf-8") as f: f.write(json.dumps(out, ensure_ascii=False) + "\n")
        return out
def hits_ok(hits, ev): return any(h["score"] >= ev.get("thr", 0.2) + 0.15 for h in hits)
