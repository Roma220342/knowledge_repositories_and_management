"""До/після для RAG (ЛР 11 → ЛР 14): основні метрики + 2 додаткові, що відображають вплив якості: частка застарілих значень у відповідях на конфліктні питання і частка дублікатів у контексті."""
import json, sys
B = json.load(open("results/rag_eval_q_base.json")); A = json.load(open("results/rag_eval_q_after.json")); STALE = ["три місяці", "1500", "трьох днів"]
def extra(rs):
    conf = [r for r in rs["rows"] if r["cat"] == "conflict"]; stale = sum(any(s in r["answer"] for s in STALE) for r in conf)
    srcs = [s for r in rs["rows"] if r["cat"] in ("answer", "conflict") for s in r["sources"]]; dup = sum(s.startswith("DUP-") for s in srcs)
    return dict(stale_answers=f"{stale}/{len(conf)}", dup_context_share=round(dup / max(1, len(srcs)), 3), n_ctx=len(srcs))
out = dict(before=dict(B["summary"], **extra(B)), after=dict(A["summary"], **extra(A))); json.dump(out, open("results/rag_compare.json", "w"), ensure_ascii=False, indent=1)
for k in ["faithfulness", "context_recall", "citation_accuracy", "abstention_rate_noanswer", "false_abstain_answerable", "answer_hit_rate", "conflict_flagged", "injection_safe", "stale_answers", "dup_context_share", "prompt_tokens"]: print(k, out["before"][k], "→", out["after"][k])
for r in A["rows"]:
    if r["cat"] == "conflict": print(r["id"], r["answer"][:200])
