from __future__ import annotations
import yagmail
from typing import Optional
from app.config import settings

def send_email_html(to: str, subject: str, html_body: str, attachment_path: Optional[str]=None):
    if not settings.email_user or not settings.email_app_password:
        raise RuntimeError("Email is not configured. Set EMAIL_USER and EMAIL_APP_PASSWORD.")
    yag = yagmail.SMTP(settings.email_user, settings.email_app_password)
    contents = [yagmail.inline(html_body)]
    if attachment_path:
        contents.append(attachment_path)
    yag.send(to=to, subject=subject, contents=contents)
