-- Q10 [віконна: ранг]. Питання: хто з співробітників проводить найбільше годин на навчанні в межах своєї посади (топ-3 за посадою)?
WITH t AS (SELECT p.position_name, e.employee_name, ROUND(SUM(f.hours),1) AS hours FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY p.position_name, e.employee_id, e.employee_name),
r AS (SELECT *, RANK() OVER (PARTITION BY position_name ORDER BY hours DESC) AS rnk FROM t)
SELECT position_name, rnk, employee_name, hours FROM r WHERE rnk <= 3 ORDER BY position_name, rnk, employee_name;
