from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path


_SAMPLE_EVIDENCE = [
    {
        "artifact_filename": "access_review_jan2025.pdf",
        "control_id": "CC6.1",
        "control_description": "Logical and physical access to resources is restricted to authorized users.",
        "artifact_text": (
            "Quarterly Access Review — Acme Corp — Production Systems\n"
            "Date: 2025-01-15\nSystem: AWS Production Account\n"
            "Reviewed by: Jane Smith, IT Security\n"
            "Finding: All 47 active users verified. 3 terminated accounts removed.\n"
            "Next review: 2025-04-15"
        ),
        "collection_date": (date.today() - timedelta(days=30)).isoformat(),
        "system_name": "AWS Production Account",
    },
    {
        "artifact_filename": "vuln_scan_old.png",
        "control_id": "CC7.1",
        "control_description": "Vulnerabilities are identified and addressed in a timely manner.",
        "artifact_text": (
            "Vulnerability Scan Export\nScanner: Qualys\n"
            "Total findings: 12 Critical, 45 High\nExport date: 2024-06-01"
        ),
        "collection_date": (date.today() - timedelta(days=120)).isoformat(),
        "system_name": "",  # intentionally missing
    },
    {
        "artifact_filename": "backup_test_screenshot.png",
        "control_id": "A.12.3.1",
        "control_description": "Backup copies of information are taken and tested.",
        "artifact_text": "Backup completed successfully. No system name or date visible.",
        "collection_date": (date.today() - timedelta(days=10)).isoformat(),
        "system_name": "Backup System",
    },
]


class DrataMock:
    """Simulates Drata evidence ingestion API responses for local development."""

    def __init__(self, evidence_dir: str | None = None) -> None:
        self.evidence_dir = Path(
            evidence_dir
            or os.path.join(os.getenv("KNOWLEDGE_PATH", "./knowledge"), "evidence_samples")
        )

    def get_evidence_for_control(self, control_id: str) -> list[dict]:
        return [e for e in _SAMPLE_EVIDENCE if e["control_id"] == control_id]

    def get_all_evidence(self) -> list[dict]:
        return list(_SAMPLE_EVIDENCE)

    def get_stale_evidence(self, staleness_days: int = 90) -> list[dict]:
        cutoff = date.today() - timedelta(days=staleness_days)
        result = []
        for e in _SAMPLE_EVIDENCE:
            try:
                if date.fromisoformat(e["collection_date"]) < cutoff:
                    result.append(e)
            except ValueError:
                pass
        return result

    def list_controls(self) -> list[str]:
        return list({e["control_id"] for e in _SAMPLE_EVIDENCE})
