import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def is_email_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP. Returns False and logs if SMTP is not configured."""
    if not is_email_configured():
        logger.info(f"[EMAIL DISABLED] To: {to_email} | Subject: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.ehlo()
            if settings.SMTP_TLS:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def build_job_digest_html(jobs: List[dict], user_name: str) -> str:
    cards = ""
    for j in jobs[:20]:
        cards += f"""
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:10px">
          <div style="font-weight:600;font-size:15px;color:#0f172a">{j['title']}</div>
          <div style="color:#64748b;font-size:13px">{j.get('company','')} &bull; {j.get('location','')}</div>
          <div style="margin-top:6px">
            <a href="{j.get('platform_url','#')}" style="background:#4f46e5;color:#fff;padding:6px 12px;border-radius:6px;text-decoration:none;font-size:12px">Apply Now</a>
            <span style="margin-left:8px;font-size:12px;color:#10b981;font-weight:600">Match: {int(j.get('match_score',0)*100)}%</span>
          </div>
        </div>"""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#0f172a">Hi {user_name}, here are your new job matches</h2>
      {cards or '<p>No new matching jobs this time.</p>'}
      <p style="color:#94a3b8;font-size:12px">Sent by JobApply AI - you can adjust this in your Platform settings.</p>
    </div>"""