# Безпека
8 атак у 6 типах (tests/attacks.jsonl). До захисту: {'mode': 'before', 'n': 8, 'succeeded': 7, 'blocked_share': 0.125}. Після: {'mode': 'after', 'n': 8, 'succeeded': 0, 'blocked_share': 1.0}.
Захисти: hub/access.py (ACL, карантин, фільтр полів), agent/policy.py (ліміти, закріплення маніфесту, заборонені дії), agent/agent.py (фільтр входу, шлюз, verify), agent/propose_fact.py (валідація, ризик).
Залишкові ризики: див. звіт.
