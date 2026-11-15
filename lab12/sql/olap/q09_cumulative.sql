-- Q9 [віконна: накопичення]. Питання: як зростають сукупні витрати на навчання помісячно, і яку частку річного бюджету складають за 2025 рік?
WITH m AS (SELECT d.year, d.year_month, SUM(f.cost_eur) AS cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY d.year, d.year_month)
SELECT year_month, ROUND(cost_eur,2) AS cost_eur, ROUND(SUM(cost_eur) OVER (PARTITION BY year ORDER BY year_month),2) AS ytd_cost,
       ROUND(100.0 * SUM(cost_eur) OVER (PARTITION BY year ORDER BY year_month) / SUM(cost_eur) OVER (PARTITION BY year), 1) AS ytd_share_pct
FROM m WHERE year = 2025 ORDER BY year_month;
