"""Результат 1: RAG-конвеєр. Запит -> захисна перевірка -> гібридний пошук (pre-filter за правами) -> reranking
-> промпт -> LLM -> перевірка цитат -> журнал. LLM-бекенд змінний: 'extractive' (офлайн, без API) або 'anthropic' (потрібен ключ)."""
import re, os, sys, json, time, math
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, SEED, stems, tokens, load_corpus
from hybrid import Hybrid

ROLE_MAX_SENS = {"viewer": "public", "employee": "internal", "hr": "confidential", "admin": "restricted"}
ID_RE = re.compile(r"\[([A-Z]\d+-p\d+|n:[\w-]+)\]")
INJ = [r"ігноруй", r"забудь\s+(усі\s+|всі\s+)?(попередні\s+)?(правила|інструкції)", r"ignore\s+(all\s+)?(previous|prior)", r"системн\w+\s+(промпт|підказк)",
       r"system\s+prompt", r"розкрий\s+(пароль|персональн)", r"відповідай\s+['\"«]?пароль", r"you\s+are\s+now", r"режим\s+розробника"]
ABSTAIN = "Не знаю: у наданих джерелах немає відповіді"
REFUSE = "Запит відхилено політикою безпеки"
def est_tokens(t): return max(1, math.ceil(len(t) / 3.0))      # оцінка: ≈3 символи на токен для української
def is_injection(t): return any(re.search(p, t.lower()) for p in INJ)
NUMW = {"од": "1", "два": "2", "дві": "2", "двох": "2", "три": "3", "трьох": "3", "чотир": "4", "п'ят": "5", "пя": "5", "шіст": "6", "сім": "7", "вісім": "8", "дев'ят": "9", "десят": "10"}
def nums(t):
    out = set(re.findall(r"\d+(?:[.,]\d+)?", t))
    for w in tokens(t):
        for k, v in NUMW.items():
            if w == k or (len(k) > 3 and w.startswith(k)): out.add(v)
    return out
def sentences(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if len(s.strip()) > 8]

class ExtractiveLLM:
    """Офлайн-«модель»: детермінований екстрактивний генератор. Обирає речення контексту з найбільшим перекриттям з питанням,
    цитує [id], виявляє конфлікт чисел між джерелами. Замінник LLM у середовищі без доступу до API (див. звіт)."""
    name = "extractive-v1"
    def __init__(self, rho=0.6): self.rho = rho        # частка від найкращого перекриття, достатня для додаткового речення
    def generate(self, question, ctx, max_sent=2, tau=0.34):
        qs = set(stems(question)); cands = []
        for c in ctx:
            for s in sentences(c["text"]):
                ss = set(stems(s)); ov = len(qs & ss) / max(1, len(qs)); cands.append((ov, c, s, ss))
        cands.sort(key=lambda x: -x[0])
        if not cands or cands[0][0] < tau: return ABSTAIN
        top = cands[0]; out = [top]
        # конфлікт: схоже речення з іншого фрагмента, але інші числа
        for ov, c, s, ss in cands[1:]:
            if c["id"] != top[1]["id"] and ov >= tau and len(top[3] & ss) / max(1, len(top[3] | ss)) >= 0.3 and nums(s) and nums(top[2]) and nums(s) != nums(top[2]):
                a, b = sorted([top, (ov, c, s, ss)], key=lambda x: x[1]["date"])
                return (f"Джерела суперечать: {a[2]} [{a[1]['id']}] ({a[1]['date']}) і {b[2]} [{b[1]['id']}] ({b[1]['date']}). Новішим є [{b[1]['id']}].")
        for ov, c, s, ss in cands[1:]:
            if len(out) >= max_sent: break
            if ov >= max(tau, self.rho * top[0]) and c["id"] not in {o[1]["id"] for o in out}: out.append((ov, c, s, ss))
        return " ".join(f"{s} [{c['id']}]" for _, c, s, _ in out)

