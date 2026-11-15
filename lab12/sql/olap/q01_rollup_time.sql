-- Q1 [ROLLUP за часом]. Питання: скільки годин і коштів витрачено на навчання за роками та кварталами, з проміжними та загальним підсумком?
-- Еквівалент DuckDB: GROUP BY ROLLUP (year, quarter). Тут розгорнуто через UNION ALL (SQLite не підтримує ROLLUP).
SELECT * FROM (
WITH b AS (SELECT d.year, d.quarter, f.hours, f.cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key)
SELECT year, quarter, ROUND(SUM(hours),1) AS hours, ROUND(SUM(cost_eur),2) AS cost_eur, COUNT(*) AS events FROM b GROUP BY year, quarter
UNION ALL SELECT year, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2), COUNT(*) FROM b GROUP BY year
UNION ALL SELECT NULL, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2), COUNT(*) FROM b
)
ORDER BY year IS NULL, year, quarter IS NULL, quarter;
