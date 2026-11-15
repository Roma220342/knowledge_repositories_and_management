-- Q5 [GROUPING SETS]. Питання: вартість навчання за (рік, клас), лише за класом і загальна — без зайвих комбінацій.
-- Еквівалент DuckDB: GROUP BY GROUPING SETS ((year, class_label), (class_label), ()).
SELECT * FROM (
WITH b AS (SELECT d.year, c.class_label, f.cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key)
SELECT year, class_label, ROUND(SUM(cost_eur),2) AS cost_eur FROM b GROUP BY 1,2
UNION ALL SELECT NULL, class_label, ROUND(SUM(cost_eur),2) FROM b GROUP BY 2
UNION ALL SELECT NULL, NULL, ROUND(SUM(cost_eur),2) FROM b
)
ORDER BY class_label IS NULL, class_label, year IS NULL, year;
