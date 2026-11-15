"""Starlette-обгортка тієї ж логіки (api/core.py) — для тестування API без fastapi. Ендпоінти й коди відповідей ідентичні api/main.py."""
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from core import Service, ApiError
def build(svc: Service):
    def wrap(fn):
        async def h(request):
            try: return JSONResponse(await fn(request))
            except ApiError as e: return JSONResponse({"error": {"code": e.code, "message": e.msg}}, e.status, e.headers)
        return h
    async def health(r): return svc.health()
    async def ask(r):
        try: body = await r.json()
        except Exception: body = None
        return svc.ask(r.headers.get("x-api-key"), body)
    async def source(r): return svc.source(r.headers.get("x-api-key"), r.path_params["sid"])
    return Starlette(routes=[Route("/health", wrap(health)), Route("/ask", wrap(ask), methods=["POST"]), Route("/sources/{sid}", wrap(source))])
