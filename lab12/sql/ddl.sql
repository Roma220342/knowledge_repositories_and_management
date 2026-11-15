-- Зіркова схема «Навчання та розвиток компетенцій» (Domain Knowledge Hub, HR). Типи сумісні з DuckDB і SQLite.
-- Зерно fact_training: один запис = одна участь одного співробітника в одному навчальному курсі (сесії) на дату.
-- Зерно fact_perf_quarter: один запис = один співробітник за один квартал.
DROP TABLE IF EXISTS fact_training; DROP TABLE IF EXISTS fact_perf_quarter;
DROP TABLE IF EXISTS dim_date; DROP TABLE IF EXISTS dim_employee; DROP TABLE IF EXISTS dim_position;
DROP TABLE IF EXISTS dim_competence; DROP TABLE IF EXISTS dim_course;

CREATE TABLE dim_date (
  date_key INTEGER PRIMARY KEY,            -- YYYYMMDD
  full_date TEXT NOT NULL, year INTEGER NOT NULL, quarter INTEGER NOT NULL, month INTEGER NOT NULL,
  year_quarter TEXT NOT NULL, year_month TEXT NOT NULL, day_of_week INTEGER NOT NULL, is_weekend INTEGER NOT NULL);

CREATE TABLE dim_position (                -- SCD тип 1: назва/грейд перезаписуються
  position_key INTEGER PRIMARY KEY, position_id TEXT NOT NULL UNIQUE, position_name TEXT NOT NULL, salary_grade INTEGER NOT NULL);

CREATE TABLE dim_employee (                -- SCD тип 2: нова версія рядка при зміні посади
  employee_sk INTEGER PRIMARY KEY, employee_id TEXT NOT NULL, employee_name TEXT NOT NULL, hire_date TEXT NOT NULL,
  position_key INTEGER NOT NULL REFERENCES dim_position(position_key),
  valid_from TEXT NOT NULL, valid_to TEXT NOT NULL, is_current INTEGER NOT NULL);

CREATE TABLE dim_competence (              -- вимір на основі таксономії компетенцій (клас -> підклас -> компетенція), IRI
  competence_key INTEGER PRIMARY KEY, competence_iri TEXT NOT NULL UNIQUE, competence_label TEXT NOT NULL,
  subclass_iri TEXT NOT NULL, subclass_label TEXT NOT NULL, class_iri TEXT NOT NULL, class_label TEXT NOT NULL, source TEXT NOT NULL);

CREATE TABLE dim_course (
  course_key INTEGER PRIMARY KEY, course_id TEXT NOT NULL UNIQUE, course_name TEXT NOT NULL, default_hours INTEGER NOT NULL,
  provider_type TEXT NOT NULL, competence_key INTEGER NOT NULL REFERENCES dim_competence(competence_key));

CREATE TABLE fact_training (
  training_key INTEGER PRIMARY KEY,
  date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
  employee_sk INTEGER NOT NULL REFERENCES dim_employee(employee_sk),
  course_key INTEGER NOT NULL REFERENCES dim_course(course_key),
  competence_key INTEGER NOT NULL REFERENCES dim_competence(competence_key),
  hours REAL NOT NULL,                     -- адитивна
  cost_eur REAL NOT NULL,                  -- адитивна
  completed INTEGER NOT NULL,              -- адитивна (кількість завершень)
  score_before REAL, score_after REAL,     -- неадитивні (оцінки 0–10; лише для завершених)
  satisfaction INTEGER);                   -- неадитивна (1–5)

CREATE TABLE fact_perf_quarter (
  perf_key INTEGER PRIMARY KEY,
  date_key INTEGER NOT NULL REFERENCES dim_date(date_key),   -- останній день кварталу
  employee_sk INTEGER NOT NULL REFERENCES dim_employee(employee_sk),
  headcount INTEGER NOT NULL,              -- напівадитивна (знімок: не підсумовується за часом)
  productivity_score REAL NOT NULL,        -- неадитивна
  bonus_eur REAL NOT NULL);                -- адитивна
CREATE INDEX ix_ft_date ON fact_training(date_key); CREATE INDEX ix_ft_emp ON fact_training(employee_sk); CREATE INDEX ix_ft_comp ON fact_training(competence_key);
