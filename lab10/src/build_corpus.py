"""Результат 1: збирання корпусу. kb_src -> kb/*.md (сирі, з шумом) -> очищення -> data/corpus.jsonl"""
import re, json, glob, os, collections, random
random.seed(42)
SENS = ["public", "internal", "confidential", "restricted"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 1. розбір джерельних файлів і запис «сирих» md з типовим шумом вебсторінки
docs = []
for fn in sorted(glob.glob(f"{ROOT}/kb_src/part*.txt")):
    cur = None
    for line in open(fn, encoding="utf-8").read().splitlines():
        if line.startswith("="):
            did, title, typ, date, sens = line[1:].split("|")
            cur = dict(doc_id=did, title=title, type=typ, date=date, sensitivity=sens, sections=[])
            docs.append(cur)
        elif line.startswith("#"):
            cur["sections"].append([line[1:], []])
        elif line.strip():
            cur["sections"][-1][1].append(line)
os.makedirs(f"{ROOT}/kb", exist_ok=True)
for d in docs:
    out = ["---", f"doc_id: {d['doc_id']}", f"title: {d['title']}", f"type: {d['type']}",
           f"date: {d['date']}", f"sensitivity: {d['sensitivity']}", f"source_url: internal://hub/kb/{d['doc_id']}",
           "---", f"Головна > Управління персоналом > {d['title']}", "Цей сайт використовує cookie. Прийняти | Налаштувати", f"# {d['title']}", ""]
    for i, (sec, ps) in enumerate(d["sections"], 1):
        out += [f"## {sec}", ""]
        for p in ps: out += [p, ""]
        if i % 2 == 0: out += ["Наверх ↑", ""]
        if i == 3: out += [f"Сторінка 2 з 4", ""]
    out += ["Поділитися | Друкувати | Наверх", f"Сторінка 4 з 4", "© Відділ персоналу, 2025. Усі права захищено. Контакти: hr@example.org", ""]
    open(f"{ROOT}/kb/{d['doc_id']}.md", "w", encoding="utf-8").write("\n".join(out))

# ---- 2. правила очищення (описані в docs/corpus_card.md)
RULES = {
 "R1_breadcrumb": re.compile(r"^Головна\s*>"),
 "R2_page_number": re.compile(r"^Сторінка \d+ з \d+$"),
 "R3_copyright": re.compile(r"^©"),
 "R4_nav_buttons": re.compile(r"^(Наверх|Поділитися|Друкувати)"),
 "R5_cookie_banner": re.compile(r"^Цей сайт використовує cookie"),
}
removed = collections.Counter()
def clean_lines(lines):
    keep = []
    for ln in lines:
        s = ln.strip()
        hit = next((k for k, r in RULES.items() if r.match(s)), None)
        if hit: removed[hit] += 1; continue
        keep.append(re.sub(r"\s+", " ", s))   # R6: нормалізація пробілів
    return keep

# ---- 3. очищення, розбиття на фрагменти (абзаци) та метадані
frags, raw_lines = [], 0
for fn in sorted(glob.glob(f"{ROOT}/kb/D*.md")):
    txt = open(fn, encoding="utf-8").read()
    meta_block, body = txt.split("---\n")[1], txt.split("---\n", 2)[2]
    meta = dict(l.split(": ", 1) for l in meta_block.strip().splitlines())
    lines = body.splitlines(); raw_lines += len(lines)
    lines = clean_lines(lines)
    sec, sidx, pidx = None, 0, 0
    for ln in lines:
        if not ln or ln.startswith("# "): continue
        if ln.startswith("## "): sec = ln[3:]; sidx += 1; continue
        pidx += 1
        sens = meta["sensitivity"]
        if ln.startswith("[R]"):               # абзац з обмеженим доступом (персональні/кадрові деталі)
            ln = ln[3:]; sens = "restricted"
        frags.append(dict(id=f"{meta['doc_id']}-p{pidx:02d}", doc_id=meta["doc_id"], title=meta["title"], section=sec,
            section_idx=sidx, para_idx=pidx, type=meta["type"], date=meta["date"], sensitivity=sens,
            restricted=(SENS.index(sens) >= 2), source_url=meta["source_url"], lang="uk", text=ln, n_words=len(ln.split())))
os.makedirs(f"{ROOT}/data", exist_ok=True)
with open(f"{ROOT}/data/corpus.jsonl", "w", encoding="utf-8") as f:
    for r in frags: f.write(json.dumps(r, ensure_ascii=False) + "\n")
stats = dict(n_docs=len(set(r["doc_id"] for r in frags)), n_frags=len(frags), raw_lines=raw_lines,
    removed=dict(removed), removed_total=sum(removed.values()),
    words_total=sum(r["n_words"] for r in frags), words_mean=round(sum(r["n_words"] for r in frags)/len(frags), 1),
    by_type=dict(collections.Counter(r["type"] for r in frags)),
    by_sens=dict(collections.Counter(r["sensitivity"] for r in frags)),
    docs_by_sens=dict(collections.Counter(d["sensitivity"] for d in docs)))
json.dump(stats, open(f"{ROOT}/results/corpus_stats.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(stats, ensure_ascii=False, indent=1))
