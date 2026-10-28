from __future__ import annotations
from typing import List
from dataclasses import dataclass
from app.tools.user_profile_check import user_profile_check
from app.tools.context_retrieval import context_retrieval
from app.tools.guardrails import is_prompt_injection
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

@dataclass
class TextToSQLResult:
    allowed_tables: List[str]
    sql: str | None
    message: str | None

class TextToSQLAgent:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)

    def run(self, user_id: str, question: str, feedback: str | None = None) -> TextToSQLResult:
        if is_prompt_injection(question):
            return TextToSQLResult([], None, "Refusing prompt injection attempt.")
        profile = user_profile_check(user_id)
        allowed = profile.get("allowed_tables", [])
        if not allowed:
            return TextToSQLResult(allowed, None, "No allowed data is available to answer your question")
        ctx = context_retrieval(question)
        messages = [
            ("system", "You are a senior analytics engineer. Generate a single Snowflake SQL SELECT that answers the user's question. Only use these tables: {allowed}. Never use other tables. Prefer simple, correct SQL. Return only SQL, no prose."),
            ("user", "Question: {question}\nHelpful context: {ctx}"),
        ]
        if feedback:
            messages.append(("system", "Previous attempt failed. Fix the SQL using this feedback: {feedback}"))
        prompt = ChatPromptTemplate.from_messages(messages)
        sql = self.llm.invoke(prompt.format_messages(
            allowed=", ".join(allowed), question=question, ctx="\n".join(ctx), feedback=feedback or "")
        ).content.strip()

        up = sql.upper()
        if not (up.startswith("SELECT") or up.startswith("WITH")):
            import re
            m = re.search(r"```(?:sql)?\s*(.*?)```", sql, re.S|re.I)
            if m: sql = m.group(1).strip()
        up = sql.upper() if sql else ""
        if not sql or not (up.startswith("SELECT") or up.startswith("WITH")):
            return TextToSQLResult(allowed, None, "Failed to compose a valid SQL SELECT.")
        return TextToSQLResult(allowed, sql, None)
