from __future__ import annotations

import re
from datetime import date, datetime, timedelta

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_MONTH_NAMES = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}


class EvidenceScorer:
    """Rule-based pre-scorer for evidence artifacts before sending to the AI agent."""

    STALENESS_DAYS = 90

    def score(
        self,
        artifact_text: str,
        collection_date: str,
        system_name: str,
        control_keywords: list[str] | None = None,
    ) -> dict:
        today = date.today()
        tags: list[str] = []
        deductions = 0

        # Freshness check
        try:
            collected = datetime.fromisoformat(collection_date).date()
            age_days = (today - collected).days
            freshness_pass = age_days <= self.STALENESS_DAYS
            if not freshness_pass:
                tags.append("STALE")
                deductions += 30
        except ValueError:
            freshness_pass = False
            tags.append("INVALID_DATE")
            deductions += 20

        # System name check
        system_name_pass = system_name.lower() in artifact_text.lower()
        if not system_name_pass:
            tags.append("MISSING_SYSTEM_NAME")
            deductions += 25

        # Timestamp in artifact
        has_timestamp = bool(
            _YEAR_RE.search(artifact_text)
            or any(m in artifact_text for m in _MONTH_NAMES)
        )
        if not has_timestamp:
            tags.append("MISSING_TIMESTAMP")
            deductions += 15

        # Keyword relevance
        relevance_pass = True
        if control_keywords:
            hits = sum(1 for kw in control_keywords if kw.lower() in artifact_text.lower())
            if hits == 0:
                tags.append("IRRELEVANT")
                deductions += 40
                relevance_pass = False

        completeness_score = max(0, 100 - deductions)
        return {
            "completeness_score": completeness_score,
            "freshness_pass": freshness_pass,
            "relevance_pass": relevance_pass,
            "tags": tags,
        }
