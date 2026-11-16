"""Інструмент: SQL-інваріанти (SQLite; еквівалент SPARQL/Cypher-запитів-інваріантів)."""
import sqlite3, pytest
@pytest.fixture
def db(S):
    c = sqlite3.connect(":memory:"); c.execute("create table r(id, doc_id, date, restricted, sensitivity)"); c.executemany("insert into r values(?,?,?,?,?)", [(x["id"], x["doc_id"], x["date"], int(bool(x.get("restricted"))), x["sensitivity"]) for x in S]); return c
def test_10_sql_id_prefix_matches_doc(db): assert db.execute("select count(*) from r where id not like doc_id || '-p%'").fetchone()[0] == 0
def test_11_sql_no_future_dates(db): assert db.execute("select count(*) from r where date > '2026-11-16'").fetchone()[0] == 0
def test_12_sql_unique_id(db): assert db.execute("select count(*) from (select id from r group by id having count(*)>1)").fetchone()[0] == 0
