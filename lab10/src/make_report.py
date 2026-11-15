import json, csv
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
R = "results/"; J = lambda n: json.load(open(R + n, encoding="utf-8"))
cs, chk, ixr, pre, kp, cl = J("corpus_stats.json"), J("chunking.json"), J("index.json"), J("prefilter.json"), J("kappa.json"), J("claims_stats.json")
EV = J("eval.json"); ev, pq = EV["summary"], EV["per_q"]
G = {json.loads(l)["qid"]: json.loads(l) for l in open("eval/gold.jsonl", encoding="utf-8")}
claims = list(csv.reader(open("claims/claims.csv", encoding="utf-8")))[1:]
changed = sum(1 for q, d in pq.items() if d["Hybrid (RRF k=60)"]["top"] != d["Hybrid + rerank"]["top"]); n_ans = len(pq)
reord = sum(1 for q, d in pq.items() if d["Hybrid (RRF k=60)"]["top"] != d["Hybrid + rerank"]["top"] and set(d["Hybrid (RRF k=60)"]["top"]) == set(d["Hybrid + rerank"]["top"]))
doc = Document(); FN = "Times New Roman"
sec = doc.sections[0]; sec.page_height, sec.page_width = Cm(29.7), Cm(21); sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3), Cm(1.5), Cm(2), Cm(2)
st = doc.styles["Normal"]; st.font.name = FN; st.font.size = Pt(14); st.element.rPr.rFonts.set(qn("w:eastAsia"), FN)
def fmt(p, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, ls=1.5, before=0, after=0, keep=False):
    pf = p.paragraph_format; p.alignment = align; pf.line_spacing = ls; pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.first_line_indent = Cm(1.25) if indent else None; pf.keep_with_next = keep
def run(p, t, b=False, i=False, size=None, font=None):
    r = p.add_run(t); r.bold, r.italic = b, i; r.font.name = font or FN
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font or FN)
    if size: r.font.size = Pt(size)
    return r
def P(t="", b=False, i=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, **kw):
    p = doc.add_paragraph(); fmt(p, align, indent, **kw); run(p, t, b, i); return p
def H(t): return P(t, b=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, before=10, keep=True)
def H2(t): return P(t, b=True, i=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, before=4, keep=True)
def BUL(items):
    for t in items:
        p = doc.add_paragraph(); fmt(p, indent=False); p.paragraph_format.left_indent = Cm(1.25); p.paragraph_format.first_line_indent = Cm(-0.6); run(p, "• " + t)
def CODE(text):
    for ln in text.strip("\n").split("\n"):
        p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.LEFT, False, ls=1.0); p.paragraph_format.left_indent = Cm(0.6); run(p, ln, size=9.5, font="Courier New")
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "F2F2F2"); p._p.get_or_add_pPr().append(sh)
    P("", ls=0.6, indent=False)
tn = [0]; fn_ = [0]
def TCAP(t): tn[0] += 1; return P(f"Таблиця {tn[0]} - {t}", i=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, ls=1.0, before=6, after=3, keep=True)
def FIG(path, cap, w=16):
    p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.CENTER, False, ls=1.0, before=6); p.add_run().add_picture(path, width=Cm(w))
    fn_[0] += 1; P(f"Рисунок {fn_[0]} - {cap}", i=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, ls=1.0, before=3, after=8)
def borders(tbl):
    tblPr = tbl._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:color"), "000000"); b.append(x)
    tblPr.append(b)
def TBL(headers, rows, widths, size=11):
    t = doc.add_table(rows=1, cols=len(headers)); borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    def cell(c, txt, b=False, w=None):
        c.width = Cm(w); p = c.paragraphs[0]; fmt(p, WD_ALIGN_PARAGRAPH.LEFT, False, ls=1.0); run(p, str(txt), b=b, size=size)
    for j, h in enumerate(headers): cell(t.rows[0].cells[j], h.upper() if size >= 11 and len(h) < 18 else h, True, widths[j])
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for r in rows:
        cells = t.add_row().cells
        for j, v in enumerate(r): cell(cells[j], v, False, widths[j])
    for j, w in enumerate(widths): t.columns[j].width = Cm(w)
    P("", ls=0.6, indent=False)
def CRIT(rows):
    P("Самоперевірка за критеріями результату", i=True, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, ls=1.0, before=6, after=3, keep=True)
    TBL(["№", "Критерій перевірки", "✓", "Підтвердження"], rows, [1.1, 6.0, 0.9, 9.5], 10.5)
