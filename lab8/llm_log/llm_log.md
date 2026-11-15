# Журнал взаємодії з LLM (ЛР 8)

- Дата: 2026-11-04
- Модель і версія: Claude (чат-сесія Claude Code)
- Параметри: temperature — за замовчуванням, seed не підтримується
- Версії підказки: v1 (схема), v2 (схема + 5 правил)
- Сирий вихід: tests/t2s_llm_v1.jsonl, tests/t2s_llm_v2.jsonl
- Рішення людини: v2 підтверджено 20 із 20 відповідей; відхилені й причини — docs/t2s_eval.md

## Підказка v1
```
Роль: SPARQL-експерт. Перетвори питання українською на ОДИН запит SPARQL 1.1 до RDF-графа HR-домену.
Префікс hr: <http://example.org/hr#>. Доступні класи: Action, ActiveState, Appraisal, AssignCourseAction, Attestation, Bonus, Candidate, CandidateState, CloseRecordAction, Competence, ConfirmEmploymentAction, Course, CourseCompletedEvent, DecisionRule, Dismissal, DismissedState, Document, Employee, Event, HRDecision, HRIS, HRISSensor, HRProcess, HardSkill, HighPerformer, HireEvent, InformationSystem, InitiateDismissalAction, Interview, KPI, KPISensor, LMS, LMSSensor, LowPerformer, LowProductivityEvent, ManagedEmployee, Manager, Metric, Motivation, Onboarding, OnboardingState, Person, Position, PositionProfile, ProbationReviewEvent, ProbationState, Productivity, Promotion, Recruiter, Recruitment, ResignationRequestEvent, Resume, Reward, Salary, Sensor, SituationTemplate, SoftSkill, StartOnboardingAction, State, TrainedEmployee, Training, TrainingPlan, Turnover, UnderReviewState, UpdateCompetenceAction.
Доступні властивості: affects, appliesRule, candidateFor, completedCourse, concernsEmployee, courseHours, courseTitle, decisionAbout, directManager, employeeId, evaluates, evaluatesMetric, fromState, fullName, guard, hasCompetence, hasSubProcess, hireDate, inState, includesCourse, isOccupiedBy, kpiTarget, lowers, makesDecision, manages, observedBy, occupies, occurredOn, onEvent, performsAction, planFor, positionTitle, productivityScore, raises, reportedBy, reportsTo, requiresCompetence, requiresDocument, ruleLeadsTo, salaryAmount, salaryGrade, storesDocument, storesRecordOf, subProcessOf, submittedResume, tenureMonths, toState, turnoverRate.
Поверни лише запит.
```

## Підказка v2
```
Роль: SPARQL-експерт. Перетвори питання українською на ОДИН запит SPARQL 1.1 до RDF-графа HR-домену.
Префікс hr: <http://example.org/hr#>. Доступні класи: Action, ActiveState, Appraisal, AssignCourseAction, Attestation, Bonus, Candidate, CandidateState, CloseRecordAction, Competence, ConfirmEmploymentAction, Course, CourseCompletedEvent, DecisionRule, Dismissal, DismissedState, Document, Employee, Event, HRDecision, HRIS, HRISSensor, HRProcess, HardSkill, HighPerformer, HireEvent, InformationSystem, InitiateDismissalAction, Interview, KPI, KPISensor, LMS, LMSSensor, LowPerformer, LowProductivityEvent, ManagedEmployee, Manager, Metric, Motivation, Onboarding, OnboardingState, Person, Position, PositionProfile, ProbationReviewEvent, ProbationState, Productivity, Promotion, Recruiter, Recruitment, ResignationRequestEvent, Resume, Reward, Salary, Sensor, SituationTemplate, SoftSkill, StartOnboardingAction, State, TrainedEmployee, Training, TrainingPlan, Turnover, UnderReviewState, UpdateCompetenceAction.
Доступні властивості: affects, appliesRule, candidateFor, completedCourse, concernsEmployee, courseHours, courseTitle, decisionAbout, directManager, employeeId, evaluates, evaluatesMetric, fromState, fullName, guard, hasCompetence, hasSubProcess, hireDate, inState, includesCourse, isOccupiedBy, kpiTarget, lowers, makesDecision, manages, observedBy, occupies, occurredOn, onEvent, performsAction, planFor, positionTitle, productivityScore, raises, reportedBy, reportsTo, requiresCompetence, requiresDocument, ruleLeadsTo, salaryAmount, salaryGrade, storesDocument, storesRecordOf, subProcessOf, submittedResume, tenureMonths, toState, turnoverRate.
Поверни лише запит.
Правила (додано після аналізу помилок v1):
1) У графі немає reasoner: ієрархію класів обходь шляхом a/rdfs:subClassOf* (Manager і Recruiter — підкласи Employee; HardSkill і SoftSkill — підкласи Competence).
2) Визначені класи (наприклад LowPerformer) не мають явних екземплярів — замість них пиши FILTER за властивостями.
3) Рядкові значення типізовані xsd:string: порівнюй через FILTER(STR(?x) = "..."), а не літералом у шаблоні.
4) Властивість reportsTo не заповнена; транзитивних підлеглих шукай через hr:directManager+.
5) Коли перелічуєш типи (a ?type), виключай owl:NamedIndividual; коли рахуєш людей, обмежуй вибірку класом Employee з підкласами.
```
