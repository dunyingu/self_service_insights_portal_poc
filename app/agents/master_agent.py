from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from app.tools.insights import data_to_insights
from app.tools.charts import data_to_charts
from app.tools.json_dataframe import json_to_dataframe
from app.tools.emailer import send_email_html
from app.tools.logging import log_session_event, similar_question_retrieval, data_update_check
from app.config import settings
try:
    from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None
    AzureOpenAIEmbeddings = None

@dataclass
class Presentation:
    insights: str
    chart_spec: Dict[str, Any]
    df_preview: List[Dict[str, Any]]

def _embed(text: str) -> list[float]:
    if settings.azure_openai_api_key and AzureOpenAIEmbeddings:
        emb = AzureOpenAIEmbeddings(
            azure_deployment=settings.embedding_model or "text-embedding-3-large",
            openai_api_key=settings.azure_openai_api_key,
            openai_api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        return emb.embed_query(text)
    if settings.openai_api_key and OpenAIEmbeddings:
        emb = OpenAIEmbeddings(model=settings.embedding_model or "text-embedding-3-large")
        return emb.embed_query(text)
    return [0.0,0.0,0.0]

def precheck(question: str) -> Tuple[bool, List[Dict[str, Any]], str | None, str | None]:
    """Check for similar answered question and data freshness.
    Returns (reused, rows, insights, sql_text).
    """
    hit = similar_question_retrieval(_embed(question))
    if not hit or not hit.get("rows_json"):
        return (False, [], None, None)
    sql_text = hit.get("sql_text") or ""
    last_ts = hit.get("answered_ts") or ""
    if data_update_check(sql_text, last_ts):
        return (False, [], None, None)
    import json
    rows = json.loads(hit["rows_json"])
    insights = data_to_insights(rows)
    return (True, rows, insights, sql_text)

class MasterAgent:
    def present(self, session_id: str, user_id: str, question: str, rows: List[Dict[str, Any]],
                send_email: bool=False, email_to: str|None=None) -> Presentation:
        insights = data_to_insights(rows)
        chart = data_to_charts(rows)
        df = json_to_dataframe(rows)
        preview = df.head(25).to_dict(orient='records')
        if send_email and email_to:
            html = f"""<h3>Insights</h3><p>{insights}</p><h3>Sample rows</h3><pre>{preview}</pre>"""
            try:
                send_email_html(email_to, subject="Insights Portal results", html_body=html)
            except Exception as e:
                insights += f" | (Email failed: {e})"
        log_session_event(session_id, user_id, question, None, rows, insights, reused=False)
        return Presentation(insights, chart, preview)
