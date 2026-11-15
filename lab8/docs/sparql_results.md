# Результати SPARQL-запитів

| id | конструкція | рядків | мс |
|---|---|---|---|
| q01 | SELECT | 2 | 6.4 |
| q02 | SELECT + FILTER | 1 | 32.6 |
| q03 | ASK | 1 | 5.3 |
| q04 | SELECT + агрегація COUNT + шлях rdfs:subClassOf* | 1 | 19.9 |
| q05 | SELECT + GROUP BY + AVG | 4 | 39.6 |
| q06 | SELECT + FILTER + OPTIONAL | 6 | 51.8 |
| q07 | SELECT + property path (alternative + one-or-more) | 29 | 16.7 |
| q08 | CONSTRUCT | 1 | 9.6 |
| q09 | SELECT + FILTER | 14 | 22.8 |
| q10 | SELECT + GROUP BY + HAVING | 3 | 47.5 |
| q12 | SELECT + federated SERVICE (Wikidata) | 5 | 6278.9 |


## q01
**CQ:** Які компетенції вимагає посада «Python-розробник»?  
**Конструкція:** SELECT  
**Інтерпретація:** Повертає IRI компетенцій, пов'язаних із посадою властивістю requiresCompetence; відповідає профілю посади.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT ?competence WHERE { hr:pythonDeveloperPost hr:requiresCompetence ?competence } ORDER BY ?competence
```

Час: 6.4 мс; рядків: 2

| competence |
|---|
| pythonProgramming |
| teamCommunication |


## q02
**CQ:** Хто є безпосереднім керівником Петра Бондаря?  
**Конструкція:** SELECT + FILTER  
**Інтерпретація:** Знаходить співробітника за іменем і повертає ім'я керівника через directManager.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT ?manager WHERE {
  ?e hr:fullName ?n ; hr:directManager ?m .
  FILTER(STR(?n) = "Петро Бондар")
  ?m hr:fullName ?manager
}
```

Час: 32.6 мс; рядків: 1

| manager |
|---|
| Іван Шевчук |


## q03
**CQ:** Чи має Марія Гончар компетенцію pythonProgramming?  
**Конструкція:** ASK  
**Інтерпретація:** Булева відповідь true/false про наявність факту hasCompetence.

```sparql
PREFIX hr: <http://example.org/hr#>
ASK { hr:maria hr:hasCompetence hr:pythonProgramming }
```

Час: 5.3 мс; рядків: 1

| answer |
|---|
| true |


## q04
**CQ:** Скільки всього співробітників (з урахуванням підкласів Manager і Recruiter)?  
**Конструкція:** SELECT + агрегація COUNT + шлях rdfs:subClassOf*  
**Інтерпретація:** Без reasoner підкласи потрібно обходити шляхом a/rdfs:subClassOf*; інакше менеджери й рекрутери не потраплять у вибірку.

```sparql
PREFIX hr: <http://example.org/hr#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT (COUNT(DISTINCT ?e) AS ?n) WHERE { ?e a/rdfs:subClassOf* hr:Employee }
```

Час: 19.9 мс; рядків: 1

| n |
|---|
| 30 |


## q05
**CQ:** Скільки співробітників і яка середня продуктивність на кожній посаді?  
**Конструкція:** SELECT + GROUP BY + AVG  
**Інтерпретація:** Групує співробітників за назвою посади; показує навантаження та якість по посадах.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT ?position (COUNT(?e) AS ?employees) (ROUND(AVG(?s) * 100) / 100 AS ?avgScore) WHERE {
  ?e hr:occupies ?p ; hr:productivityScore ?s .
  ?p hr:positionTitle ?position
} GROUP BY ?position ORDER BY DESC(?employees)
```

Час: 39.6 мс; рядків: 4

| position | employees | avgScore |
|---|---|---|
| Python-розробник | 24 | 6.79 |
| Рекрутер | 3 | 5.03 |
| Керівник команди | 2 | 9.05 |
| HR-менеджер | 1 | 7.9 |


## q06
**CQ:** Хто має продуктивність нижче 5 і які курси вони завершили (якщо є)?  
**Конструкція:** SELECT + FILTER + OPTIONAL  
**Інтерпретація:** OPTIONAL зберігає співробітників без курсів (порожнє значення); вибірка — кандидати на навчання.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT ?name ?score ?course WHERE {
  ?e hr:fullName ?name ; hr:productivityScore ?score .
  FILTER(?score < 5.0)
  OPTIONAL { ?e hr:completedCourse ?c . ?c hr:courseTitle ?course }
} ORDER BY ?score
```

Час: 51.8 мс; рядків: 6

| name | score | course |
|---|---|---|
| Тетяна Семенко | 3.6 |  |
| Святослав Ткачук | 3.9 | Ефективні перемовини |
| Степан Дорош | 4.1 |  |
| Петро Бондар | 4.2 |  |
| Олег Олійник | 4.5 |  |
| Ярослав Захарчук | 4.7 | Python Advanced |


