# SHACL-валідація (pySHACL 0.40.2)

Форм: **7**, обмежень на властивості: **21** (типи: class, datatype, maxCount, maxInclusive, minCount, minInclusive, nodeKind, pattern).

## Навмисні дефекти
| № | Дефект | Очікується |
|---|---|---|
| D1 | petro: productivityScore = 12.5 | порушення діапазону 0..10 (MaxInclusive) |
| D2 | andriy: employeeId = "EMP-3" | порушення шаблону E-NNN (Pattern) |
| D3 | candidate1 candidateFor hr:pythonProgramming | значення не належить класу Position (Class) |


## Валідний набір (data/kb.ttl)
conforms = **True**, порушень: 0

_(порожньо)_


## Дефектний набір (data/kb_defects.ttl), inference = none
conforms = **False**, порушень: **3**

| вузол | властивість | обмеження | значення | повідомлення |
|---|---|---|---|---|
| andriy | employeeId | PatternConstraintComponent | EMP-3 | employeeId: рівно одне значення за шаблоном E-NNN |
| candidate1 | candidateFor | ClassConstraintComponent | http://example.org/hr#pythonProgramming | candidateFor: посада класу Position |
| petro | productivityScore | MaxInclusiveConstraintComponent | 12.5 | productivityScore: десяткове число в діапазоні 0..10 |


## Дефектний набір, inference = rdfs (порівняння)
conforms = **False**, порушень: **5**

| вузол | властивість | обмеження | значення | повідомлення |
|---|---|---|---|---|
| andriy | employeeId | PatternConstraintComponent | EMP-3 | employeeId: рівно одне значення за шаблоном E-NNN |
| petro | productivityScore | MaxInclusiveConstraintComponent | 12.5 | productivityScore: десяткове число в діапазоні 0..10 |
| pythonProgramming | positionTitle | MinCountConstraintComponent |  | positionTitle обов'язкове |
| pythonProgramming | requiresCompetence | MinCountConstraintComponent |  | посада має вимагати хоча б одну компетенцію |
| pythonProgramming | salaryGrade | MinCountConstraintComponent |  | salaryGrade: ціле число 1..10 |


## Чому SHACL, а не OWL
OWL працює у відкритому світі й без припущення унікальності імен: відсутня посада чи другий табельний номер для нього не помилка, бо відповідний факт може бути невідомим або вказувати на той самий індивід. SHACL працює із замкненим світом: порушення minCount/maxCount, datatype, діапазону, pattern і class дають явний звіт про валідацію. Тому обмеження якості даних (формат ідентифікатора, діапазон оцінки, тип значення) виражені в SHACL, а класифікація й виведення знань залишаються в OWL. Режим inference = rdfs змінює результат валідації (виведені типи можуть маскувати або створювати порушення), тому дані перевіряють без виведення.
