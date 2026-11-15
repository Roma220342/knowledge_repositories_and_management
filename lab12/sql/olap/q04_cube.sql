-- Q4 [CUBE]. Питання: години навчання за посадою та класом компетенцій з усіма проміжними підсумками (посада, клас, обидва, загальний).
-- Еквівалент DuckDB: GROUP BY CUBE (position_name, class_label).
SELECT * FROM (
WITH b AS (SELECT p.position_name, c.class_label, f.hours FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key)
SELECT position_name, class_label, ROUND(SUM(hours),1) AS hours FROM b GROUP BY 1,2
UNION ALL SELECT position_name, NULL, ROUND(SUM(hours),1) FROM b GROUP BY 1
UNION ALL SELECT NULL, class_label, ROUND(SUM(hours),1) FROM b GROUP BY 2
UNION ALL SELECT NULL, NULL, ROUND(SUM(hours),1) FROM b
)
ORDER BY position_name IS NULL, position_name, class_label IS NULL, class_label;
