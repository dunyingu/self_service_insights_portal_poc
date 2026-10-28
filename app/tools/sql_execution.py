from typing import List, Dict, Any
import pandas as pd, json
from app.tools.snowflake_utils import execute_sql
from app.tools.sql_verification import sql_verification

def sql_execution(sql: str, user_id: str, allowed_tables: List[str]) -> pd.DataFrame:
    check = sql_verification(sql, user_id, allowed_tables)
    if not check.ok:
        raise ValueError(f"SQL failed verification: {check.feedback}")
    df = execute_sql(sql, role=None)
    return df

def data_to_json(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return json.loads(df.to_json(orient='records', date_format='iso'))