class AnthropicLLM:
    """Бекенд LLM через Anthropic Messages API (ключ — зі змінної середовища ANTHROPIC_API_KEY). У цьому середовищі НЕ запускався."""
    name = "anthropic"
    def __init__(self, model=None): self.model = model or os.environ.get("HUB_MODEL", "claude-sonnet-5-5")
    def generate(self, question, ctx, **kw):
        import urllib.request
        sys_prompt = open(f"{ROOT}/prompts/rag_v1.md", encoding="utf-8").read()
        ctx_txt = "\n".join(f"[{c['id']}] ({c['date']}) {c['text']}" for c in ctx)
        body = json.dumps({"model": self.model, "max_tokens": 400, "temperature": 0, "system": sys_prompt,
                           "messages": [{"role": "user", "content": f"КОНТЕКСТ:\n{ctx_txt}\n\nПИТАННЯ: {question}"}]}).encode()
        req = urllib.request.Request(os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com") + "/v1/messages", body,
              {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())["content"][0]["text"]

class RAG:
    def __init__(self, frags=None, llm=None, k=3, role="hr", log_path=None, thr=None, extra=None, graph=None):
        self.F = (frags or load_corpus()) + (extra or []); self.H = Hybrid(self.F); self.llm = llm or ExtractiveLLM()
        self.k, self.role, self.graph = k, role, graph
        self.log_path = log_path if log_path is not None else f"{ROOT}/logs/rag_log.jsonl"
        self.thr = thr if thr is not None else self.calibrate()
    def calibrate(self):
        """Поріг відсікання: половина медіани top-1 reranker-а на запитах золотого набору ЛР 10 із відповіддю (як у ЛР 10)."""
        g = [json.loads(l) for l in open(f"{ROOT}/eval/gold_lab10.jsonl", encoding="utf-8")]
        tops = [self.H.hybrid_rerank(x["query"], 1)[0][1] for x in g if x["relevant"]]
        import numpy as np; return float(np.median(tops) * 0.5)
    def retrieve(self, q, role=None, k=None):
        allowed = self.H.allowed(max_sensitivity=ROLE_MAX_SENS[role or self.role])
        res = self.H.hybrid_rerank(q, 10, allowed); return res[: (k or self.k)], (res[0][1] if res else 0.0)
    def build_prompt(self, q, ctx):
        sys_p = open(f"{ROOT}/prompts/rag_v1.md", encoding="utf-8").read()
        return sys_p + "\n\nКОНТЕКСТ:\n" + "\n".join(f"[{c['id']}] ({c['date']}) {c['text']}" for c in ctx) + f"\n\nПИТАННЯ: {q}"
    def validate_citations(self, answer, ctx_ids):
        cited = ID_RE.findall(answer); bad = [c for c in cited if c not in ctx_ids]
        return dict(cited=cited, invalid=bad, valid=not bad)
    def ask(self, q, role=None, k=None, use_graph=False):
        t0 = time.perf_counter(); role = role or self.role; k = k or self.k; quarantined = []
        if is_injection(q):
            ans, ctx, top1, blocked = REFUSE, [], 0.0, "query_injection"; ctx_ids = []
        else:
            hits, top1 = self.retrieve(q, role, k); ctx = []
            for i, s in hits:
                f = self.H.by_id[i]
                if is_injection(f["text"]): quarantined.append(i); continue      # непряма ін'єкція: фрагмент в карантин
                ctx.append(f)
            blocked = None
            if use_graph and self.graph is not None:
                g = self.graph.context(q); ctx = ctx + [dict(id=x["id"], text=x["text"], date="graph", sensitivity="internal") for x in g]
            ctx_ids = {c["id"] for c in ctx} | {m for c in ctx if c["date"] == "graph" for m in re.findall(r"\[(n:[\w]+)\]", c["text"])}   # id фрагментів + id вузлів підграфа
            ans = ABSTAIN if (top1 < self.thr and not (use_graph and any(c["date"] == "graph" for c in ctx))) or not ctx else self.llm.generate(q, ctx, max_sent=(8 if (use_graph and any(c['date']=='graph' for c in ctx)) else 2))
        v = self.validate_citations(ans, set(ctx_ids))
        if not v["valid"]: ans = ABSTAIN; v = self.validate_citations(ans, set(ctx_ids)); v["repaired"] = True   # невалідні цитати -> відмова
        prompt = self.build_prompt(q, ctx) if ctx else ""
        rec = dict(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), query=q, role=role, k=k, sources=[c["id"] for c in ctx], quarantined=quarantined, blocked=blocked,
                   top1_score=round(top1, 4), answer=ans, cited=v["cited"], citations_valid=v["valid"], model=self.llm.name,
                   prompt_tokens=est_tokens(prompt) if ctx else est_tokens(q), completion_tokens=est_tokens(ans), latency_ms=round((time.perf_counter() - t0) * 1000, 3))
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as fh: fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        rec["context"] = ctx; return rec