## q07
**CQ:** Хто (транзитивно) підпорядкований Олені Коваль?  
**Конструкція:** SELECT + property path (alternative + one-or-more)  
**Інтерпретація:** Шлях (directManager|reportsTo)+ обходить ланцюжок керівників без записаної транзитивності.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT DISTINCT ?e WHERE { ?e (hr:directManager|hr:reportsTo)+ hr:olena } ORDER BY ?e
```

Час: 16.7 мс; рядків: 29

| e |
|---|
| andriy |
| emp007 |
| emp008 |
| emp009 |
| emp010 |
| emp011 |
| emp012 |
| emp013 |
| emp014 |
| emp015 |


## q08
**CQ:** Який граф зв'язків «керівник керує підлеглим» можна отримати з directManager?  
**Конструкція:** CONSTRUCT  
**Інтерпретація:** Будує нові триплети hr:manages (обернена властивість), які можна завантажити окремим графом.

```sparql
PREFIX hr: <http://example.org/hr#>
CONSTRUCT { ?m hr:manages ?e } WHERE { ?e hr:directManager ?m }
```

Час: 9.6 мс; рядків: 1

| triples |
|---|
| 29 |


## q09
**CQ:** Хто пропрацював в організації понад 60 місяців?  
**Конструкція:** SELECT + FILTER  
**Інтерпретація:** Фільтр за числовою властивістю tenureMonths; ядро «досвідчених» співробітників.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT ?name ?months WHERE {
  ?e hr:fullName ?name ; hr:tenureMonths ?months .
  FILTER(?months > 60)
} ORDER BY DESC(?months)
```

Час: 22.8 мс; рядків: 14

| name | months |
|---|---|
| Уляна Стасюк | 95 |
| Зоряна Левицький | 95 |
| Мирослава Литвин | 88 |
| Олена Коваль | 88 |
| Максим Федина | 84 |
| Остап Павлюк | 84 |
| Галина Головатий | 77 |
| Іван Шевчук | 76 |
| Тетяна Семенко | 73 |
| Дарина Вовк | 71 |


## q10
**CQ:** Які керівники мають щонайменше 5 безпосередніх підлеглих?  
**Конструкція:** SELECT + GROUP BY + HAVING  
**Інтерпретація:** HAVING відфільтровує групи після агрегації; показує навантаження керівників.

```sparql
PREFIX hr: <http://example.org/hr#>
SELECT ?manager (COUNT(?e) AS ?team) WHERE {
  ?e hr:directManager ?m .
  ?m hr:fullName ?manager
} GROUP BY ?manager HAVING (COUNT(?e) >= 5) ORDER BY DESC(?team)
```

Час: 47.5 мс; рядків: 3

| manager | team |
|---|---|
| Іван Шевчук | 13 |
| Олена Коваль | 10 |
| Остап Павлюк | 6 |


## q12
**CQ:** Які зовнішні відповідники (Wikidata) мають наші поняття, зв'язки з якими верифіковано?  
**Конструкція:** SELECT + federated SERVICE (Wikidata)  
**Інтерпретація:** З локального графа беруться лише верифіковані зв'язки (data/links.ttl); мітку й опис отримуємо з query.wikidata.org.

Режим: rdflib SERVICE → query.wikidata.org

Час: 6278.9 мс; рядків: 5

| term | relation | conf | label | desc |
|---|---|---|---|---|
| Employee | exactMatch | 0.9 | employee |  |
| Resume | exactMatch | 0.9 | curriculum vitae |  |
| Salary | exactMatch | 0.9 | salary |  |
| Position | closeMatch | 0.7 | occupation |  |
| KPI | closeMatch | 0.7 | performance indicator |  |


## Оптимізація q11a → q11b
| Варіант | Рушій | Час, мс | Пар |
|---|---|---|---|
| q11a (FILTER наприкінці, декартів добуток) | rdflib | 7348.7 | 743 |
| q11b (селективні підзапити першими) | rdflib | 480.2 | 743 |
| q11a (FILTER наприкінці, декартів добуток) | Oxigraph | 2.4 | 743 |
| q11b (селективні підзапити першими) | Oxigraph | 1.1 | 743 |

Відповіді однакові: **True**


## Ручна перевірка
| запит | очікування (перебір триплетів) | результат SPARQL | збіг |
|---|---|---|---|
| q02 | Іван Шевчук | Іван Шевчук | так |
| q04 | 30 | 30 | так |
| q07 | 29 підлеглих | 29 підлеглих | так |
| q09 | 14 осіб | 14 осіб | так |
| q10 | Іван Шевчук 13; Олена Коваль 10; Остап Павлюк 6 | Іван Шевчук 13; Олена Коваль 10; Остап Павлюк 6 | так |
