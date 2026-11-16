"""Інструмент: інваріанти графа (Python-еквіваленти Cypher; SHACL-версія — quality/shapes.ttl)."""
def test_13_occupies_is_functional(rels):
    d = {}
    for r in rels["rels_OCCUPIES__Employee__Position.csv"]: d.setdefault(r["from"], set()).add(r["to"])
    bad = {k: v for k, v in d.items() if len(v) > 1}; assert not bad, bad
def test_14_manager_hierarchy_acyclic(rels):
    g = {}
    for r in rels["rels_DIRECT_MANAGER__Employee__Employee.csv"]: g.setdefault(r["from"], set()).add(r["to"])
    def cyc(n, path):
        if n in path: return path[path.index(n):] + [n]
        for m in g.get(n, ()): 
            c = cyc(m, path + [n])
            if c: return c
    found = [c for n in g if (c := cyc(n, []))]; assert not found, found[:2]
def test_15_no_dangling_edges(rels, nodes):
    bad = [(n, r["from"], r["to"]) for n, rs in rels.items() for r in rs if r["from"] not in nodes or r["to"] not in nodes]; assert not bad, bad[:5]
