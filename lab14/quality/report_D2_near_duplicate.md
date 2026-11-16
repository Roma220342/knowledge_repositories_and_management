# Звіт перевірок: D2_near_duplicate
Пройдено 14, провалено 1

| перевірка | інструмент | статус |
|--|--|--|
| test_01_record_json_schema | JSON Schema | ✅ |
| test_02_unique_ids | pytest | ✅ |
| test_03_completeness | pytest | ✅ |
| test_04_valid_dates | pytest | ✅ |
| test_05_provenance | pytest | ✅ |
| test_06_terminology | pytest | ✅ |
| test_07_restricted_not_public | pytest | ✅ |
| test_08_no_near_duplicates | pytest | ❌ |
| test_09_no_unresolved_value_conflicts | pytest | ✅ |
| test_10_sql_id_prefix_matches_doc | SQL (SQLite) | ✅ |
| test_11_sql_no_future_dates | SQL (SQLite) | ✅ |
| test_12_sql_unique_id | SQL (SQLite) | ✅ |
| test_13_occupies_is_functional | graph invariants | ✅ |
| test_14_manager_hierarchy_acyclic | graph invariants | ✅ |
| test_15_no_dangling_edges | graph invariants | ✅ |
