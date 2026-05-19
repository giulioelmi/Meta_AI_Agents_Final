# MSBA AI Agents Demo (LangGraph + LangChain)

Multi-agent system for operations/dispatch planning:
- Reads business context & KPI definitions from a PDF (RAG)
- Analyzes ops data from CSV (KPIs + anomaly detection)
- Pulls weather forecast and derives dispatch risk
- Produces a leadership-ready PDF report saved in the current working directory

## Project Structure
- `data/` input PDF + CSV
- `src/` application code
- `chroma_db/` local vector store (not committed)
- `.env` secrets (not committed)

## Run
```bash
python src/main.py --disruption demand_spike
```

The pipeline runs fully in the terminal with step-by-step updates and writes a final PDF report to the directory where you launch the command.

## Troubleshooting
- If you see `openai.OpenAIError: Missing credentials`, your API key is not loaded.
- Ensure `.env` exists and contains:
  - `OPENAI_API_KEY=your_key_here`
- Or export it directly before running:
  - macOS/Linux: `export OPENAI_API_KEY=your_key_here`
  - Windows PowerShell: `$env:OPENAI_API_KEY="your_key_here"`
- If you see repeated LangSmith `403 Forbidden` ingest errors, tracing is misconfigured.
  - By default tracing is now OFF.
  - Only enable tracing when you explicitly set:
    - `ENABLE_LANGSMITH=true`
    - `LANGSMITH_API_KEY=...`
    - `LANGCHAIN_PROJECT=MSBA_AI_Agents_Demo` (or your project name)

## Setup
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
windows: python -m pip install -r requirements.txt

cp .env.example .env
# fill OPENAI_API_KEY
windows: python src/main.py
```
