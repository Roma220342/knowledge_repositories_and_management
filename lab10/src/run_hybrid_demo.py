import sys, json; sys.path.insert(0, "src")
from common import *; from hybrid import Hybrid
F = load_corpus(); H = Hybrid(F); by = H.by_id; out = {}
def show(res): return [(i, by[i]["type"], by[i]["sensitivity"], by[i]["date"]) for i, _ in res]
tests = [
 ("T1: clearance=public", "Чому люди звільнялися найчастіше за результатами вихідних бесід?", dict(max_sensitivity="public")),
 ("T2: clearance=internal", "Чи можна відправляти дані працівників у зовнішній чат-бот зі штучним інтелектом?", dict(max_sensitivity="internal")),
 ("T3: type=policy", "порядок оскарження та перегляд рішення", dict(types={"policy"})),
 ("T4: date>=2026-01-01", "плинність кадрів і рекомендації", dict(date_from="2026-01-01")),
]
for name, q, flt in tests:
    al = H.allowed(**flt)
    before = H.hybrid_rerank(q, 5); after = H.hybrid_rerank(q, 5, al)
    chk = {"T1: clearance=public": lambda r: all(by[i]["sensitivity"] == "public" for i, _ in r),
           "T2: clearance=internal": lambda r: all(by[i]["sensitivity"] in ("public", "internal") for i, _ in r),
           "T3: type=policy": lambda r: all(by[i]["type"] == "policy" for i, _ in r),
           "T4: date>=2026-01-01": lambda r: all(by[i]["date"] >= "2026-01-01" for i, _ in r)}[name]
    out[name] = dict(query=q, allowed_n=len(al), before=show(before), after=show(after), filter_respected=bool(chk(after)),
                     violations_before=int(not chk(before)))
    print(name, len(al), "OK" if chk(after) else "FAIL", "| before violates:", not chk(before))
json.dump(out, open("results/prefilter.json", "w"), indent=1, ensure_ascii=False)
