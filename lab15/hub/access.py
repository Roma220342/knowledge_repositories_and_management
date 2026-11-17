"""Функції доступу до сховищ Hub (ЛР 8–14) — ЛИШЕ читання. kb: гібридний пошук (ЛР 11/14), graph: граф (ЛР 9), sql: семантичний шар над OLAP (ЛР 12).
secure=True вмикає захисти: ACL за роллю сесії, карантин фрагментів з ін'єкціями, фільтр чутливих властивостей, білий список запитів."""
import os, sys, re, json, sqlite3, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT + "/hub_src", ROOT + "/semantic"]
from rag import RAG, ROLE_MAX_SENS, is_injection
from graph_context import Graph, REL_UA
import metrics as SEM
EXTRA_PATTERNS = [r"викличи\s+(інструмент|propose|delete)", r"propose_fact", r"видали", r"відповідай\s+(лише|тільки)", r"admin|адмін\w*\s+пароль", r"розкрий"]
def looks_malicious(t): return is_injection(t) or any(re.search(p, t.lower()) for p in EXTRA_PATTERNS)
class Hub:
    def __init__(self, secure=True, role="employee", poison=False):
        self.secure, self.role = secure, role; F = [json.loads(l) for l in open(ROOT + "/data/store_v1.jsonl", encoding="utf-8")]
        if poison: F += [json.loads(l) for l in open(ROOT + "/data/poison_overlay.jsonl", encoding="utf-8")]
        self.rag = RAG(frags=F, log_path="", k=3); self.G = Graph(ROOT + "/graph_ro"); self.db = ROOT + "/data/hub.db"
    def _role(self, role): return self.role if self.secure else (role or self.role)         # безпечний режим ігнорує роль із аргументів
    def search_kb(self, query, k=3, role=None):
        role = self._role(role); k = max(1, min(int(k), 5)); hits, top1 = self.rag.retrieve(query, role, k); wide = self.rag.retrieve(query, role, 5)[0]; out = []; quarantined = []
        for i, s in hits:
            f = self.rag.H.by_id[i]
            if self.secure and looks_malicious(f["text"]): quarantined.append(i); continue
            out.append(dict(id=i, text=f["text"], date=f["date"], sensitivity=f["sensitivity"], score=round(float(s), 3)))
        return dict(hits=out, top1=round(float(top1), 3), thr=round(float(self.rag.thr), 3), quarantined=quarantined, conflicts=self._conflicts([dict(id=i, text=self.rag.H.by_id[i]['text'], score=float(sc)) for i, sc in wide if not (self.secure and looks_malicious(self.rag.H.by_id[i]['text']))], role))
    NUMW = ["один", "одна", "два", "двох", "три", "трьох", "чотири", "п'ят", "шість", "двадцят", "місяц", "відсот"]
    def _nums(self, t): import re; return set(re.findall(r"\d+", t)) | {w for w in self.NUMW[:8] if w in t.lower()}
    def _conflicts(self, hits, role):
        """Виявлення суперечностей (виправлення за аналізом невдач): для релевантних фрагментів із числами шукаємо «двійників» (схожі основи слів, інші числа)."""
        from common import stems; res = {}
        for h in hits:
            if h["score"] < self.rag.thr or not self._nums(h["text"]): continue
            for i, sc in self.rag.retrieve(h["text"], role, 4)[0]:
                o = self.rag.H.by_id[i]
                if i == h["id"] or (self.secure and looks_malicious(o["text"])): continue
                a, b = set(stems(h["text"])), set(stems(o["text"]))
                if len(a & b) / max(1, min(len(a), len(b))) >= 0.6 and self._nums(h["text"]) != self._nums(o["text"]) and self._nums(o["text"]):
                    k = tuple(sorted((h["id"], i))); res[k] = [dict(id=x, text=self.rag.H.by_id[x]["text"].split(". ")[0].rstrip(".") + ".", date=self.rag.H.by_id[x]["date"]) for x in k]
        return list(res.values())
    def get_record(self, rid, role=None):
        role = self._role(role); f = self.rag.H.by_id.get(rid)
        if not f: return dict(error="не знайдено")
        order = ["public", "internal", "confidential", "restricted"]
        if order.index(f["sensitivity"]) > order.index(ROLE_MAX_SENS[role]): return dict(error="доступ заборонено політикою")
        if self.secure and looks_malicious(f["text"]): return dict(error="запис у карантині")
        return dict(id=rid, text=f["text"], date=f["date"], sensitivity=f["sensitivity"])
    def graph_lookup(self, question, role=None):
        role = self._role(role); seeds = self.G.link(question)
        if not seeds: return dict(seeds=[], facts=[])
        edges = self.G.subgraph(seeds, 1, 12, question); facts = self.G.linearize(edges); props = {}
        for s in seeds:
            n = self.G.nodes[s]
            if n["label"] == "Employee":
                p = {k: v for k, v in n["props"].items() if k in ("name", "employeeId", "hireDate", "tenureMonths")}
                if (not self.secure) or role in ("hr", "admin"): p["productivityScore"] = n["props"].get("productivityScore")    # чутливе поле — лише hr/admin
                props[s] = p
        return dict(seeds=seeds, facts=facts, props=props)
    def metric_query(self, metric, by=(), where=None, limit=20):
        if self.secure and ("employee" in by) and self.role not in ("hr", "admin"): return dict(error="розріз за співробітником заборонено для цієї ролі")
        sql = SEM.sql_for(metric, list(by), where or {}, True, min(int(limit), 50))                 # лише метрики/виміри семантичного шару; довільного SQL немає
        con = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True); con.execute("PRAGMA query_only=ON"); dl = time.perf_counter() + 2; con.set_progress_handler(lambda: 1 if time.perf_counter() > dl else 0, 10000)
        try: cur = con.execute(sql); cols = [c[0] for c in cur.description]; rows = cur.fetchall()
        finally: con.close()
        return dict(sql=sql, columns=cols, rows=[list(r) for r in rows], id=f"sql:{metric}")
