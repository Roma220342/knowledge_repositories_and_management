# ЛР 15 — LLM-агент з MCP над Hub
Python 3.13, mcp 2.3.0. seed: 42 (RAG з ЛР 11). «Мозок» агента — офлайн (без API-ключів).
    python3 agent/pin_tools.py                  # маніфест інструментів
    python3 tests/run_scenarios.py after         # сценарії → results/scenarios_after.json
    python3 tests/run_attacks.py before|after    # red team
    python3 tests/hitl_demo.py                   # HITL (схвалення імітовано)
    python3 -m pytest tests/test_permissions.py  # права
    python3 agent/approve.py <id> <reviewer> approve|reject   # людина
