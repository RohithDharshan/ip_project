"""
Email Service
──────────────
Sends SMTP emails for:
  • New proposal submitted (to approvers)
  • Approval / rejection notifications
  • Reminders for pending approvals
  • Status updates to proposal submitters

Falls back to console logging if SMTP is not configured.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from config import settings

logger = logging.getLogger(__name__)

_SMTP_CONFIGURED = bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


# ─── Templates ───────────────────────────────────────────────────────────────

def _approval_request_html(approver_name: str, proposal_title: str, proposal_id: int) -> str:
    return f"""
<html><body>
<p>Dear {approver_name},</p>
<p>A new event proposal requires your approval:</p>
<ul>
  <li><strong>Title:</strong> {proposal_title}</li>
  <li><strong>Proposal ID:</strong> #{proposal_id}</li>
</ul>
<p>Please log in to the <a href="http://localhost:3000/approvals">Workflow Dashboard</a> to review.</p>
<br><p>— PSG AI Consortium Workflow System</p>
</body></html>
"""


def _status_update_html(faculty_name: str, proposal_title: str, status: str) -> str:
    color = "green" if "approved" in status.lower() else "red" if "rejected" in status.lower() else "orange"
    return f"""
<html><body>
<p>Dear {faculty_name},</p>
<p>Your proposal <strong>"{proposal_title}"</strong> status has been updated to:</p>
<p style="color:{color};font-size:18px;font-weight:bold;">{status.replace('_',' ').title()}</p>
<p>Visit the <a href="http://localhost:3000">dashboard</a> for details.</p>
<br><p>— PSG AI Consortium Workflow System</p>
</body></html>
"""


# ─── Sender ───────────────────────────────────────────────────────────────────

def _send(to_emails: List[str], subject: str, html_body: str) -> bool:
    if not _SMTP_CONFIGURED:
        logger.info(f"[EmailService] (SMTP not configured) Would send to {to_emails}: {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = settings.SMTP_FROM
        msg["To"]      = ", ".join(to_emails)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_emails, msg.as_string())

        logger.info(f"[EmailService] Email sent to {to_emails}: {subject}")
        return True
    except Exception as exc:
        logger.warning(f"[EmailService] Failed to send email: {exc}")
        return False


# ─── Public API ───────────────────────────────────────────────────────────────

class EmailService:

    @staticmethod
    def send_approval_request(
        approver_email: str,
        approver_name:  str,
        proposal_title: str,
        proposal_id:    int,
    ) -> bool:
        subject = f"[Action Required] Approval Request: {proposal_title}"
        html    = _approval_request_html(approver_name, proposal_title, proposal_id)
        return _send([approver_email], subject, html)

    @staticmethod
    def send_status_update(
        faculty_email:  str,
        faculty_name:   str,
        proposal_title: str,
        status:         str,
    ) -> bool:
        subject = f"[Workflow Update] Proposal '{proposal_title}' — {status.replace('_',' ').title()}"
        html    = _status_update_html(faculty_name, proposal_title, status)
        return _send([faculty_email], subject, html)

    @staticmethod
    def send_reminder(
        approver_email: str,
        approver_name:  str,
        proposal_title: str,
        proposal_id:    int,
    ) -> bool:
        subject = f"[Reminder] Pending Approval: {proposal_title}"
        html    = _approval_request_html(approver_name, proposal_title, proposal_id)
        return _send([approver_email], subject, html)
