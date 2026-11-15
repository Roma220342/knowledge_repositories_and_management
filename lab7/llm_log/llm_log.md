# Журнал взаємодії з LLM (ЛР 7)

- Дата: 14.10.2026
- Модель: Claude Sonnet 5.5 (claude-sonnet-5-5)
- Параметри: temperature — за замовчуванням середовища; seed не підтримується
- Версія підказки: v1.0 (роль «онтолог», вхід — таксономія ЛР 4 + триплети ЛР 6, вихід — Turtle)

## Ітерація v1
- parse_error: BadSyntax: at line 44 of <>:
Bad syntax (expected '.' or '}' or ']' at end of statement) at ^ in:
"...b'Document .\n:Course a owl:Class ; rdfs:subClassOf :HRProcess\n'^b':InformationSystem a owl:Class .\n:HRIS a owl:Class ; rdfs:su'..."
- consistent: None
- unsat: None
- log: 

## Ітерація v2
- parse_error: None
- consistent: False
- unsat: []
- log: EXC OwlReadyJavaError: Java error message is:
Exception in thread "main" java.lang.IllegalArgumentException: Non-simple property '<http://example.org/hr#reportsTo>' or its inverse appears in asymmetric object property axiom.

## Ітерація v3
- parse_error: None
- consistent: False
- unsat: []
- log: EXC OwlReadyJavaError: Java error message is:
Exception in thread "main" org.semanticweb.HermiT.datatypes.UnsupportedDatatypeException: HermiT supports all and only the datatypes of the OWL 2 datatype map, see 
http://www.w3.org/TR/owl2-syntax/#Datatype_Maps. 
The datatype 'http://www.w3.org/2001/XM

## Ітерація v3b
- parse_error: None
- consistent: True
- unsat: ['Candidate', 'Recruiter', 'Manager']
- log: SubClassOf( <http://example.org/hr#Department> <http://example.org/hr#Organization> )
SubClassOf( <http://example.org/hr#Promotion> <http://example.org/hr#HRDecision> )
SubClassOf( <http://example.org/hr#SoftSkill> <http://example.org/hr#Competence> )
SubClassOf( <http://example.org/hr#HardSkill> <h

## Ітерація v4
- parse_error: None
- consistent: True
- unsat: []
- log: SubClassOf( <http://example.org/hr#Department> <http://example.org/hr#Organization> )
SubClassOf( <http://example.org/hr#PositionProfile> <http://example.org/hr#Document> )
SubClassOf( <http://example.org/hr#Contract> <http://example.org/hr#Document> )
SubClassOf( <http://example.org/hr#Resume> <htt

Рішення людини: підтверджено 42, відхилено 17 із 59 тверджень (див. claims.csv).
