"""Результат 3: SHACL-валідація (pySHACL). Валідний набір = data/kb.ttl, дефектний = kb + 3 навмисні дефекти.
Звіти: results/shacl_*.ttl|txt, docs/shacl_report.md
"""
from importlib.metadata import version

from pyshacl import validate
from rdflib import Graph, Literal, RDF, XSD
from rdflib.namespace import SH

from common import HR, ROOT, local, md_table, write


def summarize(rg):
    rows = []
    for r in rg.subjects(RDF.type, SH.ValidationResult):
        rows.append({
            "вузол": local(rg.value(r, SH.focusNode)),
            "властивість": local(rg.value(r, SH.resultPath)) if rg.value(r, SH.resultPath) else "",
            "обмеження": local(rg.value(r, SH.sourceConstraintComponent)),
            "значення": str(rg.value(r, SH.value) or ""),
            "повідомлення": str(rg.value(r, SH.resultMessage) or ""),
        })
    return sorted(rows, key=lambda x: (x["вузол"], x["властивість"]))


def run(data, shapes, inference="none"):
    conforms, rg, text = validate(data, shacl_graph=shapes, inference=inference, abort_on_first=False)
    return conforms, rg, text


def main():
    shapes = Graph(); shapes.parse(ROOT / "shapes" / "shapes.ttl")
    n_shapes = len(list(shapes.subjects(RDF.type, SH.NodeShape)))
    n_constraints = sum(1 for _ in shapes.subjects(SH.path, None))
    kinds = sorted({local(p) for p in shapes.predicates() if str(p).startswith(str(SH)) and local(p) in
                    ("minCount", "maxCount", "datatype", "class", "minInclusive", "maxInclusive", "pattern", "nodeKind")})
    print(f"форм: {n_shapes}; обмежень (property shapes): {n_constraints}; типи: {kinds}")

    valid = Graph(); valid.parse(ROOT / "data" / "kb.ttl")
    defect = Graph()
    for t in valid:
        defect.add(t)
    # D1: оцінка поза діапазоном 0..10
    defect.remove((HR.petro, HR.productivityScore, None))
    defect.add((HR.petro, HR.productivityScore, Literal("12.5", datatype=XSD.decimal)))
    # D2: табельний номер не за шаблоном
    defect.remove((HR.andriy, HR.employeeId, None))
    defect.add((HR.andriy, HR.employeeId, Literal("EMP-3", datatype=XSD.string)))
    # D3: кандидат претендує на «посаду», яка не є Position (компетенція)
    defect.remove((HR.candidate1, HR.candidateFor, None))
    defect.add((HR.candidate1, HR.candidateFor, HR.pythonProgramming))
    defect.serialize(ROOT / "data" / "kb_defects.ttl", format="turtle")

    out = {}
    res = ROOT / "results"; res.mkdir(exist_ok=True)
    for name, data, inf in (("valid", valid, "none"), ("defect", defect, "none"), ("defect_rdfs", defect, "rdfs")):
        conforms, rg, text = run(data, shapes, inf)
        rg.serialize(res / f"shacl_{name}.ttl", format="turtle")
        write(res / f"shacl_{name}.txt", text)
        out[name] = (conforms, summarize(rg))
        print(f"{name}: conforms={conforms}, порушень={len(out[name][1])}")

    md = ["# SHACL-валідація (pySHACL %s)\n" % version("pyshacl"),
          f"Форм: **{n_shapes}**, обмежень на властивості: **{n_constraints}** (типи: {', '.join(kinds)}).\n",
          "## Навмисні дефекти\n" + md_table([
              {"№": "D1", "Дефект": "petro: productivityScore = 12.5", "Очікується": "порушення діапазону 0..10 (MaxInclusive)"},
              {"№": "D2", "Дефект": "andriy: employeeId = \"EMP-3\"", "Очікується": "порушення шаблону E-NNN (Pattern)"},
              {"№": "D3", "Дефект": "candidate1 candidateFor hr:pythonProgramming", "Очікується": "значення не належить класу Position (Class)"}]),
          f"\n## Валідний набір (data/kb.ttl)\nconforms = **{out['valid'][0]}**, порушень: {len(out['valid'][1])}\n",
          md_table(out["valid"][1]),
          f"\n## Дефектний набір (data/kb_defects.ttl), inference = none\nconforms = **{out['defect'][0]}**, порушень: **{len(out['defect'][1])}**\n",
          md_table(out["defect"][1]),
          f"\n## Дефектний набір, inference = rdfs (порівняння)\nconforms = **{out['defect_rdfs'][0]}**, порушень: **{len(out['defect_rdfs'][1])}**\n",
          md_table(out["defect_rdfs"][1]),
          "\n## Чому SHACL, а не OWL\n"
          "OWL працює у відкритому світі й без припущення унікальності імен: відсутня посада чи другий табельний номер для нього не помилка, "
          "бо відповідний факт може бути невідомим або вказувати на той самий індивід. "
          "SHACL працює із замкненим світом: порушення minCount/maxCount, datatype, діапазону, pattern і class дають явний звіт про валідацію. "
          "Тому обмеження якості даних (формат ідентифікатора, діапазон оцінки, тип значення) виражені в SHACL, а класифікація й виведення знань залишаються в OWL. "
          "Режим inference = rdfs змінює результат валідації (виведені типи можуть маскувати або створювати порушення), тому дані перевіряють без виведення.\n"]
    write(ROOT / "docs" / "shacl_report.md", "\n".join(md))
    print("docs/shacl_report.md записано")


if __name__ == "__main__":
    main()
