"""Дані для text-to-SPARQL: питання, еталонні запити (gold) та відповіді LLM для двох версій підказки.

Відповіді v1/v2 згенеровано в чат-сесії (не через API) і записано тут дослівно; конвеєр r4_t2s.py лише перевіряє й оцінює їх.
Префікси (hr, rdf, rdfs, owl, xsd) додаються конвеєром автоматично. Якщо відповідь не змінювалась між версіями, v2 = v1.
Контрольні питання H01–H04 не використовувались для покращення підказки (є лише відповідь v2).
"""

Q = []


def add(id, diff, cat, question, gold, v1=None, v2=None, heldout=False):
    Q.append({"id": id, "difficulty": diff, "category": cat, "question": question, "gold": gold,
              "v1": gold if v1 is None and not heldout else v1, "v2": gold if v2 is None else v2, "heldout": heldout})


add("T01", "easy", "aggregation", "Скільки співробітників мають продуктивність нижче 5?",
    "SELECT (COUNT(DISTINCT ?e) AS ?n) WHERE { ?e a/rdfs:subClassOf* hr:Employee ; hr:productivityScore ?s . FILTER(?s < 5) }",
    "SELECT (COUNT(?e) AS ?n) WHERE { ?e a hr:Employee ; hr:productivityScore ?s . FILTER(?s < 5) }")
add("T02", "easy", "lookup", "Яка посада у Петра Бондаря?",
    'SELECT ?title WHERE { ?e hr:fullName ?n ; hr:occupies ?p . ?p hr:positionTitle ?title . FILTER(STR(?n) = "Петро Бондар") }',
    'SELECT ?title WHERE { ?e hr:fullName "Петро Бондар" ; hr:occupies ?p . ?p hr:positionTitle ?title }')
add("T03", "easy", "lookup", "Які компетенції вимагає посада «Рекрутер»?",
    'SELECT ?c WHERE { ?p hr:positionTitle ?t ; hr:requiresCompetence ?c . FILTER(STR(?t) = "Рекрутер") }',
    'SELECT ?c WHERE { ?p hr:positionTitle "Рекрутер" ; hr:requiresCompetence ?c }')
add("T04", "easy", "ask", "Чи завершив Андрій Мельник курс Python Advanced?",
    "ASK { hr:andriy hr:completedCourse hr:pythonAdvancedCourse }")
add("T05", "easy", "lookup", "Хто безпосередній керівник Марії Гончар?",
    'SELECT ?manager WHERE { ?e hr:fullName ?n ; hr:directManager ?m . ?m hr:fullName ?manager . FILTER(STR(?n) = "Марія Гончар") }',
    'SELECT ?manager WHERE { ?e hr:fullName "Марія Гончар" ; hr:directManager ?m . ?m hr:fullName ?manager }')
add("T06", "medium", "aggregation", "Яка середня продуктивність на кожній посаді?",
    "SELECT ?title (AVG(?s) AS ?avg) WHERE { ?e hr:occupies ?p ; hr:productivityScore ?s . ?p hr:positionTitle ?title } GROUP BY ?title")
add("T07", "medium", "path", "Хто транзитивно підпорядкований Івану Шевчуку?",
    "SELECT DISTINCT ?e WHERE { ?e hr:directManager+ hr:ivan }",
    "SELECT ?e WHERE { ?e hr:reportsTo hr:ivan }")
add("T08", "medium", "aggregation", "Скільки менеджерів у графі?",
    "SELECT (COUNT(DISTINCT ?e) AS ?n) WHERE { ?e a/rdfs:subClassOf* hr:Manager }",
    "SELECT (COUNT(?e) AS ?n) WHERE { ?e a hr:Manager }")
add("T09", "medium", "defined-class", "Хто має низьку продуктивність (клас LowPerformer)?",
    "SELECT DISTINCT ?name WHERE { ?e hr:fullName ?name ; hr:productivityScore ?s . FILTER(?s < 5) }",
    "SELECT ?name WHERE { ?e a hr:LowPerformer ; hr:fullName ?name }")
add("T10", "medium", "join", "Які курси входять до плану навчання Петра?",
    "SELECT ?title WHERE { ?plan hr:planFor hr:petro ; hr:includesCourse ?c . ?c hr:courseTitle ?title }")
