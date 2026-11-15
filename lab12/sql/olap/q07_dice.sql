-- Q7 [dice]. Питання: як розподілено години технічного навчання у другому півріччі 2025 між підкласами для Python-розробників і керівників команди (куб, обмежений за трьома вимірами)?
SELECT c.subclass_label, p.position_name, ROUND(SUM(f.hours),1) AS hours, COUNT(DISTINCT e.employee_id) AS learners FROM fact_training f JOIN dim_date d ON d.date_key = f.date_key JOIN dim_competence c ON c.competence_key = f.competence_key JOIN dim_employee e ON e.employee_sk = f.employee_sk JOIN dim_position p ON p.position_key = e.position_key
WHERE c.class_label = 'Технічні навички' AND p.position_name IN ('Python-розробник', 'Керівник команди') AND d.year_quarter IN ('2025-Q3', '2025-Q4')
GROUP BY c.subclass_label, p.position_name ORDER BY p.position_name, hours DESC;
