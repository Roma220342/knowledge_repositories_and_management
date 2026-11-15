# ЛР 10 — Векторне сховище та семантичний пошук (Domain Knowledge Hub, HR)
Python 3.12; numpy, scipy, scikit-learn, faiss-cpu, rank_bm25, matplotlib (pip install -r requirements.txt). seed = 42 (src/common.py).
```
python src/build_corpus.py     # Результат 1: kb/*.md -> очищення -> data/corpus.jsonl
python src/run_chunking.py     # Результат 2: results/chunking.json
python src/run_index.py        # Результат 3: results/index.json (HNSW, embeddings, upsert/delete)
python src/run_hybrid_demo.py  # Результат 4: pre-filter -> results/prefilter.json
python eval/run_eval.py        # Результат 4–5: results/eval.json
python eval/kappa.py           # κ (розмітник B = автоматичне правило; --human для людської розмітки)
python src/make_figs.py && python src/make_support.py
```
Для e5/cross-encoder (потрібен доступ до HuggingFace): `pip install sentence-transformers`, у src/index.py використайте `STEmbedder('intfloat/multilingual-e5-base')`, у src/hybrid.py замініть `rerank()` на `CrossEncoder(...).predict`. Ключі API не використовуються.