add("T11", "medium", "filter", "Хто з співробітників пропрацював понад 60 місяців?",
    "SELECT ?name WHERE { ?e a/rdfs:subClassOf* hr:Employee ; hr:fullName ?name ; hr:tenureMonths ?t . FILTER(?t > 60) }",
    "SELECT ?name WHERE { ?e a hr:Employee ; hr:fullName ?name ; hr:tenureMonths ?t . FILTER(?t > 60) }")
add("T12", "medium", "aggregation", "Скільки співробітників у кожному стані?",
    "SELECT ?st (COUNT(DISTINCT ?e) AS ?n) WHERE { ?e a/rdfs:subClassOf* hr:Employee ; hr:inState ?st } GROUP BY ?st",
    "SELECT ?st (COUNT(?e) AS ?n) WHERE { ?e hr:inState ?st } GROUP BY ?st")
add("T13", "hard", "aggregation", "Який керівник має найбільше безпосередніх підлеглих?",
    "SELECT ?m (COUNT(?e) AS ?n) WHERE { ?e hr:directManager ?m } GROUP BY ?m ORDER BY DESC(?n) LIMIT 1")
add("T14", "hard", "aggregation", "Для кожної посади: скільки співробітників мають оцінку не нижче 7?",
    "SELECT ?title (COUNT(?e) AS ?n) WHERE { ?e hr:occupies ?p ; hr:productivityScore ?s . ?p hr:positionTitle ?title . FILTER(?s >= 7) } GROUP BY ?title")
add("T15", "hard", "hierarchy", "Скільки різних компетенцій (будь-якого типу) вимагають посади?",
    "SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE { ?p hr:requiresCompetence ?c . ?c a/rdfs:subClassOf* hr:Competence }",
    "SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE { ?p hr:requiresCompetence ?c . ?c a hr:Competence }")
add("T16", "hard", "join", "Які події стосуються співробітників з оцінкою нижче 5 і яких вони типів?",
    "SELECT ?ev ?type WHERE { ?ev a ?type ; hr:concernsEmployee ?e . ?e hr:productivityScore ?s . FILTER(?s < 5) FILTER(?type != owl:NamedIndividual) }",
    "SELECT ?ev ?type WHERE { ?ev a ?type ; hr:concernsEmployee ?e . ?e hr:productivityScore ?s . FILTER(?s < 5) }")

# контрольний набір (не використовувався при покращенні підказки)
add("H01", "easy", "aggregation", "Скільки кандидатів у графі?",
    "SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE { ?c a/rdfs:subClassOf* hr:Candidate }", heldout=True)
add("H02", "medium", "aggregation", "Хто має найвищу продуктивність і яка вона?",
    "SELECT ?name ?s WHERE { ?e hr:fullName ?name ; hr:productivityScore ?s } ORDER BY DESC(?s) LIMIT 1", heldout=True)
add("H03", "medium", "aggregation", "Скільки співробітників обіймають посаду «Python-розробник»?",
    'SELECT (COUNT(DISTINCT ?e) AS ?n) WHERE { ?e hr:occupies ?p . ?p hr:positionTitle ?t . FILTER(STR(?t) = "Python-розробник") }', heldout=True)
add("H04", "easy", "lookup", "Хто підпорядкований безпосередньо Олені Коваль?",
    "SELECT ?name WHERE { ?e hr:directManager hr:olena ; hr:fullName ?name }", heldout=True)

PROMPT_V1 = ("Роль: SPARQL-експерт. Перетвори питання українською на ОДИН запит SPARQL 1.1 до RDF-графа HR-домену.\n"
             "Префікс hr: <http://example.org/hr#>. Доступні класи: {classes}.\nДоступні властивості: {props}.\n"
             "Поверни лише запит.")
PROMPT_V2_EXTRA = ("\nПравила (додано після аналізу помилок v1):\n"
                   "1) У графі немає reasoner: ієрархію класів обходь шляхом a/rdfs:subClassOf* (Manager і Recruiter — підкласи Employee; HardSkill і SoftSkill — підкласи Competence).\n"
                   "2) Визначені класи (наприклад LowPerformer) не мають явних екземплярів — замість них пиши FILTER за властивостями.\n"
                   "3) Рядкові значення типізовані xsd:string: порівнюй через FILTER(STR(?x) = \"...\"), а не літералом у шаблоні.\n"
                   "4) Властивість reportsTo не заповнена; транзитивних підлеглих шукай через hr:directManager+.\n"
                   "5) Коли перелічуєш типи (a ?type), виключай owl:NamedIndividual; коли рахуєш людей, обмежуй вибірку класом Employee з підкласами.")
