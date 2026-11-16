# ЛР 14 — Якість, очищення та оцінювання сховища знань
Python 3.13; залежності: numpy, scikit-learn, pytest, jsonschema (див. requirements.txt). seed: 14 (дефекти, пари), 42 (RAG з ЛР 11).
    python3 quality/defects.py                 # baseline store_v0 (синтетичні дефекти)
    python3 quality/make_accuracy_sample.py baseline store_v0
    python3 quality/dedup.py eval              # пари, поріг на dev, P/R на test
    python3 quality/dedup.py detect store_v0 baseline && python3 quality/metrics.py store_v0 data/graph_v0 baseline
    python3 quality/resolve.py                 # store_v1, graph_v1, альтернативи, журнал рішень
    python3 quality/dedup.py detect store_v1 after && python3 quality/make_accuracy_sample.py after store_v1 && python3 quality/metrics.py store_v1 data/graph_v1 after
    python3 quality/gate.py after data/store_v1.jsonl data/graph_v1      # gate (код ≠0 при порушеннях)
    python3 quality/demo_defects.py            # 3 навмисні дефекти
    python3 eval/run_rag_eval.py --tag q_base --store store_v0 --repeats 2 && python3 eval/run_rag_eval.py --tag q_after --store store_v1 --repeats 2 && python3 quality/rag_compare.py
