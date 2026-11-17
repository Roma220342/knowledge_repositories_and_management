"""MCP-сервер Hub (stdio). Інструменти read-only (search_kb, graph_lookup, metric_query, get_record) + propose_fact (черга пропозицій із HITL).
Роль сесії задає змінна HUB_ROLE; HUB_SECURE=0 вимикає захисти (лише для red-team «до»); HUB_POISON=1 додає отруєні фрагменти до KB (непряма ін'єкція)."""
import os, sys, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT, ROOT + "/agent"]
from mcp.server.mcpserver import MCPServer
from hub.access import Hub
import propose_fact as PF
SECURE = os.environ.get("HUB_SECURE", "1") == "1"; hub = Hub(SECURE, os.environ.get("HUB_ROLE", "employee"), os.environ.get("HUB_POISON") == "1")
mcp = MCPServer("hub-knowledge")
@mcp.tool()
def search_kb(query: str, k: int = 3, role: str = "") -> dict:
    """Гібридний пошук (BM25+dense+reranker) у базі знань політик HR. Лише читання. Використовуй для питань про політики, правила, процедури. k ≤ 5."""
    return hub.search_kb(query, k, role or None)
@mcp.tool()
def get_record(record_id: str, role: str = "") -> dict:
    """Повертає один запис бази знань за id (напр. D12-p01), якщо роль має доступ. Лише читання."""
    return hub.get_record(record_id, role or None)
@mcp.tool()
def graph_lookup(question: str, role: str = "") -> dict:
    """Шаблонний (не довільний) пошук у графі знань: співробітники, посади, компетенції, курси, керівники. Лише читання; чутливі властивості лише для hr/admin."""
    return hub.graph_lookup(question, role or None)
@mcp.tool()
def metric_query(metric: str, by: list[str] = [], where: dict = {}, limit: int = 20) -> dict:
    """Агрегати навчання через семантичний шар (метрики: training_hours, training_cost, cost_per_hour, completion_rate, avg_score_gain, active_learners). Лише SELECT, довільного SQL немає."""
    return hub.metric_query(metric, by, where, limit)
@mcp.tool()
def propose_fact(subject: str, relation: str, object: str, source: str, evidence: str, action: str = "add") -> dict:
    """Пропонує нове знання (id вузлів, relation, джерело, цитата). НЕ записує напряму: валідація → ризик → авто (low) / схвалення людиною (medium) / відмова (high)."""
    return PF.propose_fact(dict(subject=subject, relation=relation, object=object, source=source, evidence=evidence, action=action), actor="agent")
if __name__ == "__main__": mcp.run("stdio")
