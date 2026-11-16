"""Локальний «gate» (і крок CI): запускає перевірки, пише лог, звіт-таблицю та тренд; код виходу ≠ 0 при порушеннях.
Використання: python3 quality/gate.py <мітка> [store.jsonl] [graph_dir]"""
import sys, os, subprocess, re, csv, datetime
Q = os.path.dirname(os.path.abspath(__file__)); R = Q + "/.."; label = sys.argv[1] if len(sys.argv) > 1 else "v1"
env = dict(os.environ); 
if len(sys.argv) > 2: env["QUALITY_STORE"] = os.path.abspath(sys.argv[2])
if len(sys.argv) > 3: env["QUALITY_GRAPH"] = os.path.abspath(sys.argv[3])
p = subprocess.run([sys.executable, "-m", "pytest", Q + "/tests", "-rA", "--tb=line", "-q", "-p", "no:cacheprovider"], capture_output=True, text=True, env=env, cwd=R)
os.makedirs(Q + "/logs", exist_ok=True); open(f"{Q}/logs/gate_{label}.log", "w", encoding="utf-8").write(p.stdout + p.stderr)
res = re.findall(r"^(PASSED|FAILED) quality/tests/(\w+)\.py::(test_\d+_\w+)", p.stdout, re.M); tool = {"test_json_schema": "JSON Schema", "test_store_pytest": "pytest", "test_sql_invariants": "SQL (SQLite)", "test_graph_invariants": "graph invariants"}
ok = sum(s == "PASSED" for s, _, _ in res); bad = len(res) - ok
rows = "\n".join(f"| {n} | {tool[f]} | {'✅' if s == 'PASSED' else '❌'} |" for s, f, n in sorted(res, key=lambda x: x[2]))
open(f"{Q}/report_{label}.md", "w", encoding="utf-8").write(f"# Звіт перевірок: {label}\nПройдено {ok}, провалено {bad}\n\n| перевірка | інструмент | статус |\n|--|--|--|\n{rows}\n")
tr = Q + "/trend.csv"; new = not os.path.exists(tr); w = csv.writer(open(tr, "a", newline="")); 
if new: w.writerow(["date", "label", "passed", "failed"])
w.writerow([datetime.date(2026, 11, 16).isoformat(), label, ok, bad]); print(f"gate[{label}]: passed={ok} failed={bad}"); sys.exit(1 if bad else 0)
