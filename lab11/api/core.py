"""Результат 3: логіка REST API (автентифікація, ролі, ліміти, валідація, коди помилок), незалежна від веб-фреймворку.
Обгортки: api/main.py (FastAPI — цільовий варіант) і api/asgi_test.py (Starlette — використано для тестів у середовищі без fastapi)."""
import os, sys, time, hmac, hashlib, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from collections import deque
from pydantic import BaseModel, Field, ValidationError
from rag import RAG, ROLE_MAX_SENS
from common import ROOT
SENS = ["public", "internal", "confidential", "restricted"]

class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(default=3, ge=1, le=8)
    use_graph: bool = False

class ApiError(Exception):
    def __init__(self, status, code, msg, headers=None): self.status, self.code, self.msg, self.headers = status, code, msg, headers or {}

class Service:
    """Ключі беруться зі змінної середовища HUB_API_KEYS='ключ1:viewer,ключ2:hr' (у коді та репозиторії ключів немає); зберігаються лише SHA-256 хеші."""
    def __init__(self, rag=None, keys=None, limit=10, window=60.0):
        raw = keys if keys is not None else os.environ.get("HUB_API_KEYS", "")
        self.keys = {hashlib.sha256(k.encode()).hexdigest(): r for k, r in (p.split(":", 1) for p in raw.split(",") if ":" in p)}
        for r in self.keys.values(): assert r in ROLE_MAX_SENS, f"невідома роль {r}"
        self.rag, self.limit, self.window, self.hits, self.lock = rag, limit, window, {}, threading.Lock()
    def auth(self, key):
        if not key: raise ApiError(401, "missing_api_key", "Потрібен заголовок X-API-Key", {"WWW-Authenticate": "ApiKey"})
        h = hashlib.sha256(key.encode()).hexdigest(); role = next((r for k, r in self.keys.items() if hmac.compare_digest(k, h)), None)
        if role is None: raise ApiError(401, "invalid_api_key", "Невірний API-ключ", {"WWW-Authenticate": "ApiKey"})
        now = time.monotonic()
        with self.lock:
            q = self.hits.setdefault(h, deque())
            while q and now - q[0] > self.window: q.popleft()
            if len(q) >= self.limit: raise ApiError(429, "rate_limited", f"Ліміт {self.limit} запитів за {int(self.window)} с", {"Retry-After": str(int(self.window - (now - q[0])) + 1)})
            q.append(now)
        return role
    def health(self): return {"status": "ok", "fragments": len(self.rag.F), "model": self.rag.llm.name}
    def ask(self, key, body):
        role = self.auth(key)
        try: m = AskIn(**(body if isinstance(body, dict) else {}))
        except ValidationError as e: raise ApiError(422, "validation_error", "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()))
        x = self.rag.ask(m.question, role=role, k=m.k, use_graph=m.use_graph)
        return {"answer": x["answer"], "sources": [{"id": c["id"], "title": c.get("title"), "sensitivity": c["sensitivity"], "date": c["date"]} for c in x["context"]],
                "citations_valid": x["citations_valid"], "blocked": x["blocked"], "usage": {"prompt_tokens": x["prompt_tokens"], "completion_tokens": x["completion_tokens"]},
                "latency_ms": x["latency_ms"], "role": role}
    def source(self, key, sid):
        role = self.auth(key); f = self.rag.H.by_id.get(sid)
        if f is None: raise ApiError(404, "not_found", f"Джерело {sid} не знайдено")
        if SENS.index(f["sensitivity"]) > SENS.index(ROLE_MAX_SENS[role]): raise ApiError(403, "forbidden", "Недостатньо прав для цього джерела")
        return {k: f[k] for k in ("id", "doc_id", "title", "section", "type", "date", "sensitivity", "source_url", "text")}
