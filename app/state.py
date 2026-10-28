from typing import TypedDict, Optional, List, Dict, Any
from typing_extensions import NotRequired

class PortalState(TypedDict, total=False):
    # Inputs
    user_id: str
    session_id: str
    question: str
    email_to: NotRequired[str]
    send_email: NotRequired[bool]

    # Derived / shared
    allowed_resources: List[str]
    context_snippets: List[str]
    sql: str
    sql_check_feedback: str
    data_json: List[Dict[str, Any]]
    insights: str
    chart_spec: Dict[str, Any]
    dataframe_preview: List[Dict[str, Any]]
    route: str
    reused_from_cache: bool
    retry_count: int
    last_feedback: NotRequired[str]
    cached_rows: NotRequired[List[Dict[str, Any]]]

    # Logging / debug
    similar_question_id: NotRequired[str]
    reused_answer_hash: NotRequired[str]
    error: NotRequired[str]
