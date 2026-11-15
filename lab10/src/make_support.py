import json, csv, collections, os
R = "results/"; J = lambda n: json.load(open(R + n, encoding="utf-8"))
cs, chk, ixr, pre, kp = J("corpus_stats.json"), J("chunking.json"), J("index.json"), J("prefilter.json"), J("kappa.json")
EV = J("eval.json"); ev, pq = EV["summary"], EV["per_q"]
G = {json.loads(l)["qid"]: json.loads(l) for l in open("eval/gold.jsonl", encoding="utf-8")}
# контроль: пояснення прикладів у звіті відповідають даним
assert pq["q16"]["BM25"]["top"][0] == "D18-p02" and pq["q16"]["Hybrid (RRF k=60)"]["top"][0] == "D18-p07"
assert pq["q14"]["Hybrid (RRF k=60)"]["top"][0] == "D03-p02" and pq["q14"]["Dense (LSA-word)"]["top"][0] != "D03-p02"
def tbl(h, rows): return "\n".join(["| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])
L = {"fixed_60_15": "Фіксований розмір 60 слів, overlap 15", "by_heading": "За заголовками (розділ)", "hierarchical": "Ієрархічна (parent–child)", "semantic": "Семантична (злиття сусідніх абзаців, cos>0,12)"}
open("docs/corpus_card.md", "w", encoding="utf-8").write(f"""# Картка корпусу HR-Hub
- **Документи:** {cs['n_docs']} (kb/D01–D21.md); **фрагменти:** {cs['n_frags']}; слів {cs['words_total']} (у середньому {cs['words_mean']} на фрагмент); мова: українська (uk).
- **Джерела:** синтетичні внутрішні HR-документи вигаданої ІТ-компанії (положення, регламенти, методики, звіти, кейс, FAQ), згенеровані LLM (Claude Sonnet 5.5, 2026-11-11) за темою курсу; `source_url` має форму `internal://hub/kb/Dxx`. Реальних персональних даних немає.
- **Ліцензія:** CC BY 4.0 для навчального використання в межах курсу; тексти не є копіями сторонніх джерел. Правові норми (КЗпП, закони про відпустки та про захист персональних даних) цитуються описово, їх треба звіряти з чинною редакцією (див. claims/claims.csv).
- **Типи:** {cs['by_type']}. **Чутливість (фрагменти):** {cs['by_sens']}.
- **Правила очищення (src/build_corpus.py):** R1 «хлібні крихти» `Головна >`; R2 «Сторінка N з M»; R3 рядки `©`; R4 кнопки `Наверх/Поділитися/Друкувати`; R5 cookie-банер; R6 нормалізація пробілів. Видалено {cs['removed_total']} рядків із {cs['raw_lines']} ({cs['removed']}).
- **Метадані:** doc_id, title, section, type, date, sensitivity, source_url (+ id, section_idx, para_idx, lang, n_words).
- **Обмежений доступ:** sensitivity ∈ {{public, internal, confidential, restricted}}; рівень документа успадковується фрагментом, а абзаци з персональними деталями кейсу помічено `restricted` вручну ([R] у джерелі). Обмежений доступ = confidential або restricted ({cs['by_sens'].get('confidential',0)+cs['by_sens'].get('restricted',0)} фрагментів).
- **Відомі прогалини:** немає документів про охорону праці, трудові спори, податки, релокацію, корпоративний транспорт (використано як запити без відповіді); корпус невеликий (≈4 тис. слів), тому метрики мають широкі довірчі інтервали.
""")
open("docs/chunking_cmp.md", "w", encoding="utf-8").write("# Порівняння стратегій chunking\nМодель embeddings однакова: LSA-char (128d), HNSW M=32. recall@5 і MRR — на 10 тестових запитах (q02,q06,q10,q14,q18,q21,q25,q30,q33,q36); контрольно — recall@5 і nDCG@10 на всіх 37 запитах із відповіддю. Контекст = середня довжина (слів) топ-5 chunk-ів, які отримує LLM.\n\n" + tbl(["Стратегія", "chunk-ів", "сер. chunk, слів", "recall@5 (10)", "MRR (10)", "контекст, слів", "recall@5 (37)", "nDCG@10 (37)"], [[L[k], v["n_chunks"], v["avg_chunk_words"], v["recall5"], v["mrr"], v["ctx_words"], v["recall5_all37"], v["ndcg10_all37"]] for k, v in chk.items()]) + """

**Вибір: ієрархічна (parent–child).** recall@5 такий самий, як у найкращих (1,00 на 10 запитах; 0,928 проти 0,932 у «за заголовками» на 37), а контекст для LLM ≈40 слів — майже той самий (39,9 проти 40,6). «За заголовками» має вищий MRR (1,00 проти 0,85) і nDCG@10, проте різниця — 1–2 запити й у межах шуму. Ієрархічна дає індексацію на рівні фрагмента: точні метадані sensitivity/дата для фільтрації, розмітка золотого набору на рівні фрагмента, а LLM отримує батьківський розділ. Фіксоване вікно ріже думки на межі розділів (контекст 58 слів), семантична стратегія гірша за recall.
""")
m = ixr["models"]
open("docs/embeddings_cmp.md", "w", encoding="utf-8").write(f"""# Порівняння моделей embeddings (HNSW)
> **Відхилення від завдання:** у середовищі виконання немає доступу до HuggingFace, тому замість multilingual-e5 порівняно дві щільні моделі LSA (TF-IDF + SVD, 128d): `lsa-word` (стеми + біграми) і `lsa-char` (символьні 3–5-грами). Адаптер `STEmbedder` для e5 є в src/index.py (не запускався тут).

Параметри HNSW: M=32, efConstruction=80, efSearch=64, метрика — inner product на нормованих векторах; {m['lsa-word']['n']} векторів; пам'ять векторів {m['lsa-word']['mem_kb']} КБ.

""" + tbl(["Модель", "час побудови, с", "затримка пошуку (сер./p95), мс", "recall@5 (20 запитів)", "MRR"], [[k, v["build_s"], f"{v['lat_mean_ms']} / {v['lat_p95_ms']}", v["recall5"], v["mrr"]] for k, v in m.items()]) + "\n\nВплив параметрів (lsa-char): " + "; ".join(f"M={s['M']}, efSearch={s['efSearch']}: recall@5={s['recall5']}, {s['lat_mean_ms']} мс" for s in ixr["hnsw_sweep"]) + f"""

**Мова:** українська морфологічно багата. `lsa-word` із префіксним стемером точніша на 20 запитах; англомовні запити (3 шт.) обидві моделі не знаходять (recall@5 = {ixr['english']['lsa-word']['recall5']}), бо кросмовних знань немає — для двомовних корпусів потрібна multilingual-модель.

## Процедура оновлення
Upsert: новий вектор додається в HNSW, старий вектор позначається tombstone і відфільтровується під час пошуку; delete — tombstone; compact — перебудова графа без «мертвих» вузлів. Словник моделі фіксований: при значному дрейфі лексики потрібне перенавчання (refit).

""" + tbl(["Документ", "upsert, мс", "нова версія top-1", "стара версія зникла", "видалено фрагментів", "витік у топ-10 після delete"], [[u["doc"], u["upsert_ms"], u["new_top1"], u["old_version_absent"], d["deleted"], d["leaked_in_top10"]] for u, d in zip(ixr["update"]["upsert"], ixr["update"]["delete"])]) + f"\n\nЖивих фрагментів: {ixr['update']['live_before_delete']} → {ixr['update']['live_after_delete']}; розмір індексу до/після compact: {ixr['update']['index_size_before_compact']} → {ixr['update']['index_size_after_compact']}.\n")
fx = ev["_examples"]
def ex_row(q): d = pq[q]; return [q, G[q]["query"], ", ".join(G[q]["relevant"])] + [str(d[k]["top"][:2]).replace("'", "") for k in ["BM25", "Dense (LSA-word)", "Hybrid (RRF k=60)", "Hybrid + rerank"]]
open("docs/hybrid_report.md", "w", encoding="utf-8").write("# Гібридний пошук і reranking\nBM25 (rank_bm25, k1=1,5, b=0,75, префіксний стемер 6 символів) + dense (LSA-word, HNSW) → RRF (k=60) → reranker топ-30→топ-5/10. Reranker — легка оцінка пари (0,4·косинус char-TF-IDF + 0,4·покриття основ запиту + 0,2·збіг біграм); вага задана апріорі, не підбиралась на золотому наборі. Це заміна cross-encoder (немає доступу до HuggingFace); у вашому середовищі підключіть `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.\n\n## Pre-filter\n" + tbl(["Тест", "запит", "дозволено", "порушень до фільтра", "фільтр дотримано"], [[k, v["query"], v["allowed_n"], bool(v["violations_before"]), v["filter_respected"]] for k, v in pre.items()]) + "\n\n## Приклади (топ-2 id; перший — найкращий)\n" + tbl(["qid", "запит", "релевантні", "BM25", "Dense", "Hybrid", "Hybrid+rerank"], [ex_row(q) for q in fx["win"] + fx["lose"]]) + "\n\nВиграш: q24, q14, q01 — точні терміни («заборонено звільняти», «оперативний/перспективний», «формула») виводять правильний фрагмент на 1-ше місце в BM25, а dense ставить на 1–3 місце тематичного «сусіда»; RRF зберігає лексичну точність. Програш: q16 — число «65» збігається лише лексично (BM25: 1-ше місце), а dense впевнено ставить на 1-ше місце сусідній абзац цього ж звіту (D18-p07), RRF ігнорує величини балів, тому гібрид опускає правильний фрагмент на 2-ге місце.\n")
cf = ["BM25", "Dense (LSA-word)", "Dense (LSA-char)", "Hybrid (RRF k=60)", "Hybrid + rerank"]
na = ev["_no_answer"]
open("docs/search_eval.md", "w", encoding="utf-8").write(f"""# Оцінювання пошуку
Золотий набір eval/gold.jsonl: 42 запити (16 ключових слів, 12 перефразувань, 9 багатокрокових, 5 без відповіді); релевантність на рівні фрагмента. Метрики — на 37 запитах із відповіддю; одиниця пошуку — фрагмент (hierarchical-child).

""" + tbl(["Конфігурація", "recall@5", "recall@10", "MRR", "nDCG@10", "затримка, мс (сер.)", "p95, мс", "95% ДІ recall@5"], [[c, ev[c]["recall5"], ev[c]["recall10"], ev[c]["mrr"], ev[c]["ndcg10"], ev[c]["lat_ms"], ev[c]["lat_p95_ms"], ev[c]["recall5_ci95"]] for c in cf]) + "\n\nMRR за типами запитів: " + "; ".join(f"{c}: {ev[c]['mrr_by_type']}" for c in cf) + f"""

**κ (Cohen):** {kp['kappa']} на {kp['n_queries']} запитах / {kp['n_pairs']} пар (збіг {kp['observed_agreement']}). Розмітник B — **автоматичне правило**, а не людина (див. eval/kappa.py); для захисту замініть на розмітку другого студента (`python eval/kappa.py --human`).

**Запити без відповіді:** середній бал топ-1 reranker-а {na['top1_noanswer_mean']} проти {na['top1_answerable_mean']} для запитів із відповіддю; поріг {na['threshold']} відсікає {na['rejected_noans']} із {na['n_noans']} безвідповідних і зберігає {na['kept_answerable']} із {na['n_ans']} відповідних.

**Вибір для ЛР 11: Hybrid + rerank.** Найвищі recall@10 ({ev['Hybrid + rerank']['recall10']}) і nDCG@10 ({ev['Hybrid + rerank']['ndcg10']}), дозволяє відсікання безвідповідних запитів за порогом; recall@5 у всіх конфігурацій майже однаковий (≈0,84, ДІ перекриваються), MRR найвищий у BM25 ({ev['BM25']['mrr']}). Вартість: {ev['Hybrid + rerank']['lat_ms']} мс проти {ev['BM25']['lat_ms']} мс (BM25) — для невеликого корпусу це несуттєво; зі справжнім cross-encoder на топ-30 очікується на 1–2 порядки більше (десятки–сотні мс на CPU), а також витрати на обчислення; API-вартості немає (усе локально). Висновки статистично обережні: різниці між конфігураціями менші за довірчі інтервали.
""")
# ---- журнал LLM і таблиця тверджень
log = [
 dict(id="L01", date="2026-11-11", model="Claude Sonnet 5.5", params=dict(temperature="за замовчуванням (у чаті не задається)", seed="н/д"), prompt_version="corpus-v1",
      prompt="Згенеруй 21 внутрішній HR-документ (положення, регламенти, методики, звіти, кейс, FAQ) українською, по 5 розділів × 2 абзаци, для корпусу Domain Knowledge Hub.", raw_output="kb_src/part1.txt; kb_src/part2.txt (початковий вихід)",
      human_decision="pending: студент переглядає всі 210 фрагментів; після автоперевірки виправлено D08-p09 (ст. 65 КЗпП) і D16-p10 (ст. 184 КЗпП), див. claims C09–C12"),
 dict(id="L02", date="2026-11-11", model="Claude Sonnet 5.5", params=dict(temperature="за замовчуванням", seed="н/д"), prompt_version="gold-v1",
      prompt="Складіть 42 запити (ключові слова, перефразування, багатокрокові, 5 без відповіді) і розмітьте релевантні фрагменти.", raw_output="eval/gold.jsonl (початковий вихід)",
      human_decision="pending: перегляд і виправлення запитів вручну; наявність кожного relevant id у корпусі перевірено скриптом (V4)"),
 dict(id="L03", date="2026-11-11", model="Claude Sonnet 5.5", params=dict(temperature="за замовчуванням", seed="42 (у коді)"), prompt_version="code-v1",
      prompt="Реалізуй chunking, HNSW-індекс, BM25+dense+RRF, reranker, pre-filter, метрики.", raw_output="src/*.py, eval/*.py", human_decision="pending: студент має вміти пояснити й змінити код на захисті"),
]
with open("llm_log/2026-11-11_claude.jsonl", "w", encoding="utf-8") as f:
    for r in log: f.write(json.dumps(r, ensure_ascii=False) + "\n")
claims = [
 ("C01", f"Корпус містить {cs['n_docs']} документ(ів) і {cs['n_frags']} фрагментів", "факт", "data/corpus.jsonl", "V4", "verified", "перераховано build_corpus.py"),
 ("C02", "Плинність 2025 = 87/520 = 16,7%", "факт", "D09-p01", "V4", "verified", f"87/520={87/520:.4f}"),
 ("C03", "Тестуванням охоплено 438 із 520 працівників (≈84%)", "факт", "D18-p01", "V4", "verified", f"438/520={438/520:.4f}"),
 ("C04", "Коефіцієнт плинності = звільнені / середньооблікова чисельність × 100%", "правило", "D04-p01, D04-p03", "V2", "verified", "узгоджується з визначенням у D04-p01"),
 ("C05", "Основна щорічна відпустка — 24 календарні дні", "факт", "D12-p01", "V1", "pending", "звірити з Законом «Про відпустки» (чинна редакція)"),
 ("C06", "Перші п'ять днів лікарняного оплачує роботодавець", "факт", "D12-p08", "V1", "pending", "звірити з чинним законодавством про страхування"),
 ("C07", "Особові справи зберігаються 75 років", "факт", "D11-p08", "V1", "pending", "звірити з переліком строків зберігання документів"),
 ("C08", "Про витік даних Уповноваженого повідомляють упродовж 72 годин", "правило", "D11-p09", "V1", "pending", "джерела не знайдено; для вигаданої компанії це внутрішнє правило — уточнити або прибрати посилання на закон"),
 ("C09", "ЧЕРНЕТКА: понаднормові — не більше 4 год на день", "факт", "D08-p09 (чернетка)", "V1", "rejected", "суперечить ст. 65 КЗпП (4 год упродовж двох днів поспіль); виправлено"),
 ("C10", "Понаднормові — до 4 год упродовж двох днів поспіль і 120 год на рік", "факт", "D08-p09", "V2", "pending", "виправлена редакція за ст. 65 КЗпП; підтвердити за текстом закону"),
 ("C11", "ЧЕРНЕТКА: заборона звільнення одиноких матерів з дитиною до 3 років", "факт", "D16-p10 (чернетка)", "V1", "rejected", "ст. 184 КЗпП: одинокі матері — з дитиною до 14 років; виправлено"),
 ("C12", "Не звільняють вагітних, жінок з дітьми до 3 років, одиноких матерів з дитиною до 14 років", "факт", "D16-p10", "V2", "pending", "виправлена редакція за ст. 184 КЗпП; підтвердити за текстом закону"),
 ("C13", f"BM25 recall@5 = {ev['BM25']['recall5']} на 37 запитах", "факт", "eval/run_eval.py", "V4", "verified", "відтворюється командою з README (seed=42)"),
 ("C14", f"Hybrid+rerank nDCG@10 = {ev['Hybrid + rerank']['ndcg10']}", "факт", "eval/run_eval.py", "V4", "verified", "відтворюється командою з README"),
 ("C15", "Метод 360 градусів не має бути єдиною підставою для звільнення", "правило", "D10-p02", "V1", "pending", "внутрішня політика; погодити з HR-директором"),
]
with open("claims/claims.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "твердження", "тип", "джерело", "рівень_верифікації", "статус", "коментар"]); w.writerows(claims)
st = collections.Counter(c[5] for c in claims); json.dump(dict(total=len(claims), **st), open(R + "claims_stats.json", "w"))
open("README.md", "w", encoding="utf-8").write("""# ЛР 10 — Векторне сховище та семантичний пошук (Domain Knowledge Hub, HR)
Python 3.12; numpy, scipy, scikit-learn, faiss-cpu, rank_bm25, matplotlib (pip install -r requirements.txt). seed = 42 (src/common.py).
```
python src/build_corpus.py     # Результат 1: kb/*.md -> очищення -> data/corpus.jsonl
python src/run_chunking.py     # Результат 2: results/chunking.json
python src/run_index.py        # Результат 3: results/index.json (HNSW, embeddings, upsert/delete)
python src/run_hybrid_demo.py  # Результат 4: pre-filter -> results/prefilter.json
python eval/run_eval.py        # Результат 4–5: results/eval.json
python eval/kappa.py           # κ (розмітник B = автоматичне правило; --human для людської розмітки)
python src/make_figs.py && python src/make_support.py
```
Для e5/cross-encoder (потрібен доступ до HuggingFace): `pip install sentence-transformers`, у src/index.py використайте `STEmbedder('intfloat/multilingual-e5-base')`, у src/hybrid.py замініть `rerank()` на `CrossEncoder(...).predict`. Ключі API не використовуються.
""")
open("requirements.txt", "w").write("numpy\nscipy\nscikit-learn\nfaiss-cpu\nrank_bm25\nmatplotlib\n")
print("claims", dict(st), len(claims))
