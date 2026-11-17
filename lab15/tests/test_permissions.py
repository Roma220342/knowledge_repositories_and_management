"""Перевірка прав: інструменти не змінюють базові сховища; з'єднання з БД лише для читання."""
import hashlib, glob, os, sqlite3, subprocess, sys, pytest
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def digest(): return {f: hashlib.sha256(open(f, "rb").read()).hexdigest() for f in sorted(glob.glob(ROOT + "/graph_ro/*.csv") + [ROOT + "/data/store_v1.jsonl", ROOT + "/data/hub.db"])}
def test_db_connection_is_read_only():
    con = sqlite3.connect(f"file:{ROOT}/data/hub.db?mode=ro", uri=True)
    with pytest.raises(sqlite3.OperationalError): con.execute("DROP TABLE fact_training")
def test_base_stores_unchanged_after_scenarios_and_attacks():
    before = digest()
    for cmd in (["tests/run_scenarios.py", "perm"], ["tests/run_attacks.py", "before"]): subprocess.run([sys.executable, ROOT + "/" + cmd[0], cmd[1]], cwd=ROOT, capture_output=True, check=True)
    assert digest() == before
def test_tools_list_matches_manifest_and_only_one_writer():
    import json; man = json.load(open(ROOT + "/agent/tool_manifest.json")); assert set(man) == {"search_kb", "get_record", "graph_lookup", "metric_query", "propose_fact"}
    src = open(ROOT + "/mcp_server/server.py", encoding="utf-8").read(); assert src.count("PF.propose_fact") == 1 and "approve" not in src      # approve недоступний через MCP
