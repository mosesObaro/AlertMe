"""Provider-agnostic email sender supporting Resend, Brevo, SendGrid, SMTP, and Dry-Run."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from src.utils.logger import logger

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class EmailSender:
    """Dispatches rendered emails to the user's inbox via configured free provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.provider = (
            os.environ.get("EMAIL_PROVIDER") or
            self.config.get("provider", "console")
        ).lower()
        self.sender_email = (
            os.environ.get("SENDER_EMAIL") or
            self.config.get("sender_email", "research-alert@resend.dev")
        )
        self.recipient_email = (
            os.environ.get("EMAIL_RECIPIENT") or
            self.config.get("recipient_email", "user@example.com")
        )

    def send(self, subject: str, html_body: str, text_body: str) -> bool:
        """Dispatches email to recipient using the active provider."""
        logger.info(f"Dispatching email via [{self.provider}] to [{self.recipient_email}]...")

        # Always save dry-run snapshot to output directory for local inspection
        try:
            with open(OUTPUT_DIR / "latest_email.html", "w", encoding="utf-8") as f:
                f.write(html_body)
            with open(OUTPUT_DIR / "latest_email.txt", "w", encoding="utf-8") as f:
                f.write(text_body)
        except Exception as e:
            logger.debug(f"Failed to write email snapshot to {OUTPUT_DIR}: {e}")

        if self.provider == "console" or self.provider == "dry_run":
            logger.info("=== DRY RUN / CONSOLE EMAIL DISPATCH ===")
            logger.info(f"Subject: {subject}")
            logger.info(f"To: {self.recipient_email}")
            logger.info(f"HTML Snapshot saved to: {OUTPUT_DIR / 'latest_email.html'}")
            return True

        elif self.provider == "resend":
            return self._send_resend(subject, html_body, text_body)

        elif self.provider == "brevo":
            return self._send_brevo(subject, html_body, text_body)

        elif self.provider == "sendgrid":
            return self._send_sendgrid(subject, html_body, text_body)

        elif self.provider == "smtp":
            return self._send_smtp(subject, html_body, text_body)

        else:
            logger.error(f"Unknown email provider: {self.provider}. Email not sent.")
            return False

    def _send_resend(self, subject: str, html_body: str, text_body: str) -> bool:
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            logger.error("RESEND_API_KEY environment variable is missing.")
            return False

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": self.sender_email,
            "to": [self.recipient_email],
            "subject": subject,
            "html": html_body,
            "text": text_body
        }

        try:
            res = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                logger.info(f"Email successfully delivered via Resend. ID: {res.json().get('id')}")
                return True
            else:
                logger.error(f"Resend delivery failed: HTTP {res.status_code} - {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending via Resend: {e}")
            return False

    def _send_brevo(self, subject: str, html_body: str, text_body: str) -> bool:
        api_key = os.environ.get("BREVO_API_KEY")
        if not api_key:
            logger.error("BREVO_API_KEY environment variable is missing.")
            return False

        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "sender": {"email": self.sender_email, "name": "Edge PhD Intelligence"},
            "to": [{"email": self.recipient_email}],
            "subject": subject,
            "htmlContent": html_body,
            "textContent": text_body
        }

        try:
            res = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                logger.info("Email successfully delivered via Brevo.")
                return True
            else:
                logger.error(f"Brevo delivery failed: HTTP {res.status_code} - {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending via Brevo: {e}")
            return False

    def _send_sendgrid(self, subject: str, html_body: str, text_body: str) -> bool:
        api_key = os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            logger.error("SENDGRID_API_KEY environment variable is missing.")
            return False

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "personalizations": [{"to": [{"email": self.recipient_email}]}],
            "from": {"email": self.sender_email, "name": "Edge PhD Intelligence"},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body}
            ]
        }

        try:
            res = requests.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 202]:
                logger.info("Email successfully delivered via SendGrid.")
                return True
            else:
                logger.error(f"SendGrid delivery failed: HTTP {res.status_code} - {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending via SendGrid: {e}")
            return False

    def _send_smtp(self, subject: str, html_body: str, text_body: str) -> bool:
        host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("SMTP_PORT", 587))
        user = os.environ.get("SMTP_USER") or self.sender_email
        password = os.environ.get("SMTP_PASSWORD")

        if not user or not password:
            logger.error("SMTP_USER or SMTP_PASSWORD environment variables are missing.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = self.recipient_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                    server.login(user, password)
                    server.sendmail(user, self.recipient_email, msg.as_string())
            else:
                with smtplib.SMTP(host, port, timeout=20) as server:
                    server.starttls()
                    server.login(user, password)
                    server.sendmail(user, self.recipient_email, msg.as_string())
            logger.info("Email successfully delivered via SMTP.")
            return True
        except Exception as e:
            logger.error(f"Error sending via SMTP: {e}")
            return False
