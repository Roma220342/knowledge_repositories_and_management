"""Результат 2: порівняння «лише текст» vs «текст + підграф» на 12 питаннях про зв'язки/залежності. Еталон обчислюється з графа ЛР 9 (CSV) незалежно від конвеєра."""
import sys, os, json, numpy as np; sys.path.insert(0, "src")
from rag import RAG, ID_RE, ABSTAIN
from graph_context import Graph
G = Graph(); nm = lambda i: G.nodes[i]["name"]
def tgt(a, t): return [nm(e[2]) for e in G.out.get(a, []) if e[1] == t]
def src(b, t): return [nm(e[0]) for e in G.inn.get(b, []) if e[1] == t]
Q = []
for emp, gen in [("petro", "Петра Бондаря"), ("andriy", "Андрія Мельника"), ("emp007", "Тараса Гнатюка"), ("ivan", "Івана Шевчука")]:
    Q.append((f"Хто безпосередній керівник {gen}?", tgt(emp, "DIRECT_MANAGER"), "керівник"))
for pos, n in [("pythonDeveloperPost", "Python-розробник"), ("hrManagerPost", "HR-менеджер"), ("recruiterPost", "Рекрутер"), ("teamLeadPost", "Керівник команди")]:
    Q.append((f"Які компетенції потрібні для посади {n}?", tgt(pos, "REQUIRES_COMPETENCE"), "залежність"))
for comp, n in [("negotiation", "переговори"), ("teamCommunication", "командна комунікація")]:
    Q.append((f"Які посади вимагають компетенцію {n}?", src(comp, "REQUIRES_COMPETENCE"), "залежність"))
Q.append(("Які курси завершив Андрій Мельник?", tgt("andriy", "COMPLETED_COURSE"), "зв'язок"))
Q.append(("Яку посаду займає Петро Бондар?", tgt("petro", "OCCUPIES"), "зв'язок"))
assert all(g for _, g, _ in Q), "порожній еталон"
rag = RAG(role="admin", k=3, log_path=None, graph=G)
rows = []
for q, gold, kind in Q:
    r = {}
    for mode in ("text", "graph"):
        x = rag.ask(q, use_graph=(mode == "graph"))
        ans = x["answer"]; ok = ans != ABSTAIN and all(g.lower() in ans.lower() for g in gold)
        cit = [c for c in ID_RE.findall(ans)]; gcit = [c for c in cit if c.startswith("n:")]
        r[mode] = dict(correct=ok, abstain=ans == ABSTAIN, cited=len(cit), graph_cited=len(gcit), ptok=x["prompt_tokens"], ctok=x["completion_tokens"], ans=ans)
    rows.append(dict(q=q, kind=kind, gold=gold, **r))
def agg(m): 
    R = [r[m] for r in rows]
    return dict(correct=sum(x["correct"] for x in R), n=len(R), acc=round(float(np.mean([x["correct"] for x in R])), 3), abstain=sum(x["abstain"] for x in R),
                explain=round(float(np.mean([x["cited"] > 0 for x in R])), 3), graph_cited=round(float(np.mean([x["graph_cited"] > 0 for x in R])), 3),
                noise=round(float(np.mean([x['cited'] - x['graph_cited'] for x in R])), 2), ptok=round(float(np.mean([x["ptok"] for x in R])), 1), ctok=round(float(np.mean([x["ctok"] for x in R])), 1))
out = dict(text=agg("text"), graph=agg("graph"), rows=rows, linking=[dict(q=q, **G.info(q)) for q, _, _ in Q])
json.dump(out, open("results/graph_vs_text.json", "w"), indent=1, ensure_ascii=False)
print(out["text"]); print(out["graph"])
for r in rows: print(r["q"], r["gold"], "| T:", r["text"]["correct"], "| G:", r["graph"]["correct"], r["graph"]["ans"][:90])
