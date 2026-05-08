from __future__ import annotations

import os


class JiraClient:
    """Creates Jira tickets for GRC remediation actions."""

    def __init__(
        self,
        server: str | None = None,
        email: str | None = None,
        token: str | None = None,
        project_key: str = "GRC",
    ) -> None:
        self.server = server or os.getenv("JIRA_SERVER")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.token = token or os.getenv("JIRA_API_TOKEN")
        self.project_key = project_key
        self._jira = None

    def _get_jira(self):
        if self._jira is None:
            try:
                from jira import JIRA
                self._jira = JIRA(
                    server=self.server,
                    basic_auth=(self.email, self.token),
                )
            except ImportError:
                raise RuntimeError("jira not installed. Run: pip install jira")
        return self._jira

    def create_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        labels: list[str] | None = None,
    ) -> str:
        if not all([self.server, self.email, self.token]):
            print(f"[Jira stub] Would create: {summary}")
            return "STUB-0"
        try:
            fields = {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
            if labels:
                fields["labels"] = labels
            issue = self._get_jira().create_issue(fields=fields)
            return issue.key
        except Exception as exc:
            print(f"[Jira error] {exc}")
            return ""

    def create_evidence_remediation(self, control_id: str, recommendation: str) -> str:
        return self.create_ticket(
            summary=f"Evidence remediation required — {control_id}",
            description=recommendation,
            labels=["evidence", "compliance", control_id],
            priority="High",
        )

    def create_vendor_review(self, vendor_name: str, tier: str, next_steps: list[str]) -> str:
        desc = f"Vendor: {vendor_name}\nRisk Tier: {tier}\n\nNext Steps:\n" + "\n".join(
            f"- {s}" for s in next_steps
        )
        return self.create_ticket(
            summary=f"TPRM review — {vendor_name} ({tier})",
            description=desc,
            labels=["tprm", tier.lower(), vendor_name.lower().replace(" ", "-")],
            priority="High" if tier in ("Critical", "High") else "Medium",
        )
