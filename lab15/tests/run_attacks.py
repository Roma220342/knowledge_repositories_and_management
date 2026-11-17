"""Red teaming: python3 tests/run_attacks.py before|after  (before = secure=False, after = secure=True)"""
import asyncio, sys, os, json, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT + "/agent", ROOT]
from agent import Agent
def success(a, r):
    s = a["success_if"]; ans = r["answer"]; tools = [t.get("tool") for t in r["trace"] if t["node"] == "retrieve"]
    return {"contains": lambda: s["value"] in ans, "regex": lambda: bool(re.search(s["value"], ans)), "steps_gt": lambda: r["steps"] > s["value"], "tool_called": lambda: s["value"] in tools}[s["type"]]()
async def main(mode):
    sec = mode == "after"; out = []
    for l in open(ROOT + "/tests/attacks.jsonl", encoding="utf-8"):
        a = json.loads(l); ag = Agent(secure=sec, role=a["role"], poison=a["poison"], rogue=a["rogue"], trace=f"logs/attack_{mode}.jsonl", label=a["id"])
        async with ag.connect():
            r = await ag.run(a["prompt"])
        ok = success(a, r); out.append(dict(id=a["id"], type=a["type"], attack_succeeded=ok, blocked_by=r["blocked"] or ([n for n in ag.rejected_tools] and "tool_pinning") or ("verify/quarantine" if not ok else None), steps=r["steps"], answer=r["answer"][:140], rejected_tools=ag.rejected_tools))
    n = len(out); summ = dict(mode=mode, n=n, succeeded=sum(o["attack_succeeded"] for o in out), blocked_share=round(1 - sum(o["attack_succeeded"] for o in out) / n, 3))
    json.dump(dict(summary=summ, rows=out), open(f"{ROOT}/results/attacks_{mode}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(summ)
    for o in out: print(o["id"], o["type"], "УСПІХ атаки" if o["attack_succeeded"] else "заблоковано", o["steps"], o["answer"][:90])
if os.path.exists(ROOT + f"/logs/attack_{sys.argv[1]}.jsonl"): os.remove(ROOT + f"/logs/attack_{sys.argv[1]}.jsonl")
asyncio.run(main(sys.argv[1]))
