"""Unit tests for tools/drift_checker.py — uses temporary files, no LLM."""
from __future__ import annotations

import pytest
from tools.drift_checker import DriftChecker


@pytest.fixture
def frameworks_dir(tmp_path):
    d = tmp_path / "frameworks"
    d.mkdir()
    return d


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "drift_state.json"


@pytest.fixture
def checker(frameworks_dir, state_path):
    return DriftChecker(
        state_path=str(state_path),
        frameworks_dir=str(frameworks_dir),
    )


def test_new_file_detected_as_new(checker, frameworks_dir):
    (frameworks_dir / "ISO_27001_2022.txt").write_text("ISO content", encoding="utf-8")
    drifted = checker.check_drift()
    names = [d["framework"] for d in drifted]
    assert "ISO_27001_2022.txt" in names
    statuses = {d["framework"]: d["status"] for d in drifted}
    assert statuses["ISO_27001_2022.txt"] == "new"


def test_unchanged_file_not_in_drifted(checker, frameworks_dir):
    f = frameworks_dir / "SOC2_TSC.txt"
    f.write_text("SOC 2 Trust Services Criteria", encoding="utf-8")
    checker.check_drift()  # first run — establishes baseline

    drifted = checker.check_drift()  # second run — no changes
    names = [d["framework"] for d in drifted]
    assert "SOC2_TSC.txt" not in names


def test_modified_file_detected_as_changed(checker, frameworks_dir):
    f = frameworks_dir / "NIST_CSF.txt"
    f.write_text("Original NIST CSF content", encoding="utf-8")
    checker.check_drift()  # establish baseline

    f.write_text("Updated NIST CSF content — v2.0 additions", encoding="utf-8")
    drifted = checker.check_drift()

    statuses = {d["framework"]: d["status"] for d in drifted}
    assert statuses.get("NIST_CSF.txt") == "changed"


def test_multiple_files_checked_together(checker, frameworks_dir):
    (frameworks_dir / "ISO_27001.txt").write_text("ISO content", encoding="utf-8")
    (frameworks_dir / "SOC2.txt").write_text("SOC 2 content", encoding="utf-8")
    checker.check_drift()  # baseline

    # Modify only one
    (frameworks_dir / "ISO_27001.txt").write_text("Updated ISO content", encoding="utf-8")
    drifted = checker.check_drift()

    statuses = {d["framework"]: d["status"] for d in drifted}
    assert statuses.get("ISO_27001.txt") == "changed"
    assert "SOC2.txt" not in statuses  # unchanged


def test_snapshot_persists_state(checker, frameworks_dir, state_path):
    (frameworks_dir / "framework.txt").write_text("Framework content", encoding="utf-8")
    checker.snapshot()
    assert state_path.exists()

    import json
    state = json.loads(state_path.read_text())
    assert "framework.txt" in state
    assert len(state["framework.txt"]) == 64  # SHA256 hex length


def test_empty_frameworks_dir_returns_no_drift(checker):
    drifted = checker.check_drift()
    assert drifted == []


def test_directories_inside_frameworks_are_ignored(checker, frameworks_dir):
    subdir = frameworks_dir / "subdir"
    subdir.mkdir()
    drifted = checker.check_drift()
    names = [d["framework"] for d in drifted]
    assert "subdir" not in names


def test_state_persists_between_checker_instances(frameworks_dir, state_path):
    f = frameworks_dir / "framework.txt"
    f.write_text("Initial content", encoding="utf-8")

    checker1 = DriftChecker(str(state_path), str(frameworks_dir))
    checker1.check_drift()  # baseline

    # New checker instance, same state file
    checker2 = DriftChecker(str(state_path), str(frameworks_dir))
    drifted = checker2.check_drift()  # should see no changes
    assert not any(d["status"] == "changed" for d in drifted)
