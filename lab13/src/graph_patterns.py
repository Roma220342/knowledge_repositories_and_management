"""Нормалізація/зв'язування, експорт у Cypher і Turtle з provenance, перевірка запитом (SQLite), асоціативні правила з перевіркою на випадковість. seed=13"""
import json, sys, os, random, itertools, sqlite3, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *; import extract_rules as X
rnd = random.Random(13)
pred = [json.loads(l) for l in open(R + "/results/pred_rules_dev_v1.jsonl", encoding="utf-8")] + [json.loads(l) for l in open(R + "/results/pred_llm_test.jsonl", encoding="utf-8")]
mention_cache = {}
def offs(r):   # офсет суб'єкта для provenance (для LLM — початок evidence)
    return (r.get("subj", {}).get("start") if isinstance(r.get("subj"), dict) and "start" in r["subj"] else r["evidence"]["start"])
rows = {}
for r in pred:
    k = (r["doc"], r["subj"]["id"], r["rel"], r["obj"]["id"]); rows.setdefault(k, r)       # дедуплікація
lab = {**{i: n for i, n in X.emps.items()}, **X.poss, **X.DEPS, **{k: v[0] for k, v in X.SKILLS.items()}, **X.COURSES}
ent = {}
for (d, s, rel, o), r in rows.items():
    for e in (s, o): ent[e] = lab.get(e, e)
SK = {"HAS_POSITION", "WORKS_IN", "HAS_SKILL", "COMPLETED", "REPORTS_TO", "REQUIRES_SKILL"}
# --- Cypher
cy = ["// Автозгенеровано src/graph_patterns.py", "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;"]
for e, n in sorted(ent.items()): cy.append(f"MERGE (:Entity {{id:'{e}', name:'{n}'}});")
for (d, s, rel, o), r in sorted(rows.items()):
    cy.append(f"MATCH (a:Entity {{id:'{s}'}}),(b:Entity {{id:'{o}'}}) MERGE (a)-[:{rel} {{source:'{d}', offset:{r['evidence']['start']}, model:'{r['model']}', version:'{r['version']}', confidence:{r['confidence'] if r['confidence'] is not None else 'null'}}}]->(b);")
cy.append("// Запит-доказ:\n// MATCH (p:Entity {id:'olena'})-[r]->(x) RETURN type(r), x.name, r.source, r.offset, r.model, r.confidence;")
open(R + "/data/graph_load.cypher", "w", encoding="utf-8").write("\n".join(cy) + "\n")
# --- Turtle (RDF-reification: кожне твердження — вузол із provenance)
tt = ["@prefix hub: <http://example.org/hub#> .", "@prefix prov: <http://www.w3.org/ns/prov#> .", "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> ."]
for e, n in sorted(ent.items()): tt.append(f'hub:{e} rdfs:label "{n}"@uk .')
for i, ((d, s, rel, o), r) in enumerate(sorted(rows.items())):
    tt.append(f'hub:{s} hub:{rel} hub:{o} .\nhub:stmt{i} a rdf:Statement ; rdf:subject hub:{s} ; rdf:predicate hub:{rel} ; rdf:object hub:{o} ; prov:wasDerivedFrom "{d}" ; hub:offset {r["evidence"]["start"]} ; prov:wasGeneratedBy "{r["model"]}/{r["version"]}" ; hub:confidence {r["confidence"] if r["confidence"] is not None else 0} .')
open(R + "/data/graph_load.ttl", "w", encoding="utf-8").write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n" + "\n".join(tt) + "\n")
# --- Запит-доказ через SQLite
con = sqlite3.connect(":memory:"); con.execute("create table t(subj,rel,obj,source,off,model,version,conf)")
con.executemany("insert into t values(?,?,?,?,?,?,?,?)", [(s, rel, o, d, r["evidence"]["start"], r["model"], r["version"], r["confidence"]) for (d, s, rel, o), r in rows.items()])
proof = con.execute("select * from t where subj='olena' order by source, off limit 5").fetchall()
# --- Асоціативні правила: транзакції = співробітники; елементи — навички, курси, відділ
tx = collections.defaultdict(set)
for (d, s, rel, o) in rows:
    if rel in ("HAS_SKILL", "COMPLETED", "WORKS_IN", "HAS_POSITION") and s in X.emps: tx[s].add(f"{rel}:{o}")
T = list(tx.values()); n = len(T)
def sup(S, T=T): return sum(1 for t in T if S <= t) / len(T)
items = sorted({i for t in T for i in t}); res = []
for a, b in itertools.permutations(items, 2):
    if a.split(":")[0] == b.split(":")[0] and a.split(":")[0] in ("HAS_POSITION", "WORKS_IN"): continue
    sab = sup({a, b}); 
    if sab * n < 3: continue
    sa, sb = sup({a}), sup({b}); res.append(dict(rule=f"{a} → {b}", support=round(sab, 3), confidence=round(sab / sa, 3), lift=round(sab / (sa * sb), 2), n=int(sab * n)))
res.sort(key=lambda r: (-r["lift"], -r["support"])); top = res[:5]
def perm_p(rule, B=2000):
    a, b = rule.split(" → "); obs = sup({a, b}); cnt = 0; ppl = list(tx)
    for _ in range(B):   # випадкове перемішування: елементи b призначаються іншим людям (зберігаємо частоти)
        owners = [t for t in T]; bs = [b in t for t in T]; rnd.shuffle(bs)
        cnt += sum(1 for t, hb in zip(T, bs) if a in t and hb) / n >= obs
    return (cnt + 1) / (B + 1)
half = lambda r, part: (lambda S: (sup(set(r.split(" → ")), S), len(S)))(part)
H1, H2 = T[::2], T[1::2]
for r in top:
    r["p_perm"] = round(perm_p(r["rule"]), 3); a, b = r["rule"].split(" → ")
    r["sup_half1"], r["sup_half2"] = round(sup({a, b}, H1), 3), round(sup({a, b}, H2), 3)
    r["decision"] = "у знання" if r["p_perm"] < 0.05 / len(res) else "відхилити"      # поправка Бонферроні на кількість перевірених правил
json.dump(dict(entities=len(ent), triples=len(rows), transactions=n, rules_tested=len(res), proof=proof, top=top), open(R + "/results/patterns.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(ent), len(rows), n, len(res)); [print(r) for r in top]; print(proof[:3])
