-- Q8 [pivot]. Питання: години навчання за кварталами (рядки) та класами компетенцій (стовпці) для швидкого порівняння.
-- Еквівалент DuckDB: PIVOT ... ON class_label USING SUM(hours). Тут умовна агрегація (працює в обох СУБД).
SELECT d.year_quarter, ROUND(SUM(CASE WHEN c.class_label = 'Технічні навички' THEN f.hours ELSE 0 END),1) AS hard_hours,
       ROUND(SUM(CASE WHEN c.class_label = 'М''які навички' THEN f.hours ELSE 0 END),1) AS soft_hours, ROUND(SUM(f.hours),1) AS total_hours FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY d.year_quarter ORDER BY d.year_quarter;
