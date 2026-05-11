"""Integration tests for ControlMappingAgent and GRCOrchestrator."""
from __future__ import annotations

import pytest
from tests.conftest import needs_llm


@needs_llm
def test_map_control_returns_valid_output():
    from agents.control_mapping_agent import ControlMappingAgent
    from core.models import ControlMappingInput

    inp = ControlMappingInput(
        control_id="A.8.2",
        framework_source="ISO_27001_2022",
        target_frameworks=["SOC2_TSC", "NIST_CSF_2"],
        current_ccf_text=(
            "Information shall be classified according to legal requirements, "
            "value, criticality, and sensitivity to unauthorised disclosure or modification."
        ),
    )
    result = ControlMappingAgent().map_control(inp)

    assert result.control_id == "A.8.2"
    assert isinstance(result.mappings, dict)
    assert isinstance(result.gaps, list)
    assert isinstance(result.drift_alerts, list)
    assert isinstance(result.oscal_fragment, dict)


@needs_llm
def test_map_control_target_frameworks_covered():
    from agents.control_mapping_agent import ControlMappingAgent
    from core.models import ControlMappingInput

    inp = ControlMappingInput(
        control_id="A.5.1",
        framework_source="ISO_27001_2022",
        target_frameworks=["SOC2_TSC"],
        current_ccf_text="Policies for information security shall be defined and approved.",
    )
    result = ControlMappingAgent().map_control(inp)
    # At minimum the agent should produce some mapping output or gap explanation
    assert result.control_id == "A.5.1"
    assert isinstance(result.mappings, dict) or isinstance(result.gaps, list)


@needs_llm
def test_orchestrator_classifies_control_mapping():
    from core.orchestrator import GRCOrchestrator

    key = GRCOrchestrator().classify("Map ISO 27001 control A.8.2 to SOC 2 and NIST CSF")
    assert key == "control_mapping"


@needs_llm
def test_orchestrator_classifies_evidence_review():
    from core.orchestrator import GRCOrchestrator

    key = GRCOrchestrator().classify("Review this evidence artifact for SOC 2 completeness")
    assert key == "evidence_review"


@needs_llm
def test_orchestrator_classifies_tprm():
    from core.orchestrator import GRCOrchestrator

    key = GRCOrchestrator().classify("Triage this new AI vendor that processes employee PII")
    assert key == "tprm_triage"


@needs_llm
def test_orchestrator_unknown_task_falls_back():
    from core.orchestrator import GRCOrchestrator
    from core.orchestrator import AGENT_KEYS

    key = GRCOrchestrator().classify("xyzzy frobnicate the compliance widget")
    assert key in AGENT_KEYS  # always returns a valid key


def test_path_traversal_blocked():
    """Verify the tool handler rejects filenames with path components."""
    from agents.control_mapping_agent import ControlMappingAgent

    agent = ControlMappingAgent.__new__(ControlMappingAgent)
    from pathlib import Path
    import os
    agent.frameworks_path = Path(os.getenv("KNOWLEDGE_PATH", "./knowledge")) / "frameworks"

    result = agent._handle_tool_call("read_framework_file", {"framework_name": "../../.env"})
    assert "[Agent Error]" in result or "Invalid filename" in result or "Access denied" in result


def test_path_traversal_absolute_path_blocked():
    """Absolute paths should also be rejected."""
    from agents.control_mapping_agent import ControlMappingAgent
    from pathlib import Path
    import os

    agent = ControlMappingAgent.__new__(ControlMappingAgent)
    agent.frameworks_path = Path(os.getenv("KNOWLEDGE_PATH", "./knowledge")) / "frameworks"

    result = agent._handle_tool_call("read_framework_file", {"framework_name": "/etc/passwd"})
    assert "Invalid filename" in result or "Access denied" in result


def test_path_traversal_hidden_file_blocked():
    """Filenames starting with '.' should be rejected."""
    from agents.control_mapping_agent import ControlMappingAgent
    from pathlib import Path
    import os

    agent = ControlMappingAgent.__new__(ControlMappingAgent)
    agent.frameworks_path = Path(os.getenv("KNOWLEDGE_PATH", "./knowledge")) / "frameworks"

    result = agent._handle_tool_call("read_framework_file", {"framework_name": ".env"})
    assert "Invalid filename" in result
