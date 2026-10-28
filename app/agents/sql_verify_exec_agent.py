from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from app.tools.sql_verification import sql_verification
from app.tools.sql_execution import sql_execution, data_to_json

@dataclass
class VerificationOutcome:
    ok: bool
    feedback: str | None
    rows: List[Dict[str, Any]] | None

class SQLVerifyExecuteAgent:
    def run(self, sql: str, user_id: str, allowed_tables: List[str]) -> VerificationOutcome:
        check = sql_verification(sql, user_id, allowed_tables)
        if not check.ok:
            return VerificationOutcome(False, check.feedback, None)
        df = sql_execution(sql, user_id, allowed_tables)
        rows = data_to_json(df)
        return VerificationOutcome(True, None, rows)
