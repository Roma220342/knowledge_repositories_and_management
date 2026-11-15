-- Q12 [напівадитивна міра]. Питання: яка чисельність співробітників у знімках кварталів 2025 року? Headcount не можна сумувати за часом — для року беремо останній знімок, а не суму.
WITH q AS (SELECT d.year, d.year_quarter, SUM(h.headcount) AS hc FROM fact_perf_quarter h JOIN dim_date d ON d.date_key = h.date_key WHERE d.year = 2025 GROUP BY d.year, d.year_quarter)
SELECT year_quarter, hc AS headcount, (SELECT SUM(hc) FROM q) AS wrong_sum_over_time, (SELECT hc FROM q ORDER BY year_quarter DESC LIMIT 1) AS correct_year_value FROM q ORDER BY year_quarter;
