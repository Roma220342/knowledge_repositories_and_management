"""REST API Domain Knowledge Hub (FastAPI). Запуск: HUB_API_KEYS='k1:viewer,k2:hr' uvicorn api.main:app --port 8000
Примітка: у середовищі виконання роботи пакет fastapi був недоступний, тому цей файл тут не запускався; та сама логіка (api/core.py) перевірена через Starlette (api/asgi_test.py)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from core import Service, ApiError, AskIn
from rag import RAG
from graph_context import Graph
app = FastAPI(title="Domain Knowledge Hub — RAG API", version="1.0", description="Питання → відповідь із цитатами; ролі: viewer/employee/hr/admin")
svc = Service(RAG(log_path=None, graph=Graph()))
@app.exception_handler(ApiError)
async def api_error(_: Request, e: ApiError): return JSONResponse({"error": {"code": e.code, "message": e.msg}}, e.status, e.headers)
@app.get("/health")
def health(): return svc.health()
@app.post("/ask")
def ask(body: AskIn, x_api_key: str | None = Header(default=None)): return svc.ask(x_api_key, body.model_dump())
@app.get("/sources/{sid}")
def source(sid: str, x_api_key: str | None = Header(default=None)): return svc.source(x_api_key, sid)
