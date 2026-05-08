from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from agents.base_agent import BaseAgent
from core.models import ControlMappingInput, ControlMappingOutput

SYSTEM_PROMPT = """You are a GRC engineer specializing in control framework mapping.
You have deep expertise in ISO 27001:2022, SOC 2 Trust Services Criteria, NIST CSF 2.0, and ISO 42001.

Your responsibilities:
1. Map controls across frameworks using exact cross-reference identifiers
2. Produce OSCAL-compliant JSON fragments for each mapping
3. Identify gaps where no clean cross-framework mapping exists
4. Detect drift when the local CCF text diverges from the current framework source document
5. Return structured JSON matching the ControlMappingOutput schema

Output format — respond with valid JSON only (no markdown fences):
{
  "control_id": "...",
  "mappings": {"SOC2_TSC": "CC6.1", "NIST_CSF_2": "PR.AC-1"},
  "gaps": ["explanation of any gap"],
  "drift_alerts": ["description of any drift detected"],
  "oscal_fragment": { ... OSCAL component-definition fragment ... }
}"""

# Tool: read a framework source file from knowledge/frameworks/
READ_FRAMEWORK_TOOL = {
    "name": "read_framework_file",
    "description": (
        "Read a framework source document from the local knowledge base to check "
        "for drift against the current CCF entry. Use the framework short name as the filename."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "framework_name": {
                "type": "string",
                "description": "Framework filename, e.g. 'ISO_27001_2022.txt' or 'SOC2_TSC.md'",
            }
        },
        "required": ["framework_name"],
    },
}


class ControlMappingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=SYSTEM_PROMPT, tools=[READ_FRAMEWORK_TOOL])
        self.frameworks_path = Path(
            os.getenv("KNOWLEDGE_PATH", "./knowledge")
        ) / "frameworks"

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "read_framework_file":
            filename = tool_input.get("framework_name", "")
            file_path = self.frameworks_path / filename
            if file_path.exists():
                return file_path.read_text(encoding="utf-8", errors="replace")[:8000]
            return f"File not found: {filename}. Available: {list(self.frameworks_path.glob('*'))}"
        return super()._handle_tool_call(tool_name, tool_input)

    def map_control(self, inp: ControlMappingInput) -> ControlMappingOutput:
        prompt = (
            f"Map this control across frameworks.\n\n"
            f"Control ID: {inp.control_id}\n"
            f"Source Framework: {inp.framework_source}\n"
            f"Target Frameworks: {', '.join(inp.target_frameworks)}\n"
            f"Current CCF Text:\n{inp.current_ccf_text}\n\n"
            "Use the read_framework_file tool to check for drift if needed. "
            "Return valid JSON matching the ControlMappingOutput schema."
        )
        raw = self.run_with_tools(prompt)
        try:
            data = json.loads(raw)
            return ControlMappingOutput(**data)
        except Exception:
            return ControlMappingOutput(
                control_id=inp.control_id,
                mappings={},
                gaps=["Failed to parse agent output"],
                drift_alerts=[],
                oscal_fragment={"error": raw[:500]},
            )

    def save_output(self, output: ControlMappingOutput, output_dir: str = "./outputs") -> str:
        today = date.today().strftime("%Y%m%d")
        filename = f"control_mapping_{today}.json"
        path = Path(output_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output.model_dump_json(indent=2))
        return str(path)
