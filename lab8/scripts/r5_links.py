"""Результат 5: зв'язки з Wikidata. Пошук кандидатів -> перевірка (V1) за міткою/описом -> data/links.ttl, docs/links_verification.md.
Потрібен інтернет. Вручну змінити вибір можна у data/links_overrides.json: {"Salary": "Q123"}.
"""
import json
from datetime import date

import requests
from rdflib import Graph, Literal, RDF, URIRef, XSD
from rdflib.namespace import SKOS, RDFS, DCTERMS

from common import HR, LNK, ROOT, add_claims, md_table, write

API = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "LabKnowledgeHub/1.0 (student lab work)"}
WD = "http://www.wikidata.org/entity/"

# локальне поняття, пошуковий запит, слова, які мають бути в описі, визначення
CONCEPTS = [
    ("Employee", "employee", ["person", "employ"], "особа, що перебуває в трудових відносинах з організацією"),
    ("Resume", "curriculum vitae", ["summary", "document", "career"], "документ із відомостями про освіту й досвід кандидата"),
    ("Salary", "salary", ["payment", "remuneration", "pay", "wage"], "винагорода, що виплачується регулярно"),
    ("Bonus", "bonus", ["payment", "reward", "compensation", "additional"], "додаткова винагорода за результати"),
    ("KPI", "key performance indicator", ["performance", "indicator", "measure"], "показник ефективності діяльності"),
    ("Position", "job", ["work", "position", "employment", "occupation"], "посада в організаційній структурі"),
]


def get(params):
    r = requests.get(API, params={**params, "format": "json"}, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    overrides = {}
    p = ROOT / "data" / "links_overrides.json"
    if p.exists():
        overrides = json.load(open(p, encoding="utf-8"))
    g = Graph(); g.bind("lnk", LNK); g.bind("skos", SKOS); g.bind("hr", HR); g.bind("dcterms", DCTERMS)
    rows, claims, n = [], [], 0
    for concept, term, kws, definition in CONCEPTS:
        hits = get({"action": "wbsearchentities", "search": term, "language": "en", "type": "item", "limit": 5})["search"]
        if concept in overrides:
            hits = [h for h in hits if h["id"] == overrides[concept]] or [{"id": overrides[concept], "label": "", "description": ""}]
        chosen = None
        for i, h in enumerate(hits):
            text = (h.get("label", "") + " " + h.get("description", "")).lower()
            ok = any(k in text for k in kws) and "disambiguation" not in text
            exact = h.get("label", "").lower() == term.lower()
            status = "verified" if ok and chosen is None else "rejected"
            if status == "verified":
                chosen = h["id"]
            if status == "rejected" and i > 1:
                continue                                            # у звіті лишаємо максимум два кандидати на поняття
            rel = SKOS.exactMatch if (exact and ok) else SKOS.closeMatch
            conf = 0.9 if exact and ok else 0.7 if ok else 0.3
            reason = (f"збігається ключова ознака (опис містить одне зі слів: {', '.join(kws)})" if status == "verified"
                      else "опис/мітка не відповідає визначенню або кращий кандидат уже обрано")
            n += 1
            l = LNK[f"L{n}"]
            g.add((l, RDF.type, LNK.Link)); g.add((l, LNK.source, HR[concept])); g.add((l, LNK.target, URIRef(WD + h["id"])))
            g.add((l, LNK.relation, rel)); g.add((l, LNK.confidence, Literal(conf, datatype=XSD.decimal)))
            g.add((l, LNK.status, Literal(status))); g.add((l, LNK.verificationLevel, Literal("V1")))
            g.add((l, DCTERMS.date, Literal(date.today().isoformat(), datatype=XSD.date)))
            g.add((l, DCTERMS.source, URIRef(f"https://www.wikidata.org/wiki/{h['id']}")))
            g.add((l, RDFS.comment, Literal(f"Локально: «{definition}». Wikidata: «{h.get('label', '')}» — «{h.get('description', '')}». {reason}.")))
            rows.append({"№": f"L{n}", "поняття": concept, "Wikidata": h["id"], "мітка": h.get("label", ""), "опис": h.get("description", ""),
                         "зв'язок": str(rel).split("#")[-1], "впевненість": conf, "статус": status, "пояснення": reason})
            claims.append([f"link-L{n}", f"hr:{concept} {str(rel).split('#')[-1]} wd:{h['id']}", "факт", f"Wikidata ({h['id']})", "V1", status, reason])
    g.serialize(ROOT / "data" / "links.ttl", format="turtle")
    verified = sum(1 for r in rows if r["статус"] == "verified"); rejected = len(rows) - verified
    write(ROOT / "docs" / "links_verification.md",
          f"# Верифікація зв'язків із Wikidata (V1)\n\nПідтверджено: **{verified}**, відхилено: **{rejected}**.\n\n" + md_table(rows))
    add_claims(claims, reset=True)
    print(f"links.ttl: підтверджено {verified}, відхилено {rejected}")
    print(md_table(rows))


if __name__ == "__main__":
    main()
