import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 11})
R = "/home/claude/lab10/results/"; O = "/home/claude/lab10/figs/"
ch = json.load(open(R + "chunking.json")); ev = json.load(open(R + "eval.json"))["summary"]; ix = json.load(open(R + "index.json"))
# Рис.1 — схема конвеєра
fig, ax = plt.subplots(figsize=(9.2, 3.6)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 40)
def box(x, y, w, h, t, c): ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3", fc=c, ec="#555")); ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=9)
box(1, 28, 16, 9, "kb/*.md\n(21 документ)", "#e8f0fb"); box(21, 28, 16, 9, "Очищення\n+ метадані", "#e8f0fb"); box(41, 28, 16, 9, "corpus.jsonl\n(210 фрагментів)", "#e8f0fb"); box(61, 28, 16, 9, "Chunking\n(hierarchical)", "#fdf0e3"); box(81, 28, 17, 9, "HNSW-індекс\n(LSA-word, M=32)", "#fdf0e3")
box(1, 4, 16, 9, "Запит +\nфільтр метаданих", "#eaf6ea"); box(21, 4, 16, 9, "BM25\n(топ-30)", "#eaf6ea"); box(41, 4, 16, 9, "Dense\n(топ-30)", "#eaf6ea"); box(61, 4, 16, 9, "RRF\n(k=60)", "#eaf6ea"); box(81, 4, 17, 9, "Reranker\nтоп-30 → топ-5", "#eaf6ea")
for a, b in [(17, 21), (37, 41), (57, 61), (77, 81)]: ax.annotate("", (b, 32.5), (a, 32.5), arrowprops=dict(arrowstyle="->"))
for a, b in [(17, 21), (37, 41), (57, 61), (77, 81)]: ax.annotate("", (b, 8.5), (a, 8.5), arrowprops=dict(arrowstyle="->"))
ax.plot([89, 89, 49], [28, 20, 20], "k--", lw=1); ax.annotate("", (49, 13), (49, 20), arrowprops=dict(arrowstyle="->", ls="--")); ax.text(62, 21, "dense-пошук по індексу", fontsize=8)
fig.savefig(O + "fig1_pipeline.png", dpi=200, bbox_inches="tight"); plt.close()
# Рис.2 — chunking
names = list(ch); lab = ["fixed 60/15", "за заголовками", "ієрархічна", "семантична"]
fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4))
x = np.arange(4); ax[0].bar(x - 0.2, [ch[n]["recall5"] for n in names], 0.4, label="recall@5 (10 запитів)", color="#4a7bd0"); ax[0].bar(x + 0.2, [ch[n]["recall5_all37"] for n in names], 0.4, label="recall@5 (37 запитів)", color="#9db8e6")
ax[0].set_xticks(x); ax[0].set_xticklabels(lab, rotation=15); ax[0].set_ylim(0.6, 1.2); ax[0].legend(fontsize=8, loc="upper center"); ax[0].set_title("Повнота")
ax[1].bar(x, [ch[n]["ctx_words"] for n in names], color="#e0944a"); ax[1].set_xticks(x); ax[1].set_xticklabels(lab, rotation=15); ax[1].set_title("Середній розмір контексту (слів)")
for i, n in enumerate(names): ax[1].text(i, ch[n]["ctx_words"] + 1, f"{ch[n]['ctx_words']:.0f}", ha="center", fontsize=9)
fig.tight_layout(); fig.savefig(O + "fig2_chunking.png", dpi=200); plt.close()
# Рис.3 — конфігурації пошуку
cf = ["BM25", "Dense (LSA-word)", "Hybrid (RRF k=60)", "Hybrid + rerank"]; met = [("recall5", "recall@5"), ("recall10", "recall@10"), ("mrr", "MRR"), ("ndcg10", "nDCG@10")]
fig, ax = plt.subplots(figsize=(9.2, 3.6)); w = 0.2; cols = ["#4a7bd0", "#e0944a", "#5ba36b", "#b05bbd"]
for i, (k, l) in enumerate(met): ax.bar(np.arange(4) + (i - 1.5) * w, [ev[c][k] for c in cf], w, label=l, color=cols[i])
ax.set_xticks(range(4)); ax.set_xticklabels(["BM25", "Dense\n(LSA-word)", "Hybrid\n(RRF k=60)", "Hybrid +\nrerank"]); ax.set_ylim(0.6, 1.0); ax.legend(ncol=4, fontsize=8, loc="upper center"); ax.set_ylabel("значення метрики")
fig.tight_layout(); fig.savefig(O + "fig3_eval.png", dpi=200); plt.close(); print("figs ok")
