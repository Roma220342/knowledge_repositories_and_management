# Дизайн зірки
Гранулярність fact_training: участь одного співробітника в одному курсі за дату. fact_perf_quarter: співробітник × квартал.
Бізнес-питання: 1) скільки годин/євро витрачено за рік/квартал; 2) частка технічних vs м'яких навичок; 3) вартість години за підкласом; 4) хто з посад навчається найбільше; 5) середній приріст оцінки; 6) частка завершених курсів.
Виміри: dim_date, dim_employee (SCD2), dim_position (SCD1), dim_competence (таксономія з IRI), dim_course.
Міри: additive — hours, cost_eur, completed, bonus_eur; semi-additive — headcount; non-additive — score_before/after, satisfaction, productivity_score.
SCD: Type 2 для співробітника (зміна посади), Type 1 для довідника посад. Діаграма: figs/star_schema.png.
