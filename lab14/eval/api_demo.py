"""Результат 3: демонстрація API (Starlette TestClient): 2 ролі, коди помилок, ліміт запитів. Ключі — лише змінні середовища/тимчасові."""
import sys, os, json; sys.path.insert(0, "src"); sys.path.insert(0, "api")
from starlette.testclient import TestClient
from rag import RAG; from graph_context import Graph; from core import Service; from asgi_test import build
rag = RAG(log_path=None, graph=Graph()); out = []
def call(c, method, url, label, **kw):
    r = c.request(method, url, **kw); b = r.json()
    out.append(dict(label=label, method=method, url=url, status=r.status_code, headers={k: v for k, v in r.headers.items() if k.lower() == "retry-after"}, body=b))
    short = json.dumps(b, ensure_ascii=False)[:150]; print(f"{r.status_code} {label}: {short}"); return r
svc = Service(rag, keys="viewer-demo-key:viewer,hr-demo-key:hr", limit=100); c = TestClient(build(svc))
V, H = {"X-API-Key": "viewer-demo-key"}, {"X-API-Key": "hr-demo-key"}
call(c, "GET", "/health", "health (без ключа)")
Q = {"question": "Який прохідний бал тестування компетенцій?"}
call(c, "POST", "/ask", "ask, роль viewer (confidential недоступний)", json=Q, headers=V)
call(c, "POST", "/ask", "ask, роль hr", json=Q, headers=H)
call(c, "GET", "/sources/D18-p02", "sources/D18-p02, viewer", headers=V)
call(c, "GET", "/sources/D18-p02", "sources/D18-p02, hr", headers=H)
call(c, "GET", "/sources/D99-p99", "sources/невідомий id", headers=H)
call(c, "POST", "/ask", "ask без ключа", json=Q)
call(c, "POST", "/ask", "ask з хибним ключем", json=Q, headers={"X-API-Key": "wrong"})
call(c, "POST", "/ask", "ask, питання закоротке", json={"question": "а"}, headers=H)
call(c, "POST", "/ask", "ask, k поза межами", json={"question": "Скільки триває випробувальний період?", "k": 50}, headers=H)
call(c, "POST", "/ask", "ask, питання про зв'язки з графом", json={"question": "Хто безпосередній керівник Петра Бондаря?", "use_graph": True}, headers=H)
svc2 = Service(rag, keys="limited-key:hr", limit=3, window=60); c2 = TestClient(build(svc2))
for i in range(5): call(c2, "POST", "/ask", f"ліміт 3/хв, запит {i+1}", json={"question": "Скільки місяців триває випробувальний період?"}, headers={"X-API-Key": "limited-key"})
json.dump(out, open("results/api_demo.json", "w"), indent=1, ensure_ascii=False)
