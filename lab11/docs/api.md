# REST API
Ендпоінти: GET /health; POST /ask (question 3–500 символів, k 1–8, use_graph); GET /sources/{id}. Автентифікація: заголовок X-API-Key (ключі з HUB_API_KEYS, зберігаються лише хеші). Ролі: viewer<employee<hr<admin за sensitivity. Ліміт: 10 запитів/хв на ключ (429 + Retry-After). Помилки: 401, 403, 404, 422, 429. OpenAPI: /docs, /openapi.json (FastAPI).

```
curl http://localhost:8000/health
curl -X POST http://localhost:8000/ask -H "X-API-Key: $HUB_KEY" -H "Content-Type: application/json" -d '{"question":"Скільки місяців триває випробувальний період?","k":3}'
curl http://localhost:8000/sources/D05-p07 -H "X-API-Key: $HUB_KEY"
```

## Результати демонстрації
- 200 — health (без ключа)
- 200 — ask, роль viewer (confidential недоступний)
- 200 — ask, роль hr
- 403 — sources/D18-p02, viewer
- 200 — sources/D18-p02, hr
- 404 — sources/невідомий id
- 401 — ask без ключа
- 401 — ask з хибним ключем
- 422 — ask, питання закоротке
- 422 — ask, k поза межами
- 200 — ask, питання про зв'язки з графом
- 200 — ліміт 3/хв, запит 1
- 200 — ліміт 3/хв, запит 2
- 200 — ліміт 3/хв, запит 3
- 429 — ліміт 3/хв, запит 4
- 429 — ліміт 3/хв, запит 5