def PB(): doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
# ---------------- Титульна сторінка (як у ЛР 1)
C = WD_ALIGN_PARAGRAPH.CENTER
for t in ["Міністерство освіти і науки України", "Львівський національний університет імені Івана Франка", "Факультет електроніки та комп'ютерних технологій", "Кафедра системного проєктування"]: P(t, align=C, indent=False, ls=1.15)
for _ in range(5): P("", indent=False, ls=1.15)
P("Звіт", b=True, align=C, indent=False, ls=1.15); P("Про виконання лабораторної роботи №10", align=C, indent=False, ls=1.15); P("З курсу «Сховища знань та управління знаннями»", align=C, indent=False, ls=1.15); P("«Векторне сховище та семантичний пошук»", b=True, align=C, indent=False, ls=1.15)
for _ in range(5): P("", indent=False, ls=1.15)
for t in ["Виконав:", "Студент групи ФЕІ-42", "Дячук Роман", "Перевірив:", "Патинко A. M."]: P(t, align=WD_ALIGN_PARAGRAPH.RIGHT, indent=False, ls=1.15)
for _ in range(5): P("", indent=False, ls=1.15)
P("Львів - 2026", align=C, indent=False, ls=1.15); PB()
# ---------------- Вступ
P("Тема: Векторне сховище та семантичний пошук у тематичній області “Людина. Управління персоналом. Формалізувати знання про співробітників і їх компетенції. Використання баз знань для HR-рішень.”", b=False)
P("Мета: Навчитися будувати векторний індекс, порівнювати стратегії chunking та моделі embeddings, реалізовувати гібридний пошук із злиттям RRF і reranking та оцінювати конфігурації метриками recall@k, MRR і nDCG на власному золотому наборі.")
H("Мета роботи")
P("Навчитися перетворювати текстові знання у сфері управління персоналом на векторне сховище, придатне для семантичного пошуку: підготувати корпус документів із метаданими, порівняти стратегії розбиття тексту на фрагменти та моделі векторних представлень, поєднати лексичний (BM25) і щільний (dense) пошук, застосувати reranking і фільтрацію за метаданими та оцінити якість кожної конфігурації на власному золотому наборі запитів.")
H("Індустріальний контекст і роль LLM-експерта")
P("У проєкті Domain Knowledge Hub накопичені знання про співробітників і їх компетенції розпорошені по десятках документів: положення про оцінювання, політики кадрового резерву, методики розрахунку плинності, регламенти співбесід, звіти. Керівнику або HR-спеціалісту потрібно швидко відповісти на питання на кшталт «що буде, якщо працівник три квартали має низькі результати?» або «які дані кандидата зберігаються після співбесіди?». Пошук за ключовими словами втрачає відповіді при перефразуванні, а чисто семантичний пошук може пропускати точні терміни та числа; крім того, частина документів містить конфіденційні кадрові дані, тому пошук має враховувати рівень чутливості фрагментів.")
P("Генеративну модель використано як експерта: Claude Sonnet 5.5 запропонував чернетки документів корпусу, кандидатів запитів до фрагментів (синтетичні питання) і код; їх перевірено автоматично та вручну і лише після цього формалізовано. Використані рівні верифікації V3 (людина) та V4 (метрики), метрики: recall@5, MRR, nDCG@10. На рисунку 1 наведено загальну схему розробленого конвеєра від сирих документів до ранжованої видачі.")
FIG("figs/fig1_pipeline.png", "Схема конвеєра семантичного пошуку Domain Knowledge Hub")
P("Код і дані розміщено в репозиторії Hub (гілка lab10): src/ — модулі chunking.py, index.py, hybrid.py; eval/ — золотий набір і оцінювання; data/ — корпус; docs/ — звіти за результатами; llm_log/ і claims/ — артефакти протоколу «LLM-експерт». Запуск з нуля описано в README (залежності, команди, seed = 42). Ключі API у коді не зберігаються, персональні дані у зовнішні сервіси не передавалися.")
# ================= РЕЗУЛЬТАТ 1
H("Результат 1. Корпус і метадані")
P(f"Артефакти: data/corpus.jsonl; docs/corpus_card.md. Крок 1. Зібрано корпус із {cs['n_docs']} документів предметної області «Управління персоналом» (8 методик і настанов, 5 положень і політик, 4 регламенти, 2 звіти, 1 кейс і 1 FAQ). Документи синтетичні: їх підготовлено за допомогою LLM для навчального використання, реальних персональних даних вони не містять. У «сирому» вигляді (kb/*.md) кожен документ містить типовий вебшум — «хлібні крихти», номери сторінок, кнопки навігації, cookie-банер і колонтитули. Правила очищення наведено в таблиці 1; всього видалено {cs['removed_total']} із {cs['raw_lines']} рядків.")
TCAP("Правила очищення від шуму (src/build_corpus.py)")
rl = [("R1", "Навігаційні «хлібні крихти»", r"^Головна\s*>", cs["removed"]["R1_breadcrumb"]), ("R2", "Номери сторінок", r"^Сторінка \d+ з \d+$", cs["removed"]["R2_page_number"]), ("R3", "Колонтитул з правами", r"^©", cs["removed"]["R3_copyright"]), ("R4", "Кнопки «Наверх», «Поділитися», «Друкувати»", r"^(Наверх|Поділитися|Друкувати)", cs["removed"]["R4_nav_buttons"]), ("R5", "Cookie-банер", r"^Цей сайт використовує cookie", cs["removed"]["R5_cookie_banner"]), ("R6", "Нормалізація пробілів", r"\s+ → один пробіл", "—")]
TBL(["Правило", "Що видаляється", "Шаблон", "Рядків"], rl, [1.6, 6.2, 6.3, 1.9], 10.5)
P("Крок 2. Документи розбито на фрагменти за абзацами (10 абзаців на документ, 5 розділів по 2 абзаци), що дало 210 фрагментів, у середньому 19 слів кожен. Для кожного фрагмента збережено метадані (таблиця 2).")
TCAP("Метадані фрагмента (приклад — D11-p07)")
TBL(["Поле", "Значення"], [("id", "D11-p07"), ("doc_id", "D11"), ("title", "Політика захисту персональних даних працівників"), ("section", "Зберігання і передача"), ("type", "policy (guide / policy / regulation / report / case / faq)"), ("date", "2025-05-30"), ("sensitivity", "restricted (public / internal / confidential / restricted)"), ("source_url", "internal://hub/kb/D11"), ("text", "Персональні дані не можна передавати у зовнішні сервіси штучного інтелекту без знеособлення…")], [3.5, 12.5], 10.5)
CODE("""RULES = {"R1_breadcrumb": re.compile(r"^Головна\\s*>"), "R2_page_number": re.compile(r"^Сторінка \\d+ з \\d+$"),
         "R3_copyright": re.compile(r"^©"), "R4_nav_buttons": re.compile(r"^(Наверх|Поділитися|Друкувати)"),
         "R5_cookie_banner": re.compile(r"^Цей сайт використовує cookie")}
def clean_lines(lines):
    keep = []
    for ln in lines:
        s = ln.strip(); hit = next((k for k, r in RULES.items() if r.match(s)), None)
        if hit: removed[hit] += 1; continue
        keep.append(re.sub(r"\\s+", " ", s))
    return keep""")
