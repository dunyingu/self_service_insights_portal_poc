from typing import List, Dict
from app.tools.snowflake_utils import execute_sql
from app.config import settings

def user_profile_check(user_id: str) -> Dict[str, List[str]]:
    if settings.use_fake_db:
        return {"roles": ["ANALYST"], "allowed_tables": ["SALES"]}
    sql = f"""    SELECT ROLE, TABLE_NAME
    FROM RBAC_METADATA
    WHERE USER_ID = '{user_id}' AND PRIVILEGE IN ('SELECT','USAGE')"""
    df = execute_sql(sql)
    roles = sorted(set(df["ROLE"].tolist())) if not df.empty else []
    allowed = sorted(set(df["TABLE_NAME"].tolist())) if not df.empty else []
    return {"roles": roles, "allowed_tables": allowed}
