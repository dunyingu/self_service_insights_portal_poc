from __future__ import annotations
from typing import List
import logging
from app.config import settings
from app.tools.snowflake_utils import execute_sql
try:
    from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None
    AzureOpenAIEmbeddings = None

log = logging.getLogger(__name__)

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

def _knn_sql(table: str, emb: list[float], k: int) -> str:
    vec = ",".join(str(float(x)) for x in emb)
    dist = f"VECTOR_COSINE_DISTANCE(EMBEDDING, VECTOR_CONSTRUCT({vec}))"
    return f"""        SELECT CHUNK_TEXT AS context
        FROM {table}
        ORDER BY {dist} ASC
        LIMIT {k}
    """

def context_retrieval(question: str, k: int = 5) -> List[str]:
    if settings.use_fake_db:
        return [
            "Metric 'Revenue' = SUM(AMOUNT)",
            "Date grain: day; Region dimension from SALES.REGION",
        ]
    if not (settings.semantic_model_table or settings.business_docs_table):
        log.warning("Vector tables not configured; returning empty context.")
        return []
    emb = _embed(question)
    snippets: list[str] = []
    half = max(1, k // 2)
    try:
        if settings.semantic_model_table:
            sql = _knn_sql(settings.semantic_model_table, emb, half)
            df = execute_sql(sql)
            if not df.empty:
                snippets += df["context"].astype(str).tolist()
        if settings.business_docs_table:
            sql = _knn_sql(settings.business_docs_table, emb, k - len(snippets))
            df = execute_sql(sql)
            if not df.empty:
                snippets += df["context"].astype(str).tolist()
    except Exception as e:
        log.exception("context_retrieval failed: %s", e)
    return snippets[:k]
