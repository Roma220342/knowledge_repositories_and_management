"""Запуск усіх результатів ЛР 8 по черзі: python scripts/run_all.py"""
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
for step in ("r1_build_kb.py", "r5_links.py", "r2_queries.py", "r3_shacl.py", "r4_t2s.py"):
    print(f"\n=== {step} ===", flush=True)
    r = subprocess.run([sys.executable, "-X", "utf8", str(S / step)], cwd=S)
    if r.returncode:
        print(f"!!! {step} завершився з помилкою (код {r.returncode}); решта кроків продовжується")
print("\nГотово. Надішліть вивід консолі та вміст папок docs/ і results/.")
