# ЛР 13 — Видобування знань із текстів
seed 13, Python 3.13, лише стандартна бібліотека.
    python3 src/make_corpus.py
    python3 src/extract_rules.py --split dev && python3 src/extract_rules.py --split test
    python3 llm_log/make_raw_test.py && python3 src/extract_llm.py --split test --backend replay   # або --backend anthropic (ANTHROPIC_API_KEY у середовищі)
    python3 src/evaluate.py results/pred_rules_test_v1.jsonl --split test
    python3 src/graph_patterns.py
    python3 src/kappa.py   # після заповнення data/annot2_template.csv
