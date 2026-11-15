# ЛР 11 — Чат-бот на основі гібридного сховища (RAG + граф), Domain Knowledge Hub (HR)
Python 3.12; seed = 42. Дані: корпус і золотий набір із ЛР 10 (data/, eval/gold_lab10.jsonl), граф із ЛР 9 (graph_data/*.csv).
```
pip install -r requirements.txt              # без faiss/rank_bm25 працюють запасні реалізації з shims/
python eval/make_eval.py                     # eval/rag_eval.jsonl (33 тести) + eval/overlay.jsonl
python eval/graph_vs_text.py                 # Результат 2: текст vs текст+підграф
python eval/api_demo.py                      # Результат 3: демонстрація API (Starlette TestClient)
python eval/run_rag_eval.py --k 3 --tag base # Результат 4: метрики; --k 5 --tag k5 / --rho 0.8 --tag rho08 — Результат 5
python eval/kappa11.py                       # узгодженість авто/ручної оцінки
HUB_API_KEYS='k1:viewer,k2:hr' uvicorn api.main:app --port 8000   # FastAPI (потрібен пакет fastapi)
```
LLM: за замовчуванням офлайн-генератор ExtractiveLLM (без API). Для Claude: `export ANTHROPIC_API_KEY=...` і RAG(llm=AnthropicLLM()). Neo4j: клас Neo4jGraph. Ключі в коді не зберігаються.
