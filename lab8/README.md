# ЛР 8. RDF-сховище та SPARQL-запити

Потрібен Python 3.10+ та інтернет (Wikidata). Дані ЛР 7 беруться з `../ЛР7_артефакти/models/`. Seed = 42.

```bash
cd ЛР8_артефакти
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_all.py
```

Окремі кроки: `scripts/r1_build_kb.py` (дані й сховище), `r5_links.py` (Wikidata), `r2_queries.py` (SPARQL),
`r3_shacl.py` (SHACL), `r4_t2s.py` (text-to-SPARQL).

| Результат | Артефакти |
|---|---|
| 1 | data/kb.ttl, data/kb.jsonld, docs/load_log.md |
| 2 | queries/*.rq, docs/sparql_results.md |
| 3 | shapes/shapes.ttl, docs/shacl_report.md |
| 4 | tests/t2s*.jsonl, docs/t2s_eval.md |
| 5 | data/links.ttl, docs/links_verification.md |
| LLM | llm_log/llm_log.md, claims/claims.csv |

Ключі API не використовуються.
