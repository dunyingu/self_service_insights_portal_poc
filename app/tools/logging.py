from __future__ import annotations
import hashlib, json
from typing import Dict, Any
from app.tools.snowflake_utils import execute_sql
from app.config import settings
from app.tools.guardrails import redact_pii

def _hash_rows(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()

def log_session_event(session_id: str, user_id: str, question: str, sql: str | None,
                      rows: list[dict], insights: str, reused: bool):
    question = redact_pii(question)
    h = _hash_rows(rows)
    if settings.use_fake_db:
        print("LOG:", session_id, user_id, question, h, reused)
        return
    sql_ins = f"""    INSERT INTO SESSION_LOGS (SESSION_ID, USER_ID, QUESTION, SQL_TEXT, ROWS_HASH, INSIGHTS, REUSED, TS)
    VALUES ('{session_id}','{user_id}', $$ {question} $$, $$ {sql or ''} $$, '{h}', $$ {insights} $$, {int(reused)}, CURRENT_TIMESTAMP)
    """
    execute_sql(sql_ins)

def similar_question_retrieval(question_embedding: list[float]) -> dict | None:
    if settings.use_fake_db:
        return None
    vec = ",".join(str(float(x)) for x in question_embedding)
    sql = f"""        SELECT QUESTION, SQL_TEXT, ROWS_JSON, ANSWERED_TS
        FROM QNA_CACHE
        ORDER BY VECTOR_COSINE_DISTANCE(QUESTION_EMB, VECTOR_CONSTRUCT({vec})) ASC
        LIMIT 1
    """
    df = execute_sql(sql)
    if df.empty:
        return None
    r = df.iloc[0].to_dict()
    return {
        "question": r.get("QUESTION"),
        "sql_text": r.get("SQL_TEXT"),
        "rows_json": r.get("ROWS_JSON"),
        "answered_ts": str(r.get("ANSWERED_TS")),
    }

def data_update_check(sql_text: str, last_answer_ts: str) -> bool:
    if settings.use_fake_db:
        return False
    import re
    tables = set(re.findall(r"[Ff][Rr][Oo][Mm]\s+([A-Z0-9_\.]+)", sql_text.upper()))
    if not tables:
        return False
    statements = []
    for t in tables:
        parts = t.split('.')
        if len(parts) == 3:
            db, schema, tbl = parts
        elif len(parts) == 2:
            db = settings.snowflake_database or ""
            schema, tbl = parts
        else:
            db = settings.snowflake_database or ""
            schema = settings.snowflake_schema or "PUBLIC"
            tbl = parts[0]
        statements.append(f"(SELECT LAST_ALTERED FROM {db}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{schema}' AND TABLE_NAME='{tbl}')")
    union_sql = " UNION ALL ".join(statements)
    sql = f"SELECT MAX(LAST_ALTERED) AS MAX_ALTERED FROM ({union_sql})"
    df = execute_sql(sql)
    if df.empty or df.iloc[0]["MAX_ALTERED"] is None:
        return False
    max_altered = str(df.iloc[0]["MAX_ALTERED"])
    return max_altered > last_answer_ts
