# ⚙️ grc-engineered

> **GRC automation built the way software should be — structured, versioned, and agent-driven.**  
> Seven AI agents. One shared knowledge base. Zero manual copy-paste.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Claude API](https://img.shields.io/badge/Claude-API-D97706?style=flat)](https://anthropic.com)
[![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-FF6B35?style=flat)](https://trychroma.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=flat)](LICENSE)

---

## What is this?

**grc-engineered** is a multi-agent GRC automation platform that treats compliance as a software problem — not a spreadsheet problem.

Seven specialized agents, each with a defined schema and system prompt, handle the most time-consuming work in a GRC program: mapping controls across frameworks, reviewing evidence artifacts, triaging vendors, drafting policies, answering customer questionnaires, classifying AI systems under the EU AI Act, and writing audit narratives. All powered by the Claude API, all running locally.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Claude Orchestrator                   │
│               routes tasks · manages state               │
└──────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │
  ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
  │Control │ │Evidence│ │Quest.  │ │Policy  │
  │Mapping │ │Reviewer│ │Respond.│ │Drafter │
  └────────┘ └────────┘ └────────┘ └────────┘
  ┌────────┐ ┌────────┐ ┌────────┐
  │ TPRM   │ │   AI   │ │ Audit  │
  │Triage  │ │Registry│ │Narrat. │
  └────────┘ └────────┘ └────────┘
       │          │          │
┌──────▼──────────▼──────────▼────────────────────────────┐
│                 Shared Knowledge Layer                  │
│   Vector Store · Framework Library · Evidence Store     │
│       ChromaDB · ISO 27001 · SOC 2 · NIST CSF 2.0       │
└─────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Role Scope | What It Does | Key Output |
|-------|-----------|--------------|------------|
| **Control Mapping** | GRC Engineer | Maps controls across ISO 27001, SOC 2, NIST CSF 2.0, ISO 42001; alerts on framework drift | OSCAL JSON fragment |
| **Evidence Reviewer** | GRC Engineer | Scores Drata evidence artifacts for completeness, freshness, and relevance; tags stale evidence | Scored evidence report |
| **Questionnaire Responder** | Head of GRC | Answers Tier-2/3 security questionnaires via RAG over your CCF and policy corpus | Draft answers + source refs |
| **Policy Drafter** | Head of GRC | Drafts policy revisions when a framework or regulation changes; maintains a change log | Revised Markdown + changelog |
| **TPRM Triage** | GRC Engineer | Auto-tiers new vendors; flags AI-class vendors for specialized questionnaire routing | Vendor risk profile |
| **AI Use-Case Registry** | Head of GRC | Drafts AI registry entries from intake forms; applies EU AI Act risk classification | Registry entry Markdown |
| **Audit Narrative** | Head of GRC | Drafts control narratives, auditor responses, and exception memos from real evidence | Audit-ready prose |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Reasoning | [Anthropic Claude](https://anthropic.com) (`claude-sonnet-4-6`) **or** [Ollama](https://ollama.com) (local, free) |
| Package Manager | [uv](https://docs.astral.sh/uv/) — fast Python package manager |
| Vector Store | [ChromaDB](https://trychroma.com) — local, no server needed |
| Document Ingestion | [pypdf](https://pypdf.readthedocs.io) + custom chunking pipeline |
| Data Models | [Pydantic v2](https://docs.pydantic.dev) |
| UI | [Streamlit](https://streamlit.io) |
| Document Output | [python-docx](https://python-docx.readthedocs.io) + [openpyxl](https://openpyxl.readthedocs.io) |
| State / Memory | SQLite (stdlib) |

---

## Project Structure

```
grc-engineered/
├── core/
│   ├── orchestrator.py          # Routes tasks to agents; manages conversation state
│   ├── memory.py                # SQLite-backed agent state
│   ├── vector_store.py          # ChromaDB wrapper: ingest + semantic query
│   ├── document_loader.py       # PDF/DOCX chunking pipeline
│   └── models.py                # Pydantic schemas for all agent I/O
│
├── agents/
│   ├── base_agent.py            # BaseAgent: Claude call, tool use, retry logic
│   ├── control_mapping_agent.py
│   ├── evidence_reviewer_agent.py
│   ├── questionnaire_responder_agent.py
│   ├── policy_drafter_agent.py
│   ├── tprm_triage_agent.py
│   ├── ai_registry_agent.py
│   └── audit_narrative_agent.py
│
├── knowledge/
│   ├── frameworks/              # ISO 27001, SOC 2, NIST CSF 2.0, ISO 42001 source docs
│   ├── policies/                # Policy templates
│   ├── evidence_samples/        # Mock Drata evidence exports
│   └── questionnaires/          # SIG Lite, CAIQ sample questionnaires
│
├── tools/
│   ├── drift_checker.py         # Compares framework versions against CCF
│   ├── evidence_scorer.py       # Freshness + completeness scoring
│   └── vendor_classifier.py     # Tier 1/2/3 and AI-class classification
│
├── outputs/
│   └── examples/                # Sample outputs — no API key needed to view
│       ├── control_mapping_example.json
│       ├── vendor_profile_example.md
│       └── audit_narrative_example.md
│
├── ui/
│   └── app.py                   # Streamlit demo dashboard
│
├── tests/
│   ├── test_control_mapping.py
│   ├── test_evidence_reviewer.py
│   └── test_tprm_triage.py
│
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- **One of:** an [Anthropic API key](https://console.anthropic.com) **or** [Ollama](https://ollama.com) running locally (free)

---

### Option A — Anthropic Claude (recommended for production)

```bash
# Clone the repo
git clone https://github.com/cyberzeshan/grc-engineered.git
cd grc-engineered

# Install uv (fast Python package manager)
pip install uv

# Create a virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Set up environment
cp .env.example .env
nano .env          # add your ANTHROPIC_API_KEY; set LLM_PROVIDER=anthropic
```

---

### Option B — Ollama (free, runs entirely on your machine)

Great for students or anyone without an Anthropic account.

```bash
# 1. Install Ollama from https://ollama.com and start it
ollama serve                    # keep this running in one terminal

# 2. Pull a model (llama3.2 is a good default, ~2 GB)
ollama pull llama3.2

# 3. Clone and install
git clone https://github.com/cyberzeshan/grc-engineered.git
cd grc-engineered
pip install uv
uv venv
uv pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
nano .env          # set LLM_PROVIDER=ollama (no API key needed)
```

**Models with tool-use support** (needed for the Control Mapping agent):

| Model | Size | Notes |
|---|---|---|
| `llama3.2` | ~2 GB | Default, good balance |
| `llama3.1` | ~4 GB | Stronger reasoning |
| `qwen2.5` | ~4 GB | Excellent for structured output |
| `mistral-nemo` | ~7 GB | Strong tool use |

---

### Run the Streamlit UI

```bash
# Activate the virtual environment first
source .venv/bin/activate       # Windows: .venv\Scripts\activate

streamlit run ui/app.py
```

Open `http://localhost:8501` in your browser. Select any agent from the sidebar, fill in the form, and click **Run Agent**.

The sidebar shows which provider is active and warns you if Ollama is not reachable.

---

## Troubleshooting

### `ValueError: ANTHROPIC_API_KEY environment variable is not set.`

If you are using Anthropic, make sure your `.env` file exists and contains your key:

```bash
cp .env.example .env
nano .env   # set ANTHROPIC_API_KEY=sk-ant-...  and  LLM_PROVIDER=anthropic
```

If you want to use Ollama instead (no API key needed):

```bash
nano .env   # set LLM_PROVIDER=ollama
```

Confirm the key loads correctly (Anthropic only):

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ANTHROPIC_API_KEY')[:8])"
```

---

### `[Agent Error] Rate limited — please retry in a moment.`

You've hit the Anthropic API rate limit. Wait 30–60 seconds and try again. If it happens frequently, check your [usage tier](https://console.anthropic.com) and consider upgrading.

---

### Questionnaire Responder returns generic answers with no source references

The vector store is empty — no knowledge documents have been ingested yet. Add your CCF, policies, or questionnaire templates to the `knowledge/` directory, then ingest them:

```python
from core.vector_store import VectorStore
from core.document_loader import ingest_knowledge_directory

vs = VectorStore()
results = ingest_knowledge_directory(vs)
print(results)  # shows filenames and chunk counts
```

Supported formats: `.txt`, `.md`, `.pdf`, `.docx`.

---

### Agent output shows `"Failed to parse agent output"` or `PARSE_ERROR`

The agent returned text that couldn't be parsed as JSON. This can happen when:

- The model prefaced its JSON with a markdown code fence (` ```json `)
- The response was cut off mid-stream (usually means the prompt + context is too large)

**Fix:** Reduce the size of the input (e.g. truncate long policy text or artifact content) and retry. If it happens consistently for a specific agent, open an issue with the raw output.

---

### ChromaDB error on first run or after moving the project directory

ChromaDB stores its index at the path in `CHROMA_DB_PATH` (default `./chroma_db`). If you move the project or the path no longer exists, delete the old index and re-ingest:

```bash
rm -rf ./chroma_db
```

Then re-run the ingestion step above.

---

### Streamlit UI shows a blank page or `ModuleNotFoundError`

Make sure you activated your virtual environment before running Streamlit:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
streamlit run ui/app.py
```

If you see a specific missing module, re-run `pip install -r requirements.txt` — a dependency may not have installed cleanly.

---

### Slack or Jira integration silently does nothing

Both integrations fail gracefully by printing to console when credentials are missing. Check that your `.env` includes the required keys:

```
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0123456789

# Jira
JIRA_SERVER=https://yourorg.atlassian.net
JIRA_EMAIL=you@yourorg.com
JIRA_API_TOKEN=...
```

If the keys are set and it still doesn't work, run a quick test:

```python
from integrations.slack_notifier import SlackNotifier
n = SlackNotifier()
n.send("Test message from grc-engineered")
```

---

### Tests are skipped or show `No API key found`

Integration tests require a live API key. Set it in your environment before running pytest:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # macOS/Linux
$env:ANTHROPIC_API_KEY="sk-ant-..."   # Windows PowerShell

pytest tests/
```

---

## Example Outputs

Browse pre-generated outputs in [`outputs/examples/`](outputs/examples/) — no API key or setup needed.

**Control mapping — ISO 27001 A.8.2 → SOC 2 + NIST CSF 2.0:**
```json
{
  "control_id": "A.8.2",
  "mappings": {
    "SOC2_TSC": { "control_ref": "CC6.1", "confidence": "high" },
    "NIST_CSF_2": { "control_ref": "PR.AA-01", "confidence": "high" }
  },
  "drift_alerts": [],
  "oscal_fragment": { "...": "see full file" }
}
```

**Vendor triage — AI SaaS tool flagged HIGH:**
```
Vendor:     Acme AI Assistant
Risk Tier:  HIGH
AI Flag:    ✓ — route to AI Questionnaire
Next Steps: Send AI questionnaire · Request SOC 2 · Legal DPA review
```

---

## Frameworks Supported

- ISO 27001:2022
- SOC 2 Trust Services Criteria (2017)
- NIST Cybersecurity Framework 2.0
- ISO 42001:2023 (AI Management Systems)
- EU AI Act (risk classification — Articles 5, 6, 50)
- NIST AI RMF 1.0

---

## Roadmap

- [ ] Drata API integration for live evidence ingestion
- [ ] Slack bot interface for Questionnaire Responder
- [ ] Full OSCAL export for the CCF
- [ ] GitHub Actions compliance gate (CI/CD pipeline check)
- [ ] ISO 42001 Annex A control coverage tracker
- [ ] Web-based trust portal for questionnaire responses

---

## About

Built by [Zeshan Ahmad](https://linkedin.com/in/YOUR_LINKEDIN) — GRC Specialist, ISO 27001 & ISO 42001 Lead Auditor, CISA, CISM.

---

## License

MIT — see [LICENSE](LICENSE)