P("Крок 3. Складено картку корпусу (docs/corpus_card.md): джерела (синтетичні внутрішні HR-документи вигаданої ІТ-компанії, згенеровані LLM 11.11.2026), ліцензія (CC BY 4.0 для навчального використання), мова (українська), правила очищення та відомі прогалини (немає документів про охорону праці, податки, релокацію, корпоративний транспорт — ці теми використано для запитів без відповіді). Крок 4. Кожному фрагменту присвоєно рівень sensitivity: рівень документа успадковується фрагментами, а абзац кейсу з персональними деталями (D14-p03) позначено restricted вручну. Розподіл наведено в таблиці 3; фрагментів з обмеженим доступом (confidential або restricted) — " + str(cs["by_sens"]["confidential"] + cs["by_sens"]["restricted"]) + ".")
TCAP("Розподіл фрагментів за чутливістю та типом документа")
TBL(["Sensitivity", "Фрагментів", "Тип документа", "Фрагментів"], [(k, cs["by_sens"][k], t, cs["by_type"][t]) for k, t in zip(["public", "internal", "confidential", "restricted", "—", "—"], ["guide", "policy", "regulation", "report", "case", "faq"]) if k in cs["by_sens"] or True][:6] if False else [("public", cs["by_sens"]["public"], "guide", cs["by_type"]["guide"]), ("internal", cs["by_sens"]["internal"], "policy", cs["by_type"]["policy"]), ("confidential", cs["by_sens"]["confidential"], "regulation", cs["by_type"]["regulation"]), ("restricted", cs["by_sens"]["restricted"], "report", cs["by_type"]["report"]), ("", "", "case", cs["by_type"]["case"]), ("", "", "faq", cs["by_type"]["faq"])], [3.5, 3, 5, 3], 10.5)
P("Висновок за результатом 1. Побудовано очищений корпус із 21 документа та 210 фрагментів, кожен із повними метаданими та рівнем чутливості; правила очищення задокументовано й відтворювані скриптом, картка корпусу містить джерела й ліцензії.")
CRIT([("C1", "≥ 20 документів, ≥ 200 фрагментів із метаданими", "✓", f"{cs['n_docs']} документів, {cs['n_frags']} фрагментів, 7 полів метаданих"), ("C2", "Є очищення від шуму (описано правила)", "✓", "6 правил, таблиця 1; видалено " + str(cs["removed_total"]) + " рядків"), ("C3", "Картка корпусу має джерела й ліцензії", "✓", "docs/corpus_card.md"), ("C4", "Позначено sensitivity для кожного фрагмента", "✓", "4 рівні, таблиця 3; поле заповнене для 210 з 210")])
# ================= РЕЗУЛЬТАТ 2
H("Результат 2. Стратегії chunking")
P("Артефакти: src/chunking.py; docs/chunking_cmp.md. Крок 1. Реалізовано чотири стратегії: (S1) фіксоване вікно 60 слів із перекриттям 15 слів, яке перетинає межі розділів; (S2) розбиття за заголовками — один chunk дорівнює розділу документа; (S3) ієрархічна parent–child — індексуються дочірні абзаци, а в LLM передається батьківський розділ; (S4) семантична — сусідні абзаци об'єднуються, якщо косинусна схожість їх символьних TF-IDF-векторів перевищує 0,12 (не більше 80 слів).")
CODE("""def hierarchical(frags):
    sec = {}
    for f in frags: sec.setdefault((f["doc_id"], f["section_idx"]), []).append(f)
    out = []
    for f in frags:
        parent = sec[(f["doc_id"], f["section_idx"])]
        ctx = f"{f['section']}. " + " ".join(p["text"] for p in parent)
        out.append(dict(cid=f["id"], text=f["text"], covers={p["id"] for p in parent}, ctx_text=ctx))
    return out""")
