"""Прогін сценаріїв через MCP-агента. python3 tests/run_scenarios.py <мітка>  → results/scenarios_<мітка>.json"""
import asyncio, sys, os, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT + "/agent", ROOT]
from agent import Agent
def judge(sc, r):
    a = r["answer"]; al = a.lower(); tools = [t.get("tool") for t in r["trace"] if t["node"] == "retrieve" and "tool" in t]; why = []
    if sc["kind"] == "abstain":
        if not a.startswith("Не знаю"): why.append("мало бути «Не знаю»")
    else:
        why += [f"немає «{m}»" for m in sc["must_contain"] if m.lower() not in al]; why += [f"є заборонене «{m}»" for m in sc["must_not_contain"] if m.lower() in al]; why += [f"немає цитати {c}" for c in sc["must_cite"] if c not in r["cited"] and c not in a]
        if a.startswith("Не знаю"): why.append("хибне «Не знаю»")
    why += [f"не викликано {t}" for t in sc["expect_tools"] if t not in tools]
    if r["steps"] > 6: why.append("забагато кроків")
    return not why, why, tools
async def main(label):
    sc = [json.loads(l) for l in open(ROOT + "/tests/agent_scenarios.jsonl", encoding="utf-8")]; out = []; a = Agent(secure=True, role="employee", trace=f"logs/trace_{label}.jsonl", label=label)
    if os.path.exists(a.trace_path): os.remove(a.trace_path)
    async with a.connect():
        for s in sc:
            r = await a.run(s["question"]); ok, why, tools = judge(s, r); out.append(dict(id=s["id"], kind=s["kind"], ok=ok, why=why, tools=tools, steps=r["steps"], tokens=r["tokens_prompt"] + r["tokens_completion"], cost=r["cost_usd"], ms=r["latency_ms"], answer=r["answer"][:300]))
    n = len(out); summ = dict(label=label, n=n, success_rate=round(sum(o["ok"] for o in out) / n, 3), avg_steps=round(sum(o["steps"] for o in out) / n, 2), avg_cost_usd=round(sum(o["cost"] for o in out) / n, 6), avg_ms=round(sum(o["ms"] for o in out) / n, 1), by_kind={k: f"{sum(o['ok'] for o in out if o['kind']==k)}/{sum(o['kind']==k for o in out)}" for k in ("success", "abstain", "conflict")})
    json.dump(dict(summary=summ, rows=out), open(f"{ROOT}/results/scenarios_{label}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(summ)
    for o in out:
        if not o["ok"]: print(o["id"], o["why"], "|", o["answer"][:160])
asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "run"))
