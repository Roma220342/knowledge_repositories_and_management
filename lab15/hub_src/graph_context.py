"""Результат 2: підграф із графа знань у контексті. Граф ЛР 9 читається з CSV (graph_data/) у пам'ять; клас Neo4jGraph — адаптер
для реального сервера (Cypher), у цьому середовищі не запускався. Entity linking -> підграф 1–2 кроки з лімітом -> лінеаризація з ID."""
import csv, glob, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, tokens

REL_UA = {"DIRECT_MANAGER": "є безпосереднім керівником для (підпорядковується)", "REQUIRES_COMPETENCE": "вимагає компетенцію",
          "OCCUPIES": "займає посаду", "HAS_COMPETENCE": "має компетенцію", "COMPLETED_COURSE": "завершив(ла) курс",
          "HAS_SUB_PROCESS": "має підпроцес", "CANDIDATE_FOR": "кандидат на посаду", "IN_STATE": "перебуває у стані"}
REL_UA["DIRECT_MANAGER"] = "має безпосереднього керівника"
SYN = {"negotiation": ["переговор", "перемовин", "negotiation"], "pythonProgramming": ["python програмування", "програмування python"],
       "teamCommunication": ["командна комунікація", "комунікація"], "hrAnalytics": ["hr-аналітика", "hr аналітика"],
       "negotiationCourse": ["ефективні перемовини", "курс перемовин"], "pythonAdvancedCourse": ["python advanced"]}
def _p(w, n=4): return w[:n]
def _camel(a): return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", a)

class Graph:
    def __init__(self, d=None):
        d = d or f"{ROOT}/graph_data"; self.nodes, self.out, self.inn = {}, {}, {}
        for f in glob.glob(f"{d}/nodes_*.csv"):
            lab = os.path.basename(f)[6:-4]
            for r in csv.DictReader(open(f, encoding="utf-8")): self.nodes[r["id"]] = dict(id=r["id"], name=r["name"], label=lab, props=r)
        self.edges = []
        for f in glob.glob(f"{d}/rels_*.csv"):
            t = os.path.basename(f)[5:-4].split("__")[0]
            for r in csv.DictReader(open(f, encoding="utf-8")):
                if r["from"] in self.nodes and r["to"] in self.nodes:
                    e = (r["from"], t, r["to"], r.get("source", ""), r.get("confidence", "")); self.edges.append(e)
                    self.out.setdefault(r["from"], []).append(e); self.inn.setdefault(r["to"], []).append(e)
        self.vocab = {}
        for nid, n in self.nodes.items():
            if n["label"] in ("Employee", "Position", "Competence", "Course"):
                k = 4 if n["label"] == "Employee" else 6          # імена змінюються за відмінками -> коротший префікс
                self.vocab[nid] = [[_p(w, k) for w in tokens(_camel(a))] for a in [n["name"]] + SYN.get(nid, []) if tokens(a)]
        self.klen = {nid: (4 if self.nodes[nid]["label"] == "Employee" else 6) for nid in self.vocab}
    def link(self, q):
        """Entity linking: вузол зв'язується, якщо всі префікси токенів його назви/синоніма (4 символи для імен, 6 для решти) є в запиті."""
        found = []
        for nid, variants in self.vocab.items():
            qp = {_p(w, self.klen[nid]) for w in tokens(q)}
            if any(v and all(p in qp for p in v) for v in variants): found.append(nid)
        return found
    def subgraph(self, seeds, hops=1, limit=25, q=""):
        """Підграф навколо seeds (hops кроків). Ребра ранжуються за збігом типу зв'язку з питанням, потім за близькістю до seed; ліміт — limit ребер."""
        from common import stems
        qs = set(stems(q)); S = set(seeds); layer = set(seeds); seen, cand = set(), []
        for h in range(hops):
            nxt = set()
            for n in layer:
                for e in self.out.get(n, []) + self.inn.get(n, []):
                    if e in seen: continue
                    seen.add(e); rel = len(qs & set(stems(REL_UA.get(e[1], e[1])))); cand.append((-rel, h, e)); nxt |= {e[0], e[2]}
            layer = nxt - S
        cand.sort(key=lambda x: (x[0], x[1])); return [e for _, _, e in cand[:limit]]
    def linearize(self, edges):
        out = []
        for a, t, b, src, conf in edges:
            A, B = self.nodes[a], self.nodes[b]
            out.append(dict(id=f"n:{a}-{t}-{b}", text=f"[n:{a}] {A['name']} ({A['label']}) {REL_UA.get(t, t)} [n:{b}] {B['name']} ({B['label']}). Джерело: {src}, довіра {conf}."))
        return out
    def context(self, q, hops=1, limit=25):
        seeds = self.link(q)
        return self.linearize(self.subgraph(seeds, hops, limit, q)) if seeds else []
    def info(self, q): s = self.link(q); return dict(seeds=s, edges=len(self.subgraph(s, 1, 25, q)) if s else 0)

class Neo4jGraph:
    """Адаптер до Neo4j із ЛР 9 (не запускався в цьому середовищі). Змінні: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD."""
    Q = "MATCH (s {id:$id})-[r*1..%d]-(n) RETURN s.id AS a, type(r[0]) AS t, n.id AS b LIMIT $limit"
    def __init__(self):
        from neo4j import GraphDatabase
        self.drv = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
