# Результати OLAP-запитів

## q01_rollup_time.sql
**Питання:** див. коментар у файлі.
```sql
-- Q1 [ROLLUP за часом]. Питання: скільки годин і коштів витрачено на навчання за роками та кварталами, з проміжними та загальним підсумком?
-- Еквівалент DuckDB: GROUP BY ROLLUP (year, quarter). Тут розгорнуто через UNION ALL (SQLite не підтримує ROLLUP).
SELECT * FROM (
WITH b AS (SELECT d.year, d.quarter, f.hours, f.cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key)
SELECT year, quarter, ROUND(SUM(hours),1) AS hours, ROUND(SUM(cost_eur),2) AS cost_eur, COUNT(*) AS events FROM b GROUP BY year, quarter
UNION ALL SELECT year, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2), COUNT(*) FROM b GROUP BY year
UNION ALL SELECT NULL, NULL, ROUND(SUM(hours),1), ROUND(SUM(cost_eur),2), COUNT(*) FROM b
)
ORDER BY year IS NULL, year, quarter IS NULL, quarter;

```

  year  quarter  hours  cost_eur  events
2024.0      1.0 2444.0  79916.20     146
2024.0      2.0 2373.0  82273.28     141
2024.0      3.0 2612.0  94516.18     148
2024.0      4.0 2403.0  81550.21     135
2024.0      NaN 9832.0 338255.87     570
2025.0      1.0 2976.0 104880.56     161
2025.0      2.0 2262.0  77769.90     137
2025.0      3.0 3221.0 115119.29     180

**Інтерпретація:** Витрати і години зростають за роками; ROLLUP дає підсумки по роках і загальний рядок (32066 год, 1 114 344,57 €).

## q02_rollup_taxonomy.sql
**Питання:** див. коментар у файлі.
```sql
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

```

  class_label subclass_label    competence_label  hours  cost_eur
М'які навички    Комунікація Conflict resolution 1490.0  70342.28
М'які навички    Комунікація         Negotiation 2920.0  55233.88
М'які навички    Комунікація  Team communication 2418.0  44973.02
М'які навички    Комунікація                 NaN 6828.0 170549.18
М'які навички      Лідерство            Coaching 2010.0  95690.37
М'які навички      Лідерство          Delegation  560.0  10635.45
М'які навички      Лідерство                 NaN 2570.0 106325.82
М'які навички            NaN                 NaN 9398.0 276875.00

**Інтерпретація:** Технічні навички — 75,2% витрат; найбільший внесок — Програмування.

## q03_drilldown.sql
**Питання:** див. коментар у файлі.
```sql
-- Q3 [drill-down по таксономії, 3 кроки]. Питання: яка частка витрат припадає на кожен клас, і як вона розкладається на підкласи та компетенції?
-- Крок 1: клас. Крок 2: підкласи класу «Технічні навички». Крок 3: компетенції підкласу «Програмування».
SELECT c.class_label, ROUND(SUM(f.cost_eur),2) AS cost_eur, ROUND(100.0 * SUM(f.cost_eur) / (SELECT SUM(cost_eur) FROM fact_training), 1) AS share_pct FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY c.class_label ORDER BY cost_eur DESC;
SELECT c.subclass_label, ROUND(SUM(f.cost_eur),2) AS cost_eur, ROUND(100.0 * SUM(f.cost_eur) / (SELECT SUM(f2.cost_eur) FROM fact_training f2 JOIN dim_competence c2 ON c2.competence_key = f2.competence_key WHERE c2.class_label = 'Технічні навички'), 1) AS share_pct FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key WHERE c.class_label = 'Технічні навички' GROUP BY c.subclass_label ORDER BY cost_eur DESC;
SELECT c.competence_label, ROUND(SUM(f.cost_eur),2) AS cost_eur, ROUND(SUM(f.hours),1) AS hours FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key WHERE c.subclass_label = 'Програмування' GROUP BY c.competence_label ORDER BY cost_eur DESC;

```

     class_label  cost_eur  share_pct
Технічні навички 837469.57       75.2
   М'які навички 276875.00       24.8

       subclass_label  cost_eur  share_pct
        Програмування 543793.26       64.9
            Аналітика 278459.93       33.3
Відповідність і право  15216.38        1.8

  competence_label  cost_eur  hours
Python programming 328396.79 9104.0
  Java programming 215396.47 4576.0

**Інтерпретація:** Дрилдаун клас → підклас → компетенція: Python (328 396,79 €) і Java (215 396,47 €) домінують у Програмуванні.

## q04_cube.sql
**Питання:** див. коментар у файлі.
```sql
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

```

   position_name      class_label   hours
     HR-менеджер    М'які навички   680.0
     HR-менеджер Технічні навички   808.0
     HR-менеджер              NaN  1488.0
Python-розробник    М'які навички  5136.0
Python-розробник Технічні навички 16563.0
Python-розробник              NaN 21699.0
Керівник команди    М'які навички  2935.0
Керівник команди Технічні навички  3923.0

