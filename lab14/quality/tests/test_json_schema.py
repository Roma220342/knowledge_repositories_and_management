"""Інструмент: JSON Schema (jsonschema)."""
import jsonschema
SCHEMA = {"type": "object", "required": ["id", "doc_id", "title", "section", "text", "date", "sensitivity", "source_url"], "properties": {"id": {"type": "string", "pattern": r"^(D|X)\d+-p\d+$"}, "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}, "sensitivity": {"enum": ["public", "internal", "confidential", "restricted"]}, "source_url": {"type": "string", "pattern": r"^internal://hub/kb/"}, "text": {"type": "string", "minLength": 20}}}
def test_01_record_json_schema(S):
    bad = []
    for c in S:
        try: jsonschema.validate(c, SCHEMA)
        except jsonschema.ValidationError as e: bad.append((c["id"], e.message[:60]))
    assert not bad, f"порушень схеми: {len(bad)}: {bad[:5]}"
