# Security Policy

## Supported Versions

`grc-engineered` is currently in active development. Security fixes are applied to the latest release only.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x (latest) | :white_check_mark: |
| < 0.1.x | :x: |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Use one of the following channels:

- **GitHub Private Advisory (preferred):** [Report a vulnerability](https://github.com/cyberzeshan/grc-engineered/security/advisories/new) — keeps the disclosure private until a fix is released.
- **Email:** Contact the maintainer directly via the email listed on the [GitHub profile](https://github.com/cyberzeshan).

### What to include

To help us triage and fix the issue quickly, please include:

- A clear description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept code or reproduction steps)
- The affected file(s) and version(s)
- Any suggested mitigations, if you have them

### Response timeline

| Milestone | Target |
| --------- | ------ |
| Acknowledgement | Within 48 hours |
| Initial triage & severity assessment | Within 5 business days |
| Fix published (for confirmed vulnerabilities) | Within 30 days for critical/high; 90 days for medium/low |
| Public disclosure | Coordinated with reporter after fix is released |

We follow a **coordinated disclosure** model. We ask that you give us reasonable time to release a fix before making any details public.

## Security Scope

This project is an AI-powered GRC automation platform. The following areas are in scope for security reports:

### In scope

- **Prompt injection** — malicious input in artifact text, vendor names, or policy content that manipulates LLM behavior
- **Path traversal** — exploiting file-read tools (e.g., `read_framework_file`) to read files outside the intended `knowledge/` directory
- **Credential exposure** — API keys, tokens, or secrets leaking through logs, outputs, or error messages
- **Dependency vulnerabilities** — known CVEs in pinned dependencies (`uv.lock`) that have a credible exploit path in this application
- **SQLite injection** — any SQL injection vector in `core/memory.py` session or run-log queries
- **Insecure defaults** — configurations that expose the application or its data unnecessarily

### Out of scope

- Vulnerabilities in the underlying LLM models themselves (Anthropic Claude, Ollama) — report these to the respective vendors
- Issues requiring physical access to the machine running the application
- Social engineering attacks
- Findings from automated scanners with no demonstrated exploit path
- Rate limiting or denial-of-service against the Streamlit UI in a local development context

## Security Design Notes

For contributors and auditors, the following security controls are built into the codebase:

- **Path traversal prevention:** `ControlMappingAgent` uses `Path.is_relative_to()` (Python 3.9+) to ensure file reads stay within `knowledge/frameworks/`
- **Prompt injection mitigation:** User-controlled metadata fields (filenames, control IDs, system names) are sanitized to strip embedded newlines before being interpolated into LLM prompts; artifact body content is wrapped in `<artifact>` tags and treated as untrusted in the system prompt
- **Parameterised SQLite queries:** All database operations use `?` placeholders — no string interpolation in SQL
- **Secrets via environment variables:** API keys and tokens are loaded exclusively from `.env` / environment variables; the `.env` file is `.gitignore`d
- **LLM output validation:** All agent outputs are parsed and validated against Pydantic v2 schemas before use; parse failures return safe fallback values rather than raw model output
