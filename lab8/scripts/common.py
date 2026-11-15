"""Спільні утиліти ЛР 8 (RDF, SPARQL, SHACL, text-to-SPARQL, зв'язки з Wikidata)."""
import csv
import random
import re
from datetime import date, timedelta
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, RDF, OWL, XSD, URIRef

ROOT = Path(__file__).resolve().parents[1]
LR7 = ROOT.parent / "ЛР7_артефакти" / "models"          # onto.ttl, onto_data.ttl з ЛР 7
HR = Namespace("http://example.org/hr#")
LNK = Namespace("http://example.org/lnk#")
GRAPH_IRI = "http://example.org/hr/graph/kb"
SEED = 42

PREFIX_HEADER = (
    "PREFIX hr: <http://example.org/hr#>\n"
    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
    "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
    "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n"
)

NAMESPACES = {
    "hr": HR,
    "owl": OWL,
    "xsd": XSD,
    "skos": Namespace("http://www.w3.org/2004/02/skos/core#"),
    "org": Namespace("http://www.w3.org/ns/org#"),
    "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
    "schema": Namespace("https://schema.org/"),
    "esco": Namespace("http://data.europa.eu/esco/model#"),
    "dcterms": Namespace("http://purl.org/dc/terms/"),
}

FIRST = ["Тарас", "Оксана", "Богдан", "Христина", "Юрій", "Наталія", "Остап", "Ірина", "Василь",
         "Галина", "Степан", "Леся", "Назар", "Уляна", "Максим", "Ольга", "Роман", "Дарина",
         "Олег", "Мирослава", "Тетяна", "Святослав", "Зоряна", "Ярослав"]
LAST = ["Гнатюк", "Яремчук", "Федина", "Ткачук", "Кравець", "Романюк", "Олійник", "Мороз",
        "Пономаренко", "Бойко", "Левицький", "Савченко", "Кузьмич", "Литвин", "Демчук",
        "Головатий", "Остапчук", "Захарчук", "Павлюк", "Стасюк", "Семенко", "Гуменюк", "Дорош", "Вовк"]


def local(u):
    return re.split(r"[#/]", str(u))[-1]


def bind(g):
    for k, v in NAMESPACES.items():
        g.bind(k, v)
    g.bind("lnk", LNK)
    return g


def enrich(g, n=24, start=7, seed=SEED):
    """Синтетичні співробітники E-<start>… (посада, керівник, компетенції, оцінка, дата прийому, події)."""
    rnd = random.Random(seed)
    competences = ["pythonProgramming", "teamCommunication", "negotiation", "hrAnalytics"]
    posts = rnd.choices(["pythonDeveloperPost", "recruiterPost", "teamLeadPost", "hrManagerPost"],
                        weights=[19, 2, 2, 1], k=n)
    leads, today = [], date(2026, 10, 28)
    for i in range(n):
        num = start + i
        e = HR[f"emp{num:03d}"]
        post = posts[i]
        cls = HR.Manager if post in ("teamLeadPost", "hrManagerPost") else HR.Recruiter if post == "recruiterPost" else HR.Employee
        g.add((e, RDF.type, OWL.NamedIndividual)); g.add((e, RDF.type, cls))
        g.add((e, HR.employeeId, Literal(f"E-{num:03d}", datatype=XSD.string)))
        g.add((e, HR.fullName, Literal(f"{FIRST[i % 24]} {LAST[(i * 7) % 24]}", datatype=XSD.string)))
        score, tenure = round(rnd.uniform(3.5, 9.6), 1), rnd.randint(3, 96)
        hired = today - timedelta(days=int(tenure * 30.4))
        g.add((e, HR.productivityScore, Literal(score, datatype=XSD.decimal)))
        g.add((e, HR.tenureMonths, Literal(tenure, datatype=XSD.integer)))
        g.add((e, HR.hireDate, Literal(f"{hired.isoformat()}T00:00:00", datatype=XSD.dateTime)))
        g.add((e, HR.occupies, HR[post]))
        g.add((e, HR.inState, HR.stateProbation if tenure <= 3 else HR.stateActive))
        mgr = "olena" if cls == HR.Manager else rnd.choice(["olena", "ivan", "ivan"] + leads)
        if cls == HR.Manager:
            leads.append(f"emp{num:03d}")
        g.add((e, HR.directManager, HR[mgr]))
        for c in rnd.sample(competences, rnd.randint(1, 3)):
            g.add((e, HR.hasCompetence, HR[c]))
        g.add((HR.hris1, HR.storesRecordOf, e))
        if rnd.random() < 0.5:
            g.add((e, HR.completedCourse, HR[rnd.choice(["pythonAdvancedCourse", "negotiationCourse"])]))
            ev = HR[f"eventCourse{num:03d}"]
            g.add((ev, RDF.type, OWL.NamedIndividual)); g.add((ev, RDF.type, HR.CourseCompletedEvent))
            g.add((ev, HR.concernsEmployee, e)); g.add((ev, HR.reportedBy, HR.sensorLMS))
            g.add((ev, HR.occurredOn, Literal(f"2026-{rnd.randint(1, 10):02d}-15T00:00:00", datatype=XSD.dateTime)))
        if score < 5.0:
            ev = HR[f"eventLowProd{num:03d}"]
            g.add((ev, RDF.type, OWL.NamedIndividual)); g.add((ev, RDF.type, HR.LowProductivityEvent))
            g.add((ev, HR.concernsEmployee, e)); g.add((ev, HR.reportedBy, HR.sensorKPI))
            g.add((ev, HR.occurredOn, Literal("2026-10-01T00:00:00", datatype=XSD.dateTime)))
    return g


def load_kb(links=False):
    g = Graph()
    g.parse(ROOT / "data" / "kb.ttl")
    if links and (ROOT / "data" / "links.ttl").exists():
        g.parse(ROOT / "data" / "links.ttl")
    return g


def term_str(t):
    return local(t) if isinstance(t, URIRef) else str(t)


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_table(rows, cols=None):
    if not rows:
        return "_(порожньо)_\n"
    cols = cols or list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols) + " |")
    return "\n".join(out) + "\n"


def add_claims(rows, reset=False):
    """claims/claims.csv: id, claim, type, source, verification_level, status, comment."""
    path = ROOT / "claims" / "claims.csv"
    path.parent.mkdir(exist_ok=True)
    mode = "w" if reset or not path.exists() else "a"
    with open(path, mode, newline="", encoding="utf-8-sig" if mode == "w" else "utf-8") as f:
        w = csv.writer(f)
        if mode == "w":
            w.writerow(["id", "claim", "type", "source", "verification_level", "status", "comment"])
        w.writerows(rows)
