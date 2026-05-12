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

Seven specialized agents, each with a defined schema and system prompt, handle the most time-consuming work in a GRC program: mapping controls across frameworks, reviewing evidence artifacts, triaging vendors, drafting policies, answering customer questionnaires, classifying AI systems under the EU AI Act, and writing audit narratives. All powered by the Claude API or a local Ollama model — all running on your machine.

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
│   ├── document_loader.py       # PDF/DOCX/Markdown ingestion pipeline
│   ├── providers.py             # LLM provider abstraction (Anthropic + Ollama)
│   └── models.py                # Pydantic schemas for all agent I/O
│
├── agents/
│   ├── base_agent.py            # BaseAgent: provider call, tool use, retry logic
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
├── integrations/
│   ├── slack_notifier.py        # Slack alerts for evidence and vendor events
│   └── jira_client.py           # Jira ticket creation for remediation actions
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
├── tests/                       # Unit + integration test suite
│
├── .env.example                 # Environment variable template
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Installation

### Prerequisites

- **Python 3.11 or newer** — check with `python --version` (or `python3 --version` on Mac/Linux)
- **Git** — check with `git --version`
- **One of:**
  - An [Anthropic API key](https://console.anthropic.com) (paid, recommended for production)
  - [Ollama](https://ollama.com) running locally (free, great for students)

---

### Step 1 — Install uv (one-time setup)

`uv` is a fast Python package manager. Install it once and never think about it again.

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after installing so `uv` is on your PATH.

---

### Step 2 — Clone the repository

```bash
git clone https://github.com/cyberzeshan/grc-engineered.git
cd grc-engineered
```

---

### Step 3 — Configure your environment

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

**macOS / Linux:**
```bash
cp .env.example .env
nano .env
```

Set the minimum required values:

For Anthropic Claude:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

For Ollama (no API key needed — see Step 4 below):
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

---

### Step 4 — (Ollama only) Install and start Ollama

Skip this step if you are using Anthropic Claude.

1. Download and install Ollama from [https://ollama.com](https://ollama.com) — installers for Windows, macOS, and Linux.

2. Start the Ollama service (keep this terminal open):
   ```bash
   ollama serve
   ```

3. Pull a model (do this once):
   ```bash
   ollama pull llama3.2
   ```

**Models with tool-use support** (needed for the Control Mapping agent):

| Model | Size | Notes |
|---|---|---|
| `llama3.2` | ~2 GB | Default, good balance of speed and quality |
| `llama3.1` | ~4 GB | Stronger reasoning |
| `qwen2.5` | ~4 GB | Excellent for structured output |
| `mistral-nemo` | ~7 GB | Strong tool use |

---

### Step 5 — Run the app

This single command installs all dependencies and launches the dashboard:

**macOS / Linux:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

That's it. `uv sync` reads `uv.lock`, creates the virtual environment, installs every dependency at the exact pinned versions, then starts Streamlit — all in one go. You only need to run this once after cloning (or after pulling updates from the repo).

Open `http://localhost:8501` in your browser. Select any agent from the sidebar, fill in the form, and click **Run Agent**.

The sidebar shows which LLM provider is active and warns you if Ollama is unreachable.

---

### Running tests or individual commands

After the first `uv sync`, you can run any command inside the project's virtual environment using `uv run`:

```bash
# Run tests
uv run pytest tests/

# Unit tests only (no API key required)
uv run pytest tests/ -m "not needs_llm"

# Lint
uv run ruff check .
```

Or activate the venv manually and use commands directly:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
pytest tests/
```

**macOS / Linux:**
```bash
source .venv/bin/activate
pytest tests/
```

---

## Environment Variables Reference

All variables are optional unless marked required.

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | | `anthropic` | `anthropic` or `ollama` |
| `ANTHROPIC_API_KEY` | If Anthropic | — | Your API key from console.anthropic.com |
| `ANTHROPIC_MODEL` | | `claude-sonnet-4-6` | Model to use |
| `OLLAMA_BASE_URL` | | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | | `llama3.2` | Model to use with Ollama |
| `SLACK_BOT_TOKEN` | | — | `xoxb-...` token for Slack alerts |
| `SLACK_CHANNEL_ID` | | — | Channel ID (not name) for Slack alerts |
| `JIRA_SERVER` | | — | `https://yourorg.atlassian.net` |
| `JIRA_EMAIL` | | — | Email address for Jira auth |
| `JIRA_API_TOKEN` | | — | Jira API token |
| `CHROMA_DB_PATH` | | `./chroma_db` | Where ChromaDB stores its index |
| `SQLITE_DB_PATH` | | `./memory.db` | Where session memory is stored |
| `KNOWLEDGE_PATH` | | `./knowledge` | Directory of documents to ingest |
| `OUTPUTS_PATH` | | `./outputs` | Where agent outputs are written |

---

## Running Tests

```bash
# Unit tests only (no API key required)
uv run pytest tests/ -m "not needs_llm"

# All tests including live LLM calls (requires API key or Ollama)
uv run pytest tests/

# Verbose output
uv run pytest tests/ -v
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

## Troubleshooting

### `ValueError: ANTHROPIC_API_KEY is not set`

Your `.env` file is missing or the key isn't being loaded. Check the following:

1. Make sure `.env` exists at the project root (not `.env.example`):

   **Windows:** `dir .env`  
   **macOS/Linux:** `ls -la .env`

2. Confirm the key is in the file:

   **Windows (PowerShell):**
   ```powershell
   Get-Content .env | Select-String "ANTHROPIC_API_KEY"
   ```
   **macOS/Linux:**
   ```bash
   grep ANTHROPIC_API_KEY .env
   ```

3. If you want to use Ollama instead (no API key needed), set `LLM_PROVIDER=ollama` in `.env`.

---

### `ModuleNotFoundError` when running any command

The dependencies haven't been synced yet. Run:

```bash
uv sync --system-certs
```

Or just re-run the start script — it calls `uv sync` automatically:

**macOS/Linux:** `./run.sh`  
**Windows:** `run.bat`

If you see `cannot run scripts / execution policy` on Windows, run this first in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Ollama: `[Agent Error] Connection refused` or provider shows as unreachable

Ollama must be running before you start the app.

**Start Ollama:**

- **Windows / macOS:** Open the Ollama desktop app, or run `ollama serve` in a separate terminal.
- **Linux:** `ollama serve` in a separate terminal, or enable the systemd service:
  ```bash
  sudo systemctl enable --now ollama
  ```

Confirm Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

If you changed `OLLAMA_BASE_URL` in `.env`, make sure it matches where Ollama is actually listening.

---

### Ollama: agent returns empty or nonsense output

Not all Ollama models support tool use. Make sure you are using a compatible model:

```bash
ollama pull llama3.2    # recommended default
```

Set it in `.env`:
```env
OLLAMA_MODEL=llama3.2
```

Smaller models like `phi3` or `tinyllama` do not support structured tool calls and will produce unpredictable output.

---

### `[Agent Error] Rate limited — please retry in a moment.`

You have hit the Anthropic API rate limit. Wait 30–60 seconds and retry. If it happens frequently:

- Check your [usage dashboard](https://console.anthropic.com) and consider upgrading your tier.
- Switch to Ollama (`LLM_PROVIDER=ollama`) for unlimited local usage during testing.

---

### Questionnaire Responder returns generic answers with no source references

The vector store is empty — no knowledge documents have been ingested. Add your CCF, policies, or questionnaire templates to the `knowledge/` directory, then run:

```python
from core.vector_store import VectorStore
from core.document_loader import ingest_knowledge_directory

vs = VectorStore()
results = ingest_knowledge_directory(vs)
print(results)   # shows filenames and chunk counts
```

Supported formats: `.txt`, `.md`, `.pdf`, `.docx`.

---

### Agent output shows `"Failed to parse agent output"` or `PARSE_ERROR`

The model returned text that could not be parsed as structured JSON. Common causes:

- The model prefaced its output with a markdown code fence (` ```json `)
- The prompt + context is too large and the output was truncated mid-response

**Fixes:**
- Reduce the size of the input (truncate long policy text or artifact content) and retry.
- If using Ollama, try a larger or more capable model (`llama3.1`, `qwen2.5`).
- If it happens consistently for a specific agent, open an issue with the raw output.

---

### ChromaDB error on first run or after moving the project directory

ChromaDB stores its index at `CHROMA_DB_PATH` (default `./chroma_db`). If the path is broken or the index is corrupt, delete it and re-ingest:

**Windows (PowerShell):**
```powershell
Remove-Item -Recurse -Force .\chroma_db
```

**macOS/Linux:**
```bash
rm -rf ./chroma_db
```

Then re-run the ingestion step (see Questionnaire Responder section above).

---

### Streamlit shows a blank page or fails to start

1. Use the run script from the project root — it handles everything:

   **macOS/Linux:** `./run.sh`  
   **Windows:** `run.bat`

2. If you want to run Streamlit manually, use `uv run` so the venv is automatically used:
   ```bash
   uv run streamlit run ui/app.py
   ```
   Always run from the project root, not from inside `ui/`.

3. If port 8501 is already in use, specify another port:
   ```bash
   uv run streamlit run ui/app.py --server.port 8502
   ```

---

### Slack or Jira integration silently does nothing

Both integrations fail gracefully by printing to console when credentials are missing. Verify your `.env` contains the required keys:

```env
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C0123456789

# Jira
JIRA_SERVER=https://yourorg.atlassian.net
JIRA_EMAIL=you@yourorg.com
JIRA_API_TOKEN=...
```

Quick test for Slack:
```python
from integrations.slack_notifier import SlackNotifier
n = SlackNotifier()
print(n.send("Test message from grc-engineered"))
# True = message sent; False = credentials missing or error
```

For Slack, install the optional integration and re-sync:
```bash
uv sync --extra slack --system-certs
```

For Jira, install the optional integration and re-sync:
```bash
uv sync --extra jira --system-certs
```

---

### Tests are skipped or show `No API key found`

Integration tests require a live API connection. Set credentials in your environment before running:

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
uv run pytest tests/
```

**macOS/Linux:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run pytest tests/
```

To skip live LLM tests and only run unit tests (no API key needed):
```bash
uv run pytest tests/ -m "not needs_llm"
```

---

### Python version error (`requires Python >=3.11`)

Check your Python version:
```bash
python --version
# or on macOS/Linux:
python3 --version
```

If you are on an older version:

- **Windows:** Download Python 3.11+ from [python.org](https://python.org/downloads) and reinstall.
- **macOS:** Use [Homebrew](https://brew.sh): `brew install python@3.11`
- **Ubuntu/Debian:**
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install python3.11 python3.11-venv
  ```

Tell `uv` to use a specific Python version when syncing:
```bash
uv sync --python 3.11 --system-certs
```

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
