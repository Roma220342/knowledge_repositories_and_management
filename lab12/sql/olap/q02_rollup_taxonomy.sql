-- Q2 [ROLLUP по таксономії]. Питання: розподіл годин і вартості за ієрархією компетенцій клас -> підклас -> компетенція з підсумками на кожному рівні.
-- Еквівалент DuckDB: GROUP BY ROLLUP (class_label, subclass_label, competence_label).
SELECT * FROM (
WITH b AS (SELECT c.class_label, c.subclass_label, c.competence_label, f.hours, f.cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key)
SELECT class_label, subclass_label, competence_label, ROUND(SUM(hours),1) AS hours, ROUND(SUM(cost_eur),2) AS cost_eur FROM b GROUP BY 1,2,3
UNION ALL SELECT class_label, subclass_label, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2) FROM b GROUP BY 1,2
UNION ALL SELECT class_label, NULL, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2) FROM b GROUP BY 1
UNION ALL SELECT NULL, NULL, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2) FROM b
)
ORDER BY class_label IS NULL, class_label, subclass_label IS NULL, subclass_label, competence_label IS NULL, competence_label;
