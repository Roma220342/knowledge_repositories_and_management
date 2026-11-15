# Оцінювання RAG (базова конфігурація k=3, ρ=0.6)
```json
{
 "k": 3,
 "rho": 0.6,
 "n": 33,
 "thr": 0.2221,
 "faithfulness": 1.0,
 "context_recall": 0.925,
 "citation_accuracy": 0.675,
 "abstention_rate_noanswer": 0.875,
 "false_abstain_answerable": 0.062,
 "answer_hit_rate": 0.812,
 "conflict_flagged": 1.0,
 "injection_safe": 1.0,
 "invalid_citations": 0,
 "p50_ms": 5.29,
 "p95_ms": 5.43,
 "prompt_tokens": 511.8,
 "completion_tokens": 43.3,
 "cost_per_query_usd": 0.002186,
 "price_assumption": [
  3.0,
  15.0
 ]
}
```
Показники за тестами — results/rag_eval_base.json; ручні мітки — eval/manual_labels.csv; κ — results/kappa11.json.
