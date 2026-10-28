from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.graph import graph
from typing import Optional

app = FastAPI(title="Insights Portal API", version="2.0.0" )

class AskRequest(BaseModel):
    user_id: str
    session_id: str
    question: str
    send_email: bool = False
    email_to: Optional[str] = None

class AskResponse(BaseModel):
    insights: str
    chart_spec: dict
    dataframe_preview: list
    data_json: list

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        out = graph.invoke({
            "user_id": req.user_id,
            "session_id": req.session_id,
            "question": req.question,
            "send_email": req.send_email,
            "email_to": req.email_to,
        })
        insights_val = out.get("insights") or out.get("sql_check_feedback") or out.get("error") or ""
        return AskResponse(
            insights=insights_val,
            chart_spec=out.get("chart_spec", {}),
            dataframe_preview=out.get("dataframe_preview", []),
            data_json=out.get("data_json", []),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/healthz")
def healthz():
    return {"ok": True}