P("Крок 2. Для кожної стратегії побудовано HNSW-індекс (M = 32, efSearch = 64) з однаковою моделлю embeddings (LSA-char, 128 вимірів). Крок 3. Стратегії порівняно на 10 тестових запитах (4 ключових слова, 3 перефразування, 3 багатокрокових): метрика recall@5 визначалася за фрагментами, що потрапили в контекст топ-5 chunk-ів (після об'єднання chunk-ів з однаковим покриттям), а розмір контексту — як середня довжина chunk-ів, які отримує LLM. Для перевірки стійкості висновку таблицю доповнено recall@5 і nDCG@10 на всіх 37 запитах із відповіддю (таблиця 4, рисунок 2).")
TCAP("Порівняння стратегій chunking (модель LSA-char, HNSW M = 32)")
LB = {"fixed_60_15": "S1 фіксоване 60/15", "by_heading": "S2 за заголовками", "hierarchical": "S3 ієрархічна", "semantic": "S4 семантична"}
TBL(["Стратегія", "Chunk-ів", "Сер. chunk, слів", "recall@5 (10)", "MRR (10)", "Контекст, слів", "recall@5 (37)", "nDCG@10 (37)"], [(LB[k], v["n_chunks"], v["avg_chunk_words"], v["recall5"], v["mrr"], v["ctx_words"], v["recall5_all37"], v["ndcg10_all37"]) for k, v in chk.items()], [3.6, 1.5, 1.8, 1.8, 1.5, 1.8, 1.9, 1.9], 9.5)
FIG("figs/fig2_chunking.png", "Повнота та розмір контексту для різних стратегій chunking")
P(f"Крок 4. Вибір: ієрархічна стратегія S3. На 10 тестових запитах вона має recall@5 = {chk['hierarchical']['recall5']:.2f} (так само, як S2), на всіх 37 запитах — {chk['hierarchical']['recall5_all37']:.3f} проти {chk['by_heading']['recall5_all37']:.3f} у S2 (різниця 0,004, тобто менше ніж 0,2 запиту), а розмір контексту практично той самий ({chk['hierarchical']['ctx_words']:.1f} проти {chk['by_heading']['ctx_words']:.1f} слів). Стратегія S2 має вищий MRR ({chk['by_heading']['mrr']:.2f} проти {chk['hierarchical']['mrr']:.2f}) та nDCG@10, але ця перевага становить 1–2 запити й лежить у межах шуму малого набору. Вирішальними стали властивості, потрібні решті роботи: індексація на рівні фрагмента дає точні метадані sensitivity і дати для фільтрації (в S2 розділ із одним restricted-абзацом довелося б повністю закрити), розмітка золотого набору виконується на рівні фрагмента, а LLM отримує повний батьківський розділ. Стратегія S1 різала думки на межі розділів і давала найбільший контекст ({chk['fixed_60_15']['ctx_words']:.0f} слів), S4 мала найнижчий recall.")
P("Висновок за результатом 2. Реалізовано чотири стратегії chunking, для кожної збудовано індекс із фіксованою моделлю, порівняно recall@5 і розмір контексту та обґрунтовано вибір ієрархічної стратегії даними таблиці 4.")
CRIT([("C1", "≥ 3 стратегії реалізовано", "✓", "4 стратегії: fixed, by_heading, hierarchical, semantic"), ("C2", "Індекси збудовано для кожної (фіксована модель)", "✓", "LSA-char, 128d, HNSW M = 32 для всіх чотирьох"), ("C3", "Є порівняльна таблиця recall@5 і розміру контексту", "✓", "таблиця 4"), ("C4", "Вибір обґрунтовано даними", "✓", "порівняння recall@5, контексту й властивостей фрагментного рівня")])
# ================= РЕЗУЛЬТАТ 3
H("Результат 3. Векторний індекс і порівняння embeddings")
m = ixr["models"]
P(f"Артефакти: src/index.py; docs/embeddings_cmp.md. Крок 1. Побудовано індекси FAISS HNSW (IndexHNSWFlat, метрика inner product на нормованих векторах, що еквівалентно косинусній схожості) для двох моделей embeddings. У середовищі виконання роботи немає доступу до репозиторію HuggingFace, тому замість multilingual-e5 порівняно дві щільні моделі на основі латентно-семантичного аналізу (TF-IDF + усічений SVD до 128 вимірів): LSA-word (основи слів і біграми) та LSA-char (символьні n-грами довжиною 3–5). У модулі index.py реалізовано адаптер STEmbedder для sentence-transformers (в т.ч. multilingual-e5 з префіксами query/passage), який має той самий інтерфейс і підключається без змін решти коду; у цьому середовищі його не запускали.")
P(f"Крок 2. Зафіксовано параметри: M = 32, efConstruction = 80, efSearch = 64, 128 вимірів, {m['lsa-word']['n']} векторів (пам'ять {m['lsa-word']['mem_kb']} КБ). Крок 3. Якість і затримку виміряно на 20 запитах золотого набору (таблиця 5); затримку подано як медіану з 5 повторів на запит.")
TCAP("Порівняння моделей embeddings на 20 запитах (HNSW, M = 32, efSearch = 64)")
TBL(["Модель", "Час побудови, с", "Затримка, сер., мс", "Затримка, p95, мс", "recall@5", "MRR"], [(k, v["build_s"], v["lat_mean_ms"], v["lat_p95_ms"], v["recall5"], v["mrr"]) for k, v in m.items()], [3.2, 3, 3, 3, 2, 2], 10.5)
sw = ixr["hnsw_sweep"]
P(f"Модель LSA-word точніша ({m['lsa-word']['recall5']} проти {m['lsa-char']['recall5']}) і швидша (≈{m['lsa-word']['lat_mean_ms']:.1f} проти ≈{m['lsa-char']['lat_mean_ms']:.1f} мс), бо префіксний стемер нормалізує закінчення української мови, а розріджений простір символьних n-грам вимагає більше ресурсів. Зміна параметрів HNSW на цьому обсязі даних (210 векторів) не вплинула на якість: для M ∈ {{16, 32}} і efSearch ∈ {{16, 64, 128}} recall@5 лишався {sw[0]['recall5']}, а затримка — близько {sw[3]['lat_mean_ms']:.1f} мс; граф такого розміру практично повністю обходиться навіть при малих efSearch. Щодо мови: для україномовних запитів морфологічна нормалізація важлива, тоді як для трьох англомовних запитів («turnover rate formula» тощо) обидві моделі дали recall@5 = {ixr['english']['lsa-word']['recall5']}, бо LSA не містить міжмовних знань; для двомовного корпусу потрібна багатомовна модель на кшталт multilingual-e5.")
P("Крок 4. Процедура оновлення індексу. HNSW у FAISS не підтримує фізичне видалення, тому реалізовано схему tombstone: upsert додає новий вектор, а старий вектор того ж cid позначається «мертвим» і відфільтровується під час пошуку (з over-fetch у шість разів); delete позначає вектор «мертвим»; compact перебудовує граф без «мертвих» вузлів. Словник моделі фіксований — при суттєвому дрейфі лексики модель треба перенавчати (refit). Процедуру перевірено на п'яти документах (таблиця 6): для кожного перезаписано один фрагмент новою редакцією, перевірено, що нова версія є першою у видачі, а стара зникла, після чого всі фрагменти цих документів видалено, виконано compact і перевірено відсутність «витоків» у топ-10 для запитів, що раніше вказували на ці документи.")
CODE("""def upsert(self, chunk):
    for i, c in enumerate(self.chunks):
        if c["cid"] == chunk["cid"] and i not in self.dead: self.dead.add(i)     # tombstone старої версії
    v = self.emb.encode([chunk["text"]]); self.ix.add(v); self.V = np.vstack([self.V, v]); self.chunks.append(chunk)
def delete(self, cid): ...   # self.dead.add(i) для всіх живих векторів із цим cid
def compact(self):           # фізичне видалення: перебудова HNSW без tombstones
    keep = [i for i in range(len(self.chunks)) if i not in self.dead]
    self.chunks = [self.chunks[i] for i in keep]; self.V = self.V[keep]
    self.ix = self._new_index(self.V.shape[1]); self.ix.add(self.V); self.dead = set()""")
