from __future__ import annotations
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from app.state import PortalState
from app.agents.t2sql_agent import TextToSQLAgent
from app.agents.sql_verify_exec_agent import SQLVerifyExecuteAgent
from app.agents.master_agent import MasterAgent, precheck
from app.config import settings

t2sql = TextToSQLAgent()
verexec = SQLVerifyExecuteAgent()
master = MasterAgent()

# ---- Node functions ----
def node_master(state: PortalState) -> Dict[str, Any]:
    # 1) Try reuse
    reused, rows, insights, sql_text = precheck(state["question"])
    if reused:
        return {"reused_from_cache": True, "data_json": rows, "insights": insights, "route": "present"}
    # else go to t2sql
    return {"reused_from_cache": False, "route": "t2sql", "retry_count": state.get("retry_count", 0)}

def node_t2sql(state: PortalState) -> Dict[str, Any]:
    res = t2sql.run(state["user_id"], state["question"], feedback=state.get("last_feedback"))
    if res.message:
        # bi-directional: send denial back to master/present for user-facing message
        return {"route": "present", "sql": "", "allowed_resources": res.allowed_tables,
                "data_json": [], "insights": res.message}
    return {"sql": res.sql, "allowed_resources": res.allowed_tables, "route": "verify"}

def node_verify_exec(state: PortalState) -> Dict[str, Any]:
    out = verexec.run(state["sql"], state["user_id"], state["allowed_resources"])
    if not out.ok:
        retries = int(state.get("retry_count", 0)) + 1
        if retries <= 2:  # bounded rewrite attempts
            return {"last_feedback": out.feedback, "retry_count": retries, "route": "t2sql"}
        # exceeded retries → present the feedback
        return {"sql_check_feedback": out.feedback, "route": "present"}
    rows = out.rows or []
    return {"data_json": rows, "route": "present", "retry_count": 0, "last_feedback": ""}

def node_present(state: PortalState) -> Dict[str, Any]:
    # If insights already present (e.g., denial or reused), just ship it; else compute full presentation
    if state.get("insights") and state.get("data_json") is not None:
        return {}
    pres = master.present(
        session_id=state["session_id"],
        user_id=state["user_id"],
        question=state["question"],
        rows=state.get("data_json", []),
        send_email=state.get("send_email", False),
        email_to=state.get("email_to"),
    )
    return {"insights": pres.insights, "chart_spec": pres.chart_spec, "dataframe_preview": pres.df_preview}

# ---- Graph wiring ----
workflow = StateGraph(PortalState)
workflow.add_node("master", node_master)
workflow.add_node("t2sql", node_t2sql)
workflow.add_node("verify", node_verify_exec)
workflow.add_node("present", node_present)

workflow.add_edge(START, "master")

def router(state: PortalState):
    r = state.get("route")
    if r == "t2sql": return "t2sql"
    if r == "verify": return "verify"
    if r == "present": return "present"
    return "t2sql"

# master → (present|t2sql)
workflow.add_conditional_edges("master", router, {"t2sql": "t2sql", "present": "present"})
# t2sql → (verify|present)
workflow.add_conditional_edges("t2sql", router, {"verify": "verify", "present": "present"})
# verify → (t2sql|present)
workflow.add_conditional_edges("verify", router, {"t2sql": "t2sql", "present": "present"})
# present → END
workflow.add_edge("present", END)

checkpointer = None
if settings.checkpoint_db:
    checkpointer = SqliteSaver.from_conn_string(settings.checkpoint_db)

graph = workflow.compile(checkpointer=checkpointer)
