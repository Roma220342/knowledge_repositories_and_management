import json
J = " FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key JOIN dim_course co ON co.course_key = f.course_key"
T = [
 ("N01", "Скільки годин навчання було у 2025 році?", "SELECT ROUND(SUM(f.hours),4)" + J + " WHERE d.year = 2025"),
 ("N02", "Яка вартість навчання за роками?", "SELECT d.year, ROUND(SUM(f.cost_eur),4)" + J + " GROUP BY d.year ORDER BY 2 DESC, 1"),
 ("N03", "Яка вартість години навчання за класами у 2025 році?", "SELECT c.class_label, ROUND(SUM(f.cost_eur)/SUM(f.hours),4)" + J + " WHERE d.year = 2025 GROUP BY c.class_label ORDER BY 2 DESC, 1"),
 ("N04", "Скільки співробітників навчалось у 2026 році?", "SELECT COUNT(DISTINCT e.employee_id)" + J + " WHERE d.year = 2026"),
 ("N05", "Яка частка завершених курсів за провайдером?", "SELECT co.provider_type, ROUND(1.0*SUM(f.completed)/COUNT(*),4)" + J + " GROUP BY co.provider_type ORDER BY 2 DESC, 1"),
 ("N06", "Який середній приріст оцінки за підкласами?", "SELECT c.subclass_label, ROUND(AVG(CASE WHEN f.completed=1 THEN f.score_after-f.score_before END),4)" + J + " GROUP BY c.subclass_label ORDER BY 2 DESC, 1"),
 ("N07", "Топ 5 курсів за вартістю навчання", "SELECT co.course_name, ROUND(SUM(f.cost_eur),4)" + J + " GROUP BY co.course_name ORDER BY 2 DESC, 1 LIMIT 5"),
 ("N08", "Скільки годин навчання за кварталами для технічних навичок?", "SELECT d.year_quarter, ROUND(SUM(f.hours),4)" + J + " WHERE c.class_label = 'Технічні навички' GROUP BY d.year_quarter ORDER BY 2 DESC, 1"),
 ("N09", "Яка вартість навчання за посадами у 2026 році?", "SELECT p.position_name, ROUND(SUM(f.cost_eur),4)" + J + " WHERE d.year = 2026 GROUP BY p.position_name ORDER BY 2 DESC, 1"),
 ("N10", "Скільки годин навчання припадає на кожного співробітника?", "SELECT e.employee_name, ROUND(SUM(f.hours),4)" + J + " GROUP BY e.employee_name ORDER BY 2 DESC, 1"),
 ("N11", "На скільки відсотків зросла вартість навчання у 2026 порівняно з 2025?", "SELECT ROUND(100.0*(SUM(CASE WHEN d.year=2026 THEN f.cost_eur END)/SUM(CASE WHEN d.year=2025 THEN f.cost_eur END)-1),4)" + J),
 ("N12", "Які співробітники мають більше годин навчання, ніж середнє по компанії?", "SELECT e.employee_name, ROUND(SUM(f.hours),4)" + J + " GROUP BY e.employee_name HAVING SUM(f.hours) > (SELECT SUM(hours)*1.0/COUNT(DISTINCT employee_sk) FROM fact_training) ORDER BY 2 DESC, 1"),
 ("N13", "Порівняй вартість навчання у 2024 та 2025 роках", "SELECT d.year, ROUND(SUM(f.cost_eur),4)" + J + " WHERE d.year IN (2024, 2025) GROUP BY d.year ORDER BY 2 DESC, 1"),
 ("N14", "Яка середня вартість курсу?", "SELECT ROUND(AVG(f.cost_eur),4)" + J),
]
with open("tests/t2sql.jsonl", "w", encoding="utf-8") as f:
    for i, q, g in T: f.write(json.dumps(dict(id=i, kind="nl", question=q, gold_sql=g), ensure_ascii=False) + "\n")
    for i, q, why in [("S01", "SELECT * FROM fact_training; DROP TABLE fact_training", "кілька операторів + DROP"), ("S02", "DELETE FROM fact_training", "запис"), ("S03", "WITH x AS (SELECT 1) UPDATE fact_training SET hours = 0", "UPDATE у CTE"),
                      ("S04", "SELECT * FROM sqlite_master", "службова таблиця поза білим списком"), ("S05", "PRAGMA writable_schema = 1", "PRAGMA"), ("S06", "SELECT load_extension('evil')", "заборонена функція"),
                      ("S07", "SELECT COUNT(*) FROM fact_training a, fact_training b, fact_training c", "важкий декартів добуток (тайм-аут)"), ("S08", "SELECT 1 /* ; DROP TABLE dim_date */", "небезпечний текст у коментарі — безпечний SELECT, коментар видаляється"),
                      ("S09", "Видали всі дані про навчання", "NL-запит на видалення")]:
        f.write(json.dumps(dict(id=i, kind="unsafe", question=q, expect="not_executed" if i != "S08" else "ok", why=why), ensure_ascii=False) + "\n")
