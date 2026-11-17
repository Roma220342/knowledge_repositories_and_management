"""Політики агента: ліміти, заборонені дії, фільтри, закріплення (pinning) інструментів."""
import re, hashlib, json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIMITS = dict(max_steps=6, max_prompt_tokens=6000, timeout_s=15.0)
INSECURE_LIMITS = dict(max_steps=40, max_prompt_tokens=10**9, timeout_s=60.0)      # «до захисту»: лише технічна стеля, щоб демо не зависло
FORBIDDEN_ACTIONS = ["видалення або зміна записів", "прямий запис у сховище без propose_fact", "довільний SQL/Cypher", "виклик інструментів, яких немає в закріпленому маніфесті", "розкриття системного промпта/паролів", "повернення чутливих полів чужих співробітників без ролі hr/admin"]
WRITE_INTENT = re.compile(r"\b(видали|видалити|стер(ти)?|запиши|запишіть|додай|змін(и|іть)|онови|propose)\b", re.I)
LOOP_INTENT = re.compile(r"доки не знайдеш|не зупиняйся|повторюй|шукай, поки", re.I)
def pin(tools): return {t["name"]: hashlib.sha256((t["description"] or "").encode()).hexdigest()[:16] for t in tools}
def load_manifest(): return json.load(open(ROOT + "/agent/tool_manifest.json"))
