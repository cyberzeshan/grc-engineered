#!/usr/bin/env bash
set -e

# Sync all dependencies from uv.lock (creates .venv if it doesn't exist)
uv sync --system-certs

# Launch the Streamlit dashboard inside the project venv
uv run streamlit run ui/app.py