**Інтерпретація:** CUBE показує всі комбінації клас × рік, включно з підсумками обох осей.

## q05_grouping_sets.sql
**Питання:** див. коментар у файлі.
```sql
-- Q5 [GROUPING SETS]. Питання: вартість навчання за (рік, клас), лише за класом і загальна — без зайвих комбінацій.
-- Еквівалент DuckDB: GROUP BY GROUPING SETS ((year, class_label), (class_label), ()).
SELECT * FROM (
WITH b AS (SELECT d.year, c.class_label, f.cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key)
SELECT year, class_label, ROUND(SUM(cost_eur),2) AS cost_eur FROM b GROUP BY 1,2
UNION ALL SELECT NULL, class_label, ROUND(SUM(cost_eur),2) FROM b GROUP BY 2
UNION ALL SELECT NULL, NULL, ROUND(SUM(cost_eur),2) FROM b
)
ORDER BY class_label IS NULL, class_label, year IS NULL, year;

```

  year      class_label  cost_eur
2024.0    М'які навички  75674.92
2025.0    М'які навички  99953.25
2026.0    М'які навички 101246.83
   NaN    М'які навички 276875.00
2024.0 Технічні навички 262580.95
2025.0 Технічні навички 294717.72
2026.0 Технічні навички 280170.90
   NaN Технічні навички 837469.57

**Інтерпретація:** GROUPING SETS дають лише потрібні зрізи без зайвих комбінацій.

## q06_slice.sql
**Питання:** див. коментар у файлі.
```sql
-- Q6 [slice]. Питання: скільки коштує година навчання за кожним класом компетенцій у 2025 році (зріз за часом)?
SELECT c.class_label, ROUND(SUM(f.hours),1) AS hours, ROUND(SUM(f.cost_eur),2) AS cost_eur, ROUND(SUM(f.cost_eur) / SUM(f.hours), 2) AS cost_per_hour FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key WHERE d.year = 2025 GROUP BY c.class_label ORDER BY cost_per_hour DESC;

```

     class_label  hours  cost_eur  cost_per_hour
Технічні навички 8025.0 294717.72          36.72
   М'які навички 3247.0  99953.25          30.78

**Інтерпретація:** Зріз 2025: вартість години технічних 36,72 €, м'яких 30,78 € (перевірено pandas).

## q07_dice.sql
**Питання:** див. коментар у файлі.
```sql
-- Q7 [dice]. Питання: як розподілено години технічного навчання у другому півріччі 2025 між підкласами для Python-розробників і керівників команди (куб, обмежений за трьома вимірами)?
SELECT c.subclass_label, p.position_name, ROUND(SUM(f.hours),1) AS hours, COUNT(DISTINCT e.employee_id) AS learners FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key
WHERE c.class_label = 'Технічні навички' AND p.position_name IN ('Python-розробник', 'Керівник команди') AND d.year_quarter IN ('2025-Q3', '2025-Q4')
GROUP BY c.subclass_label, p.position_name ORDER BY p.position_name, hours DESC;

```

       subclass_label    position_name  hours  learners
        Програмування Python-розробник 1744.0        13
            Аналітика Python-розробник 1004.0        12
Відповідність і право Python-розробник   29.0         5
        Програмування Керівник команди  956.0         8
            Аналітика Керівник команди  118.0         3
Відповідність і право Керівник команди   10.0         2

**Інтерпретація:** Dice: Python-розробники — 1744 год у Програмуванні, 1004 у Аналітиці.

## q08_pivot.sql
**Питання:** див. коментар у файлі.
```sql
-- Q8 [pivot]. Питання: години навчання за кварталами (рядки) та класами компетенцій (стовпці) для швидкого порівняння.
-- Еквівалент DuckDB: PIVOT ... ON class_label USING SUM(hours). Тут умовна агрегація (працює в обох СУБД).
SELECT d.year_quarter, ROUND(SUM(CASE WHEN c.class_label = 'Технічні навички' THEN f.hours ELSE 0 END),1) AS hard_hours,
       ROUND(SUM(CASE WHEN c.class_label = 'М''які навички' THEN f.hours ELSE 0 END),1) AS soft_hours, ROUND(SUM(f.hours),1) AS total_hours FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY d.year_quarter ORDER BY d.year_quarter;

```

year_quarter  hard_hours  soft_hours  total_hours
     2024-Q1      1792.0       652.0       2444.0
     2024-Q2      1695.0       678.0       2373.0
     2024-Q3      1889.0       723.0       2612.0
     2024-Q4      1730.0       673.0       2403.0
     2025-Q1      2268.0       708.0       2976.0
     2025-Q2      1550.0       712.0       2262.0
     2025-Q3      2149.0      1072.0       3221.0
     2025-Q4      2058.0       755.0       2813.0

**Інтерпретація:** Зведена таблиця (pivot) клас × рік через CASE.

