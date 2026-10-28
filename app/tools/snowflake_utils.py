from __future__ import annotations
import os, re, logging
from contextlib import contextmanager
from typing import Any, Iterable, Optional
import pandas as pd
from app.config import settings

DDL_BANNED = re.compile(r"\b(DROP|TRUNCATE|ALTER|CREATE|MERGE|DELETE|UPDATE|GRANT|REVOKE)\b", re.I)
log = logging.getLogger(__name__)

try:
    import snowflake.connector  # type: ignore
except Exception:  # pragma: no cover
    snowflake = None  # noqa

class FakeDB:
    def __init__(self):
        self.tables = {
            "SALES": pd.DataFrame({
                "ORDER_DATE": pd.to_datetime(["2025-09-01","2025-09-02","2025-09-03"]),
                "REGION": ["VIC","NSW","VIC"],
                "AMOUNT": [1200, 900, 1700],
            }),
            "CUSTOMERS": pd.DataFrame({
                "CUSTOMER_ID": [1,2,3],
                "SEGMENT": ["Retail","Wholesale","Retail"],
                "REGION": ["VIC","NSW","VIC"],
            })
        }
    @contextmanager
    def connect(self, role: Optional[str]=None):
        yield self
    def query(self, sql: str, params: Optional[Iterable[Any]]=None):
        if DDL_BANNED.search(sql):
            raise ValueError("Dangerous SQL blocked by guardrails")
        up = sql.upper()
        if " FROM SALES" in up and "SELECT" in up:
            return self.tables["SALES"]
        elif " FROM CUSTOMERS" in up and "SELECT" in up:
            return self.tables["CUSTOMERS"]
        return pd.DataFrame()

_FAKE_DB = FakeDB()

@contextmanager
def get_connection(role: Optional[str] = None):
    if settings.use_fake_db or not settings.snowflake_account:
        yield _FAKE_DB
    else:  # pragma: no cover
        assert snowflake is not None, "snowflake-connector not installed"
        con = snowflake.connector.connect(
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            account=settings.snowflake_account,
            warehouse=settings.snowflake_warehouse,
            database=settings.snowflake_database,
            schema=settings.snowflake_schema,
            session_parameters={"QUERY_TAG": "insights-portal"},
        )
        cs = con.cursor()
        try:
            if role:
                cs.execute(f"USE ROLE {role}")
            yield con
        finally:
            cs.close()
            con.close()

def explain_sql(sql: str, role: Optional[str] = None) -> str:
    if DDL_BANNED.search(sql):
        raise ValueError("SQL contains banned keywords")
    if settings.use_fake_db:
        return "FAKE PLAN: ok"
    with get_connection(role) as con:  # pragma: no cover
        cur = con.cursor()
        try:
            cur.execute("EXPLAIN USING TEXT \n" + sql)
            rows = cur.fetchall()
            return "\n".join(r[0] for r in rows)
        finally:
            cur.close()

def execute_sql(sql: str, role: Optional[str] = None) -> pd.DataFrame:
    if DDL_BANNED.search(sql):
        raise ValueError("SQL contains banned keywords")
    if settings.use_fake_db:
        return _FAKE_DB.query(sql)
    with get_connection(role) as con:  # pragma: no cover
        cur = con.cursor()
        try:
            cur.execute(sql)
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=cols)
        finally:
            cur.close()