TCAP("Перевірка upsert/delete на п'яти документах")
TBL(["Документ", "Upsert, мс", "Нова версія — 1-ша", "Стара версія зникла", "Видалено фрагм.", "Витік у топ-10"], [(u["doc"], u["upsert_ms"], "так" if u["new_top1"] else "ні", "так" if u["old_version_absent"] else "ні", d["deleted"], d["leaked_in_top10"]) for u, d in zip(ixr["update"]["upsert"], ixr["update"]["delete"])], [2.4, 2.2, 3.4, 3.2, 2.6, 2.4], 10.5)
u = ixr["update"]
P(f"Після видалення активних фрагментів стало {u['live_after_delete']} (було {u['live_before_delete']}); розмір індексу до/після compact — {u['index_size_before_compact']} → {u['index_size_after_compact']} векторів, compact виконується за ≈{u['compact_ms']:.0f} мс.")
P("Висновок за результатом 3. Побудовано HNSW-індекси для двох моделей, зафіксовано параметри та час, порівняно якість і затримку на 20 запитах; обрано LSA-word як dense-складову подальшого гібридного пошуку. Процедуру upsert/delete з tombstone та compact перевірено на п'яти документах. Порівняння з багатомовними трансформерними моделями лишається завданням для середовища з доступом до HuggingFace.")
CRIT([("C1", "Побудовано індекси для 2 моделей", "✓", "LSA-word і LSA-char (відхилення від e5 описано вище)"), ("C2", "Параметри та час зафіксовано", "✓", "M = 32, efC = 80, efS = 64; час побудови в таблиці 5"), ("C3", "Є таблиця якості й затримки для 20 запитів", "✓", "таблиця 5"), ("C4", "Upsert/delete перевірено на 5 документах", "✓", "таблиця 6: D03, D07, D12, D15, D20")])
# ================= РЕЗУЛЬТАТ 4
H("Результат 4. Гібридний пошук і reranking")
P("Артефакти: src/hybrid.py; docs/hybrid_report.md. Крок 1. Реалізовано лексичний пошук BM25 (бібліотека rank_bm25, k1 = 1,5, b = 0,75, токенізація з префіксним стемером довжиною 6 символів і списком стоп-слів), dense-пошук по HNSW-індексу (LSA-word) та злиття списків методом Reciprocal Rank Fusion: RRF(d) = Σ 1 / (k + rank_i(d)), k = 60, по топ-30 кожного списку.")
CODE("""def rrf(self, lists, k=60):
    sc = {}
    for lst in lists:
        for r, (i, _) in enumerate(lst, 1): sc[i] = sc.get(i, 0) + 1 / (k + r)
    return sorted(sc.items(), key=lambda x: -x[1])
def hybrid_rank(self, q, k=30, allowed=None):
    return self.rrf([self.bm25_rank(q, 30, allowed), self.dense_rank(q, 30, allowed)])[:k]""")
