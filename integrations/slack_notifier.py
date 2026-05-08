from __future__ import annotations

import os


class SlackNotifier:
    """Sends GRC alerts and summaries to a Slack channel."""

    def __init__(
        self,
        token: str | None = None,
        channel_id: str | None = None,
    ) -> None:
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.channel_id = channel_id or os.getenv("SLACK_CHANNEL_ID")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from slack_sdk import WebClient
                self._client = WebClient(token=self.token)
            except ImportError:
                raise RuntimeError("slack-sdk not installed. Run: pip install slack-sdk")
        return self._client

    def send(self, message: str, title: str | None = None) -> bool:
        if not self.token or not self.channel_id:
            print(f"[Slack stub] {title or 'GRC Alert'}: {message[:100]}")
            return False
        try:
            blocks = []
            if title:
                blocks.append({"type": "header", "text": {"type": "plain_text", "text": title}})
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": message}})
            self._get_client().chat_postMessage(channel=self.channel_id, blocks=blocks)
            return True
        except Exception as exc:
            print(f"[Slack error] {exc}")
            return False

    def send_evidence_alert(self, control_id: str, tags: list[str], filename: str) -> bool:
        msg = f"*Evidence Alert — {control_id}*\nFile: `{filename}`\nIssues: {', '.join(tags)}"
        return self.send(msg, title="Evidence Quality Alert")

    def send_vendor_alert(self, vendor_name: str, tier: str, ai_flag: bool) -> bool:
        flag = " 🤖 AI vendor flagged" if ai_flag else ""
        msg = f"*New Vendor Triaged:* {vendor_name}\nRisk Tier: *{tier}*{flag}"
        return self.send(msg, title="TPRM Triage Complete")
