# Оцінка text-to-SPARQL

## Конвеєр
підказка зі схемою (класи й властивості з графа) → LLM → парсер (rdflib `prepareQuery`; префікси додає конвеєр) → перевірка схеми (усі `hr:`-терміни існують у графі) → виконання на rdflib з `LIMIT 100` → порівняння множини рядків з еталоном.

## Метрики
| Набір / версія | синтаксично коректні | лише зі схеми | правильний результат |
|---|---|---|---|
| основний (n=16), v1 | 16/16 (100 %) | 16/16 (100 %) | 6/16 (38 %) |
| основний (n=16), v2 | 16/16 (100 %) | 16/16 (100 %) | 16/16 (100 %) |
| контрольний (n=4), v2 | 4/4 (100 %) | 4/4 (100 %) | 4/4 (100 %) |


## Результати по питаннях
| id | складність | v1 | v2 | рядків (еталон) |
|---|---|---|---|---|
| T01 | easy | ✗ | ✓ | 1 |
| T02 | easy | ✗ | ✓ | 1 |
| T03 | easy | ✗ | ✓ | 1 |
| T04 | easy | ✓ | ✓ | 1 |
| T05 | easy | ✗ | ✓ | 1 |
| T06 | medium | ✓ | ✓ | 4 |
| T07 | medium | ✗ | ✓ | 13 |
| T08 | medium | ✓ | ✓ | 1 |
| T09 | medium | ✗ | ✓ | 6 |
| T10 | medium | ✓ | ✓ | 2 |
| T11 | medium | ✗ | ✓ | 14 |
| T12 | medium | ✗ | ✓ | 2 |
| T13 | hard | ✓ | ✓ | 1 |
| T14 | hard | ✓ | ✓ | 4 |
| T15 | hard | ✗ | ✓ | 1 |
| T16 | hard | ✗ | ✓ | 8 |
| H01 | easy | — | ✓ | 1 |
| H02 | medium | — | ✓ | 1 |
| H03 | medium | — | ✓ | 1 |
| H04 | easy | — | ✓ | 10 |


## Аналіз помилок v1 (клас → кількість)
| клас | кількість |
|---|---|
| B — ігнорування ієрархії класів | 4 |
| E — точні літерали (xsd:string ≠ простий рядок) | 3 |
| A — залежність від виведення (немає reasoner) | 2 |
| F — інша семантична відмінність (див. результат) | 1 |

| питання | категорія | клас помилки | що пішло не так | виправлення у v2 |
|---|---|---|---|---|
| T01 | aggregation | B — ігнорування ієрархії класів | рядків 1 проти еталонних 1 | так |
| T02 | lookup | E — точні літерали (xsd:string ≠ простий рядок) | рядків 0 проти еталонних 1 | так |
| T03 | lookup | E — точні літерали (xsd:string ≠ простий рядок) | рядків 0 проти еталонних 1 | так |
| T05 | lookup | E — точні літерали (xsd:string ≠ простий рядок) | рядків 0 проти еталонних 1 | так |
| T07 | path | A — залежність від виведення (немає reasoner) | рядків 0 проти еталонних 13 | так |
| T09 | defined-class | A — залежність від виведення (немає reasoner) | рядків 0 проти еталонних 6 | так |
| T11 | filter | B — ігнорування ієрархії класів | рядків 9 проти еталонних 14 | так |
| T12 | aggregation | B — ігнорування ієрархії класів | рядків 3 проти еталонних 2 | так |
| T15 | hierarchy | B — ігнорування ієрархії класів | рядків 1 проти еталонних 1 | так |
| T16 | join | F — інша семантична відмінність (див. результат) | рядків 16 проти еталонних 8 | так |


## Підказки
### v1
```
Роль: SPARQL-експерт. Перетвори питання українською на ОДИН запит SPARQL 1.1 до RDF-графа HR-домену.
Префікс hr: <http://example.org/hr#>. Доступні класи: Action, ActiveState, Appraisal, AssignCourseAction, Attestation, Bonus, Candidate, CandidateState, CloseRecordAction, Competence, ConfirmEmploymentAction, Course, CourseCompletedEvent, DecisionRule, Dismissal, DismissedState, Document, Employee, Event, HRDecision, HRIS, HRISSensor, HRProcess, HardSkill, HighPerformer, HireEvent, InformationSystem, InitiateDismissalAction, Interview, KPI, KPISensor, LMS, LMSSensor, LowPerformer, LowProductivityEvent, ManagedEmployee, Manager, Metric, Motivation, Onboarding, OnboardingState, Person, Position, PositionProfile, ProbationReviewEvent, ProbationState, Productivity, Promotion, Recruiter, Recruitment, ResignationRequestEvent, Resume, Reward, Salary, Sensor, SituationTemplate, SoftSkill, StartOnboardingAction, State, TrainedEmployee, Training, TrainingPlan, Turnover, UnderReviewState, UpdateCompetenceAction.
Доступні властивості: affects, appliesRule, candidateFor, completedCourse, concernsEmployee, courseHours, courseTitle, decisionAbout, directManager, employeeId, evaluates, evaluatesMetric, fromState, fullName, guard, hasCompetence, hasSubProcess, hireDate, inState, includesCourse, isOccupiedBy, kpiTarget, lowers, makesDecision, manages, observedBy, occupies, occurredOn, onEvent, performsAction, planFor, positionTitle, productivityScore, raises, reportedBy, reportsTo, requiresCompetence, requiresDocument, ruleLeadsTo, salaryAmount, salaryGrade, storesDocument, storesRecordOf, subProcessOf, submittedResume, tenureMonths, toState, turnoverRate.
Поверни лише запит.
```
### v2 (покращена)
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


## Обмеження оцінки
Відповіді LLM згенеровано в чат-сесії, а не через API; еталони складено автором, тому v2 (складена після аналізу помилок v1) — оптимістична оцінка. Для чесної перевірки слугує контрольний набір H01–H04, не використаний при покращенні підказки.
