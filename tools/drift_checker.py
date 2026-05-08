from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


class DriftChecker:
    """Compares local CCF entries against framework source documents to detect drift."""

    def __init__(
        self,
        state_path: str | None = None,
        frameworks_dir: str | None = None,
    ) -> None:
        self.state_path = Path(state_path or "./outputs/drift_state.json")
        self.frameworks_dir = Path(
            frameworks_dir or os.path.join(os.getenv("KNOWLEDGE_PATH", "./knowledge"), "frameworks")
        )
        self._state: dict[str, str] = self._load_state()

    def _load_state(self) -> dict[str, str]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self._state, indent=2))

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def check_drift(self) -> list[dict]:
        """Return a list of frameworks whose source files changed since last check."""
        drifted = []
        for fpath in self.frameworks_dir.glob("*"):
            if not fpath.is_file():
                continue
            current_hash = self._hash_file(fpath)
            prior_hash = self._state.get(fpath.name)
            if prior_hash is None:
                status = "new"
            elif prior_hash != current_hash:
                status = "changed"
            else:
                status = "unchanged"

            if status != "unchanged":
                drifted.append({"framework": fpath.name, "status": status})
            self._state[fpath.name] = current_hash

        self._save_state()
        return drifted

    def snapshot(self) -> None:
        """Record current state of all framework files (baseline)."""
        for fpath in self.frameworks_dir.glob("*"):
            if fpath.is_file():
                self._state[fpath.name] = self._hash_file(fpath)
        self._save_state()
