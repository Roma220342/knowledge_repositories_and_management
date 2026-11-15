# Семантичний шар
semantic/metrics.yml: 7 метрик (name, title, definition, formula, expr, unit, additivity, owner, sources, constraints, status, reviewed_on, synonyms). Генератор SQL: semantic/metrics.py::sql_for. Узгодженість: semantic/check_consistency.py — 9 перевірок різними шляхами (метрика vs Q1/Q2/Q6/pandas), all_ok=True. Метрика hours_per_learner має статус draft.
