import re
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s()-]{7,}\d")
def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub("[redacted-email]", text)
    text = PHONE_RE.sub("[redacted-phone]", text)
    return text
BANNED_PROMPTS = ["ignore previous instructions", "system prompt", "secrets", "password"]
def is_prompt_injection(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in BANNED_PROMPTS)
