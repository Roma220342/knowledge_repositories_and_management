# Після покращення

## Метрики якості
| метрика | baseline | після | поріг |
|--|--|--|--|
| completeness | 0.8991 | 1.0 | 0.99 |
| validity_dates | 0.9167 | 1.0 | 0.99 |
| provenance | 0.9035 | 1.0 | 0.99 |
| uniqueness_text | 0.9386 | 1.0 | 0.99 |
| consistency_values | 4 | 0 | 0 |
| consistency_logical | 2 | 0 | 0 |
| timeliness | 0.7456 | 0.8131 | 0.85 |
| accuracy | 0.9667 | 1.0 | 0.95 |
| availability_graph | 1.0 | 1.0 | 1.0 |
| terminology | 0.9825 | 1.0 | 1.0 |
| uniqueness_entities | 0.9386 | 1.0 | 0.95 |

## Метрики RAG (ЛР 11, 33 тести)
| метрика | до | після |
|--|--|--|
| faithfulness | 1.0 | 1.0 |
| context_recall | 0.925 | 0.75 |
| citation_accuracy | 0.575 | 0.5 |
| abstention_rate_noanswer | 0.875 | 0.875 |
| false_abstain_answerable | 0.062 | 0.062 |
| answer_hit_rate | 0.75 | 0.75 |
| conflict_flagged | 1.0 | 0.25 |
| stale_answers | 3/4 | 1/4 |
| dup_context_share | 0.017 | 0.0 |

Висновки та процес підтримки — у звіті.