P("Крок 2. Додано reranker, який переупорядковує топ-30 кандидатів RRF і повертає топ-5 (для метрик — топ-10). Через відсутність доступу до моделей HuggingFace cross-encoder замінено легким reranker-ом на основі ознак пари «запит — фрагмент»: оцінка = 0,4 · косинус символьних TF-IDF-векторів + 0,4 · частка основ слів запиту, що є у фрагменті, + 0,2 · частка збігів біграм основ. Ваги задано апріорі й не підбирались на золотому наборі. Інтерфейс rerank(query, candidates) дозволяє замінити його на CrossEncoder без змін решти коду.")
P(f"Reranker змінює видачу: порядок топ-5 відрізняється від результату RRF для {changed} із {n_ans} запитів із відповіддю (з них для {reord} змінився лише порядок тих самих фрагментів, а для решти — склад топ-5). Наприклад, для запиту q25 («Чому люди звільнялися найчастіше за результатами вихідних бесід?») правильний фрагмент D09-p05 піднімається з другого місця на перше.")
P("Крок 3. Реалізовано pre-filter за метаданими (тип документа, максимальний рівень sensitivity, діапазон дат). Фільтр застосовується до кандидатів до ранжування в обох гілках: для BM25 — виключення з видачі, для dense — точний пошук по підмножині (якщо вона менша за половину індексу) або over-fetch із відсіканням. Перевірено чотири сценарії (таблиця 7); у кожному без фільтра видача порушувала обмеження, а з фільтром — ні.")
TCAP("Перевірка pre-filter за метаданими")
TBL(["Сценарій", "Запит", "Дозволено фрагм.", "Порушення без фільтра", "Фільтр дотримано"], [(k, v["query"], v["allowed_n"], "так" if v["violations_before"] else "ні", "так" if v["filter_respected"] else "ні") for k, v in pre.items()], [3.2, 6.3, 2.0, 2.4, 2.1], 10)
P("Крок 4. Приклади для порівняння BM25, dense, гібриду та гібриду з reranker-ом наведено в таблиці 8 (у клітинках — два перших id у видачі; правильний фрагмент виділено в стовпчику «Релевантні»).")
def exr(q): d = pq[q]; return [q, G[q]["query"], ", ".join(G[q]["relevant"])] + [", ".join(d[k]["top"][:2]) for k in ["BM25", "Dense (LSA-word)", "Hybrid (RRF k=60)", "Hybrid + rerank"]]
fx = ev["_examples"]; TCAP("Приклади виграшу (q24, q14, q01) та програшу (q16) гібридного пошуку")
TBL(["qid", "Запит", "Релевантні", "BM25", "Dense", "Hybrid", "+ rerank"], [exr(q) for q in fx["win"] + fx["lose"]], [1.0, 4.6, 1.9, 2.4, 2.4, 2.4, 2.4], 9)
P("Виграш. У трьох прикладах (q24, q14, q01) гібрид ставить правильний фрагмент на перше місце там, де dense-пошук лишає його на другому–третьому. Запит q24 («У яких випадках роботодавцю заборонено звільняти працівника?»): BM25 точно впізнає слова «заборонено звільняти», тоді як dense на перше місце ставить схожий за темою абзац про компенсацію при звільненні (D12-p09). Запит q14 («оперативний і перспективний кадровий резерв»): dense ставить загальний вступний абзац про резерв, а BM25 — абзац із цими двома термінами. Запит q01 («коефіцієнт плинності формула»): dense віддає перевагу звіту D09-p01 зі згадкою коефіцієнта та числами, а слово «формула» збігається лише з D04-p03. RRF зберігає лексичну точність BM25 і семантичну гнучкість dense-пошуку.")
P("Програш. Запит q16 («прохідний бал тестування компетенцій 65»): число «65» збігається лише лексично, тому BM25 ставить D18-p02 на перше місце, а dense упевнено ставить на перше місце сусідній абзац того ж звіту (D18-p07), який збігається за темою. RRF використовує лише ранги й не бачить упевненості методів, тому гібрид опускає правильний фрагмент на друге місце; reranker не виправляє ситуацію (рядок «+ rerank»). Це типова слабкість злиття за рангами для запитів, де важливий точний числовий збіг.")
P("Висновок за результатом 4. Реалізовано BM25, dense-пошук і злиття RRF (k = 60), доданий reranker змінює порядок топ-5, pre-filter за типом, рівнем чутливості та датою перевірено на чотирьох сценаріях; показано три приклади виграшу гібриду та один програш із поясненням.")
CRIT([("C1", "BM25, dense і RRF працюють (код + запуск)", "✓", "src/hybrid.py; запуск eval/run_eval.py"), ("C2", "Reranker інтегровано; топ-5 змінюється зі зміною порядку", "✓", f"топ-5 змінилось у {changed} із {n_ans} запитів"), ("C3", "Pre-filter за метаданими перевірено", "✓", "таблиця 7, 4 сценарії"), ("C4", "Є 3 приклади «виграшу» та 1 «програшу» з поясненням", "✓", "таблиця 8: q24, q14, q01 / q16")])
# ================= РЕЗУЛЬТАТ 5
H("Результат 5. Золотий набір і оцінювання")
na = ev["_no_answer"]
P("Артефакти: eval/gold.jsonl; docs/search_eval.md. Крок 1. Створено золотий набір із 42 запитів: 16 запитів із ключовими словами, 12 перефразувань, 9 багатокрокових (відповідь розподілена між 2–3 фрагментами) та 5 запитів без відповіді у корпусі. Для кожного запиту розмічено релевантні фрагменти (на рівні id). Кандидати запитів запропонував LLM, їх переглянуто й виправлено, а наявність кожного id у корпусі перевірено скриптом.")
TCAP("Склад золотого набору")
TBL(["Тип запиту", "Кількість", "Приклад"], [("Ключові слова", 16, "правило 70-20-10"), ("Перефразування", 12, "Скільки місяців триває випробувальний період?"), ("Багатокрокові", 9, "Як відбувається звільнення за низьку продуктивність від оцінки до наказу?"), ("Без відповіді", 5, "Як працює програма релокації працівників до Німеччини?"), ("Разом", 42, "")], [3.5, 2.5, 10], 10.5)
P(f"Крок 2. Узгодженість розмітки перевірено на {kp['n_queries']} запитах (стратифікована вибірка: ключові слова, перефразування, багатокрокові) за пулом із {kp['n_pairs']} пар «запит — фрагмент» (топ-5 BM25, dense і гібриду плюс еталонні фрагменти). Розмітник A — автор набору; розмітник B незалежно оцінював пари за автоматичним правилом (у фрагменті є щонайменше половина основ слів запиту). Cohen's κ = {kp['kappa']} при спостережуваному збігу {kp['observed_agreement']}, що відповідає суттєвій узгодженості. Слід зазначити, що розмітником B у цій версії є алгоритм, а не друга людина; для людської розмітки передбачено файл eval/annotator_B.csv і запуск eval/kappa.py --human.")
P("Крок 3. Оцінено п'ять конфігурацій (BM25, dense LSA-word, dense LSA-char, hybrid RRF, hybrid + rerank) за метриками recall@5, recall@10, MRR і nDCG@10 на 37 запитах із відповіддю (таблиця 10, рисунок 3). Метрики обчислено на рівні фрагмента з бінарною релевантністю; recall@k — частка релевантних фрагментів у топ-k, MRR — обернений ранг першого релевантного, nDCG@10 нормовано на ідеальний порядок min(|rel|, 10) релевантних. Для recall@5 подано 95% довірчий інтервал (bootstrap, 1000 вибірок).")
cf = ["BM25", "Dense (LSA-word)", "Dense (LSA-char)", "Hybrid (RRF k=60)", "Hybrid + rerank"]
TCAP("Якість і затримка конфігурацій пошуку (37 запитів із відповіддю)")
TBL(["Конфігурація", "recall@5", "recall@10", "MRR", "nDCG@10", "Затримка, мс", "95% ДІ recall@5"], [(c, ev[c]["recall5"], ev[c]["recall10"], ev[c]["mrr"], ev[c]["ndcg10"], ev[c]["lat_ms"], f"{ev[c]['recall5_ci95'][0]}–{ev[c]['recall5_ci95'][1]}") for c in cf], [3.8, 1.8, 1.9, 1.5, 1.9, 2.1, 3.0], 10)
FIG("figs/fig3_eval.png", "Метрики конфігурацій пошуку на золотому наборі")
bt = {c: ev[c]["mrr_by_type"] for c in cf}
P(f"За типами запитів (MRR): для ключових слів найкращий BM25 ({bt['BM25']['keyword']:.2f}) і гібрид ({bt['Hybrid (RRF k=60)']['keyword']:.2f}), для перефразувань — гібрид із reranker-ом ({bt['Hybrid + rerank']['paraphrase']:.2f} проти {bt['BM25']['paraphrase']:.2f} у BM25), найважчими є багатокрокові запити (MRR 0,54–0,63 для всіх конфігурацій), де потрібно знайти кілька фрагментів одночасно. Запити без відповіді: середній бал топ-1 reranker-а для них становить {na['top1_noanswer_mean']} проти {na['top1_answerable_mean']} для запитів із відповіддю; поріг {na['threshold']} (половина медіани) відсікає {na['rejected_noans']} із {na['n_noans']} безвідповідних запитів і зберігає {na['kept_answerable']} із {na['n_ans']} відповідних.")
P(f"Крок 4. Висновок: для лабораторної роботи 11 обрано конфігурацію hybrid + rerank. Вона має найвищі recall@10 ({ev['Hybrid + rerank']['recall10']}) і nDCG@10 ({ev['Hybrid + rerank']['ndcg10']}), найкраще працює на перефразуваннях і дозволяє відсікати запити без відповіді за порогом оцінки, що важливо для RAG (менше галюцинацій). Водночас потрібно чесно зазначити: recall@5 у всіх конфігурацій майже однаковий (≈0,84) і довірчі інтервали перекриваються, а MRR найвищий у BM25 ({ev['BM25']['mrr']}); на невеликому корпусі із чіткою термінологією BM25 є сильним базовим рівнем, тож статистично значущої переваги однієї конфігурації не показано. Вартість і затримка: BM25 — {ev['BM25']['lat_ms']} мс, dense — {ev['Dense (LSA-word)']['lat_ms']} мс, гібрид — {ev['Hybrid (RRF k=60)']['lat_ms']} мс, гібрид із reranker-ом — {ev['Hybrid + rerank']['lat_ms']} мс на запит (CPU); для корпусу з 210 фрагментів це несуттєво, платних API не використовується. Зі справжнім cross-encoder на топ-30 очікується зростання затримки на 1–2 порядки (десятки–сотні мс на CPU) і потреба в обчислювальних ресурсах, тому в продуктивному середовищі reranking варто застосовувати лише до топ-20–30 і кешувати результати.")
P("Висновок за результатом 5. Створено золотий набір із 42 запитів (5 без відповіді), обчислено κ на 12 запитах, оцінено п'ять конфігурацій за recall@5/10, MRR і nDCG@10 та обрано hybrid + rerank для ЛР 11 з урахуванням якості, затримки та вартості.")
CRIT([("C1", "≥ 40 запитів, ≥ 5 без відповіді", "✓", "42 запити, 5 без відповіді"), ("C2", "κ обчислено на ≥ 10 запитах", "✓", f"κ = {kp['kappa']} на {kp['n_queries']} запитах (розмітник B — автоматичний)"), ("C3", "Метрики для ≥ 4 конфігурацій у таблиці", "✓", "таблиця 10, 5 конфігурацій"), ("C4", "Висновок враховує якість, затримку й вартість", "✓", "крок 4")])
# ================= LLM-експерт
H("Протокол «LLM-експерт»")
P("Декларація використання генеративного ШІ. Інструмент: Claude Sonnet 5.5 (Anthropic). Призначення: (1) чернетки 21 документа корпусу; (2) кандидати запитів і розмітки золотого набору; (3) допомога в написанні коду. Приклад запиту: «Згенеруй 21 внутрішній HR-документ (положення, регламенти, методики, звіти, кейс, FAQ) українською, по 5 розділів × 2 абзаци». Перевірка: узгодженість чисел і арифметики контролювалась скриптами (наприклад, 87/520 = 16,7 %), наявність id релевантних фрагментів — автоматично, правові норми — звіркою з законодавством. Повний журнал взаємодії міститься в llm_log/, таблиця тверджень — у claims/claims.csv.")
TCAP("Фрагмент журналу взаємодії з LLM (llm_log/2026-11-11_claude.jsonl)")
TBL(["ID", "Дата", "Модель / параметри", "Версія підказки", "Сирий вихід", "Рішення людини"], [("L01", "2026-11-11", "Claude Sonnet 5.5; temperature за замовчуванням; seed н/д", "corpus-v1", "kb_src/part1–2.txt", "перегляд; виправлено D08-p09 і D16-p10"), ("L02", "2026-11-11", "те саме", "gold-v1", "eval/gold.jsonl", "перегляд; id перевірено скриптом"), ("L03", "2026-11-11", "те саме; seed 42 у коді", "code-v1", "src/*.py, eval/*.py", "код перевірено запуском")], [1.0, 2.0, 4.2, 2.0, 3.0, 3.8], 9)
TCAP("Таблиця тверджень (claims/claims.csv)")
TBL(["ID", "Твердження", "Тип", "Джерело", "Рівень", "Статус", "Коментар"], [(c[0], c[1], c[2], c[3], c[4], c[5], c[6]) for c in claims], [1.0, 4.3, 1.5, 2.2, 1.1, 1.6, 4.3], 8)
P(f"Підсумок: усього {cl['total']} тверджень; підтверджено {cl['verified']} ({cl['verified']/cl['total']*100:.0f} %), відхилено {cl['rejected']} (C09 і C11: у чернетці LLM було неточне формулювання про понаднормові години та гарантії від звільнення, виправлено за нормами КЗпП), очікують верифікації {cl['pending']} (правові норми потребують звірки з чинною редакцією закону). Перелік джерел: внутрішні документи корпусу D01–D21, Кодекс законів про працю України, Закон України «Про відпустки», Закон України «Про захист персональних даних».")
H("Відхилення від методики та обмеження")
BUL(["Замість моделей sentence-transformers використано LSA (TF-IDF + SVD), бо середовище виконання не має доступу до HuggingFace; адаптер STEmbedder для multilingual-e5 підготовлено, але не запускався.", "Замість cross-encoder використано легкий reranker на лексичних ознаках пари запит—фрагмент; ваги задано апріорі.", "Розмітник B при обчисленні κ — автоматичне правило, а не друга людина.", "Корпус синтетичний і невеликий (≈4 тис. слів), тому метрики мають широкі довірчі інтервали, а різниці між конфігураціями не є статистично значущими."])
H("Висновок")
P("У результаті виконання лабораторної роботи побудовано векторне сховище знань для предметної області «Управління персоналом»: підготовлено очищений корпус із 21 документа та 210 фрагментів з метаданими й рівнями чутливості; порівняно чотири стратегії chunking і обрано ієрархічну; побудовано HNSW-індекси для двох моделей embeddings та перевірено процедуру upsert/delete; реалізовано гібридний пошук BM25 + dense із злиттям RRF, reranker і pre-filter за метаданими; створено золотий набір із 42 запитів та оцінено п'ять конфігурацій метриками recall@5/10, MRR і nDCG@10. Для ЛР 11 обрано конфігурацію hybrid + rerank. Результати показали, що на невеликому корпусі зі стійкою термінологією лексичний пошук є сильним базовим рівнем, а гібридний підхід і reranking підвищують стійкість до перефразувань і дозволяють відсікати запити без відповіді.")
H("Перелік джерел")
for s in ["Reimers N., Gurevych I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks // Proc. EMNLP-IJCNLP, 2019.", "Malkov Yu. A., Yashunin D. A. Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs // IEEE TPAMI, 2020, vol. 42, no. 4.", "Johnson J., Douze M., Jégou H. Billion-scale similarity search with GPUs // IEEE Transactions on Big Data, 2021, vol. 7, no. 3.", "Cormack G. V., Clarke C. L. A., Büttcher S. Reciprocal rank fusion outperforms Condorcet and individual rank learning methods // Proc. SIGIR, 2009.", "Robertson S., Zaragoza H. The Probabilistic Relevance Framework: BM25 and Beyond // Foundations and Trends in Information Retrieval, 2009.", "Järvelin K., Kekäläinen J. Cumulated gain-based evaluation of IR techniques // ACM TOIS, 2002.", "Deerwester S. et al. Indexing by latent semantic analysis // JASIS, 1990.", "Cohen J. A coefficient of agreement for nominal scales // Educational and Psychological Measurement, 1960.", "Лекція 10 «Векторні представлення знань і семантичний пошук» курсу «Сховища знань та управління знаннями», 2026."]:
    p = P(s, indent=False)
# номер сторінки
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = fp.add_run(); r.font.name = FN; r.font.size = Pt(12)
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if tag: e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag)
    else: e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt
    r._r.append(e)
doc.save("Звіт_ЛР10_Дячук_ФЕІ-42.docx"); print("saved", tn[0], "tables", fn_[0], "figs")
