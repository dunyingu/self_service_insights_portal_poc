# Multi‑Agent NLP Insights Portal (LangGraph + Snowflake)

This version incorporates:
- Master → cache reuse & data update check before routing to Text‑to‑SQL
- KNN context retrieval from Snowflake vector tables (semantic YAML + business docs)
- Bi‑directional edges: Master↔T2SQL, T2SQL↔Verify (rewrite loop)
- Session memory via LangGraph checkpointer + Snowflake logs
- Deploy to Azure Container Apps

