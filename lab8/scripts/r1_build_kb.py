"""Результат 1: RDF-дані у триплсторі.
Онтологія + індивіди ЛР 7 -> збагачення -> data/kb.ttl, data/kb.jsonld -> Oxigraph -> COUNT -> docs/load_log.md
"""
import shutil
from datetime import datetime, timezone
from importlib.metadata import version

from rdflib import BNode, Graph, Literal, RDF, OWL, URIRef

from common import GRAPH_IRI, HR, ROOT, LR7, bind, enrich, md_table, write

try:
    import pyoxigraph as ox
except ImportError:          # Oxigraph необов'язковий: без нього COUNT рахується через rdflib
    ox = None


def to_oxi(t):
    if isinstance(t, URIRef):
        return ox.NamedNode(str(t))
    if isinstance(t, BNode):
        return ox.BlankNode(str(t))
    if t.language:
        return ox.Literal(str(t), language=t.language)
    if t.datatype:
        return ox.Literal(str(t), datatype=ox.NamedNode(str(t.datatype)))
    return ox.Literal(str(t))


def main():
    g = Graph()
    g.parse(LR7 / "onto.ttl")
    g.parse(LR7 / "onto_data.ttl")
    base = len(g)
    enrich(g)
    bind(g)
    (ROOT / "data").mkdir(exist_ok=True)
    g.serialize(ROOT / "data" / "kb.ttl", format="turtle")
    chk = Graph(); chk.parse(ROOT / "data" / "kb.ttl")            # C1: граф валідний (парситься)
    print(f"kb.ttl: {len(chk)} триплетів (ЛР 7: {base}; додано синтетикою: {len(chk) - base})")

    # JSON-LD: ≥ 20 сутностей (індивіди з типами-класами, без метаонтологічних службових)
    ents = [s for s in sorted(set(g.subjects(RDF.type, OWL.NamedIndividual)), key=str)][:40]
    sub = Graph()
    for s in ents:
        for p, o in g.predicate_objects(s):
            sub.add((s, p, o))
    ctx = {"hr": str(HR), "xsd": "http://www.w3.org/2001/XMLSchema#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
           "owl": "http://www.w3.org/2002/07/owl#", "fullName": str(HR) + "fullName", "directManager": {"@id": str(HR) + "directManager", "@type": "@id"},
           "hasCompetence": {"@id": str(HR) + "hasCompetence", "@type": "@id"}}
    sub.serialize(ROOT / "data" / "kb.jsonld", format="json-ld", context=ctx, indent=1)
    back = Graph(); back.parse(ROOT / "data" / "kb.jsonld", format="json-ld")
    n_ent = len(set(back.subjects()))
    print(f"kb.jsonld: {n_ent} сутностей")

    version_tag, loaded = "kb-1.0.0", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    n_store, engine = len(g), "rdflib (Oxigraph недоступний)"
    n_ind = len(set(g.subjects(RDF.type, OWL.NamedIndividual)))
    if ox:
        store_dir = ROOT / "store"
        shutil.rmtree(store_dir, ignore_errors=True)
        store = ox.Store(str(store_dir))
        gname = ox.NamedNode(GRAPH_IRI)
        for s, p, o in g:
            store.add(ox.Quad(to_oxi(s), to_oxi(p), to_oxi(o), gname))
        q = f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH_IRI}> {{ ?s ?p ?o }} }}"
        n_store = int(next(iter(store.query(q)))["n"].value)
        q2 = ("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { GRAPH <%s> { ?s a <http://www.w3.org/2002/07/owl#NamedIndividual> } }" % GRAPH_IRI)
        n_ind = int(next(iter(store.query(q2)))["n"].value)
        engine = f"Oxigraph (pyoxigraph {version('pyoxigraph')}), persistent store: store/"
        print(f"Oxigraph COUNT: {n_store}; NamedIndividual: {n_ind}")
    rows = [
        {"Поле": "Датасет / сховище", "Значення": engine},
        {"Поле": "Іменований граф", "Значення": GRAPH_IRI},
        {"Поле": "Версія набору", "Значення": version_tag},
        {"Поле": "Дата завантаження", "Значення": loaded},
        {"Поле": "Триплетів (rdflib)", "Значення": len(g)},
        {"Поле": "Триплетів у сховищі (COUNT)", "Значення": n_store},
        {"Поле": "Збіг із rdflib", "Значення": "так" if n_store == len(g) else "НІ"},
        {"Поле": "Іменованих індивідів", "Значення": n_ind},
        {"Поле": "Префікси", "Значення": "hr, owl, rdfs, xsd, skos, org, foaf, schema, esco, dcterms"},
        {"Поле": "JSON-LD (сутностей)", "Значення": n_ent},
        {"Поле": "Бібліотеки", "Значення": f"rdflib {version('rdflib')}"},
    ]
    write(ROOT / "docs" / "load_log.md", "# Журнал завантаження RDF\n\n" + md_table(rows))
    print("docs/load_log.md записано")


if __name__ == "__main__":
    main()
