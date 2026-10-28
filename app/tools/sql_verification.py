from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List
import sqlparse
from app.tools.snowflake_utils import explain_sql

SAFE_READONLY = re.compile(r"\b(SELECT|WITH)\b", re.I)

@dataclass
class SQLCheckResult:
    ok: bool
    feedback: str

def sql_verification(sql: str, user_id: str, allowed_tables: List[str]) -> SQLCheckResult:
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return SQLCheckResult(False, "Empty SQL")
    except Exception as e:
        return SQLCheckResult(False, f"Syntax error: {e}")

    if not SAFE_READONLY.search(sql) or re.search(r"\b(UPDATE|DELETE|INSERT|MERGE|DROP|ALTER)\b", sql, re.I):
        return SQLCheckResult(False, "Only read‑only SELECT/WITH statements are allowed.")

    up = sql.upper()
    not_allowed = [t for t in re.findall(r"FROM\s+([A-Z0-9_\.]+)", up) if t.split('.')[-1] not in allowed_tables]
    if not_allowed:
        return SQLCheckResult(False, f"References to non‑permitted tables: {', '.join(not_allowed)}")

    try:
        _ = explain_sql(sql, role=None)
    except Exception as e:
        return SQLCheckResult(False, f"Explain failed: {e}")
    return SQLCheckResult(True, "OK")
