"""Tests for the Control Mapping Agent."""
import json
import os
import pytest

# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


def test_map_control_returns_output():
    from agents.control_mapping_agent import ControlMappingAgent
    from core.models import ControlMappingInput

    inp = ControlMappingInput(
        control_id="A.8.2",
        framework_source="ISO_27001_2022",
        target_frameworks=["SOC2_TSC", "NIST_CSF_2"],
        current_ccf_text="Information shall be classified according to legal requirements, value, criticality, and sensitivity.",
    )
    agent = ControlMappingAgent()
    result = agent.map_control(inp)

    assert result.control_id == "A.8.2"
    assert isinstance(result.mappings, dict)
    assert isinstance(result.gaps, list)
    assert isinstance(result.drift_alerts, list)
    assert isinstance(result.oscal_fragment, dict)


def test_orchestrator_classifies_control_mapping():
    from core.orchestrator import GRCOrchestrator

    orch = GRCOrchestrator()
    key = orch.classify("Map ISO 27001 control A.8.2 to SOC 2 and NIST CSF")
    assert key == "control_mapping"
