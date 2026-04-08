from __future__ import annotations

import resend

from film_intel_agent.config.settings import get_settings
from film_intel_agent.reports.render import RenderedReport


class EmailSender:
    def __init__(self) -> None:
        self.settings = get_settings()
        resend.api_key = self.settings.resend_api_key

    def send_report(self, report: RenderedReport, dry_run: bool = True) -> dict:
        subject_prefix = "[DRY RUN] " if dry_run else ""
        return resend.Emails.send(
            {
                "from": self.settings.email_from,
                "to": [self.settings.email_to],
                "subject": f"{subject_prefix}Film Intelligence Weekly Report",
                "html": report.html,
                "text": report.text,
            }
        )