## q09_cumulative.sql
**Питання:** див. коментар у файлі.
```sql
-- Q9 [віконна: накопичення]. Питання: як зростають сукупні витрати на навчання помісячно, і яку частку річного бюджету складають за 2025 рік?
WITH m AS (SELECT d.year, d.year_month, SUM(f.cost_eur) AS cost_eur FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY d.year, d.year_month)
SELECT year_month, ROUND(cost_eur,2) AS cost_eur, ROUND(SUM(cost_eur) OVER (PARTITION BY year ORDER BY year_month),2) AS ytd_cost,
       ROUND(100.0 * SUM(cost_eur) OVER (PARTITION BY year ORDER BY year_month) / SUM(cost_eur) OVER (PARTITION BY year), 1) AS ytd_share_pct
FROM m WHERE year = 2025 ORDER BY year_month;

```

year_month  cost_eur  ytd_cost  ytd_share_pct
   2025-01  37095.32  37095.32            9.4
   2025-02  29806.83  66902.15           17.0
   2025-03  37978.41 104880.56           26.6
   2025-04  27195.32 132075.88           33.5
   2025-05  26017.45 158093.33           40.1
   2025-06  24557.13 182650.46           46.3
   2025-07  40211.90 222862.36           56.5
   2025-08  37213.65 260076.01           65.9

**Інтерпретація:** Кумулятивна сума за 2025 зростає монотонно, показуючи темп накопичення витрат.

## q10_rank.sql
**Питання:** див. коментар у файлі.
```sql
-- Q10 [віконна: ранг]. Питання: хто з співробітників проводить найбільше годин на навчанні в межах своєї посади (топ-3 за посадою)?
WITH t AS (SELECT p.position_name, e.employee_name, ROUND(SUM(f.hours),1) AS hours FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key GROUP BY p.position_name, e.employee_id, e.employee_name),
r AS (SELECT *, RANK() OVER (PARTITION BY position_name ORDER BY hours DESC) AS rnk FROM t)
SELECT position_name, rnk, employee_name, hours FROM r WHERE rnk <= 3 ORDER BY position_name, rnk, employee_name;

```

   position_name  rnk   employee_name  hours
     HR-менеджер    1    Олена Коваль  860.0
     HR-менеджер    2     Олег Павлюк  448.0
     HR-менеджер    3 Христина Ткачук  180.0
Python-розробник    1     Ірина Мороз 1741.0
Python-розробник    2   Богдан Федина 1706.0
Python-розробник    3    Петро Бондар 1625.0
Керівник команди    1     Іван Шевчук 1301.0
Керівник команди    2   Назар Кузьмич 1184.0

**Інтерпретація:** Топ-1 за годинами в посаді: Python-розробник Ірина Мороз — 1741 год.

## q11_moving_avg.sql
**Питання:** див. коментар у файлі.
```sql
-- Q11 [віконна: ковзне середнє]. Питання: як змінюється середній приріст оцінки після завершених курсів (3-місячне ковзне середнє) у 2025–2026 роках?
WITH m AS (SELECT d.year_month, AVG(f.score_after - f.score_before) AS gain FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key WHERE f.completed = 1 AND d.year >= 2025 GROUP BY d.year_month)
SELECT year_month, ROUND(gain,3) AS avg_gain, ROUND(AVG(gain) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),3) AS ma3 FROM m ORDER BY year_month;

```

year_month  avg_gain   ma3
   2025-01     1.626 1.626
   2025-02     1.557 1.591
   2025-03     1.796 1.659
   2025-04     1.708 1.687
   2025-05     1.670 1.725
   2025-06     1.612 1.663
   2025-07     1.794 1.692
   2025-08     1.713 1.706

**Інтерпретація:** Ковзне середнє (3 періоди) згладжує коливання приросту оцінки.

## q12_semi_additive.sql
**Питання:** див. коментар у файлі.
```sql
-- Q12 [напівадитивна міра]. Питання: яка чисельність співробітників у знімках кварталів 2025 року? Headcount не можна сумувати за часом — для року беремо останній знімок, а не суму.
WITH q AS (SELECT d.year, d.year_quarter, SUM(h.headcount) AS hc FROM fact_perf_quarter h JOIN dim_date d ON d.date_key = h.date_key WHERE d.year = 2025 GROUP BY d.year, d.year_quarter)
SELECT year_quarter, hc AS headcount, (SELECT SUM(hc) FROM q) AS wrong_sum_over_time, (SELECT hc FROM q ORDER BY year_quarter DESC LIMIT 1) AS correct_year_value FROM q ORDER BY year_quarter;

```

year_quarter  headcount  wrong_sum_over_time  correct_year_value
     2025-Q1         22                   93                  26
     2025-Q2         22                   93                  26
     2025-Q3         23                   93                  26
     2025-Q4         26                   93                  26

**Інтерпретація:** Headcount напівадитивний: 22/22/23/26; сума по часу (93) хибна, правильне значення на рік — 26.
