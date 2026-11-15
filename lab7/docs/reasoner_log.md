# Журнал reasoner HermiT

Запуск: owlready2 0.51 + HermiT (вбудований), Java 21. Онтологія: models/onto.ttl + models/onto_data.ttl

## 1. Основний запуск
Узгодженість: True; час 2.1 с; нездійсненних класів: 0.

### Виведені твердження
- hr:HighPerformer rdfs:subClassOf hr:Employee
- hr:LowPerformer rdfs:subClassOf hr:Employee
- hr:ManagedEmployee rdfs:subClassOf hr:Employee
- hr:TrainedEmployee rdfs:subClassOf hr:Employee
- hr:andriy hr:reportsTo hr:ivan
- hr:andriy hr:reportsTo hr:olena
- hr:andriy rdf:type hr:HighPerformer
- hr:andriy rdf:type hr:ManagedEmployee
- hr:andriy rdf:type hr:TrainedEmployee
- hr:attestation2026 hr:subProcessOf hr:personnelManagement
- hr:interview1 hr:subProcessOf hr:personnelManagement
- hr:ivan hr:manages hr:andriy
- hr:ivan hr:manages hr:maria
- hr:ivan hr:manages hr:petro
- hr:ivan hr:reportsTo hr:olena
- hr:ivan rdf:type hr:HighPerformer
- hr:ivan rdf:type hr:ManagedEmployee
- hr:maria hr:reportsTo hr:ivan
- hr:maria hr:reportsTo hr:olena
- hr:maria rdf:type hr:ManagedEmployee
- hr:maria rdf:type hr:TrainedEmployee
- hr:olena hr:manages hr:andriy
- hr:olena hr:manages hr:ivan
- hr:olena hr:manages hr:maria
- hr:olena hr:manages hr:petro
- hr:olena hr:manages hr:sofia
- hr:onboarding1 hr:subProcessOf hr:personnelManagement
- hr:personnelManagement hr:hasSubProcess hr:attestation2026
- hr:personnelManagement hr:hasSubProcess hr:interview1
- hr:personnelManagement hr:hasSubProcess hr:onboarding1
- hr:petro hr:reportsTo hr:ivan
- hr:petro hr:reportsTo hr:olena
- hr:petro rdf:type hr:LowPerformer
- hr:petro rdf:type hr:ManagedEmployee
- hr:sofia hr:reportsTo hr:olena
- hr:sofia rdf:type hr:ManagedEmployee

## 2. Навмисна суперечність
Додано індивід conflictPerson, типізований одночасно як Employee та Candidate (диз'юнктні класи).
```
Exception in thread "main" org.semanticweb.owlapi.reasoner.InconsistentOntologyException: Inconsistent ontology
	at org.semanticweb.HermiT.Reasoner.throwInconsistentOntologyExceptionIfNecessary(Reasoner.java:2164)
(код завершення 1)
```
Виправлення: видалено тип Candidate. Повторний запуск: код завершення 0, онтологія узгоджена.
