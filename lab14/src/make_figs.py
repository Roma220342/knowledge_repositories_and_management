import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(10, 3.4)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 34)
names = ["Запит", "Захист від\nін'єкцій", "Гібридний пошук\n+ pre-filter за ролью", "Reranking\n(топ-k)", "Підграф графа\n(entity linking)", "Промпт rag_v1\n+ LLM", "Перевірка\nцитат", "Відповідь\n+ журнал"]
for i, n in enumerate(names):
    x = 1 + i * 12.4; ax.add_patch(FancyBboxPatch((x, 12), 10.6, 11, boxstyle="round,pad=0.3", fc="#dbeafe" if i not in (4,) else "#fde68a", ec="#1f2937"))
    ax.text(x + 5.3, 17.5, n, ha="center", va="center", fontsize=7.5)
    if i < 7: ax.annotate("", xy=(x + 12.1, 17.5), xytext=(x + 11, 17.5), arrowprops=dict(arrowstyle="->"))
ax.text(50, 5, "Невалідні цитати → «Не знаю»; фрагменти з вказівками → карантин; ролі: viewer < employee < hr < admin", ha="center", fontsize=8)
plt.savefig("figs/fig1_pipeline.png", dpi=200, bbox_inches="tight")
R = {t: json.load(open(f"results/rag_eval_{t}.json"))["summary"] for t in ("base", "k5", "rho08")}
keys = [("context_recall", "context recall"), ("citation_accuracy", "citation accuracy"), ("abstention_rate_noanswer", "abstention (без відп.)"), ("answer_hit_rate", "answer hit")]
fig, ax = plt.subplots(figsize=(8, 3.2)); w = 0.26
for j, (t, lab) in enumerate([("base", "базова k=3, ρ=0.6"), ("k5", "k=5"), ("rho08", "ρ=0.8")]):
    ax.bar([i + (j - 1) * w for i in range(len(keys))], [R[t][k] for k, _ in keys], w, label=lab)
ax.set_xticks(range(len(keys))); ax.set_xticklabels([l for _, l in keys], fontsize=8); ax.set_ylim(0, 1.05); ax.legend(fontsize=8, loc="lower right"); ax.set_title("Метрики до/після оптимізації", fontsize=10)
plt.savefig("figs/fig2_optimization.png", dpi=200, bbox_inches="tight")
