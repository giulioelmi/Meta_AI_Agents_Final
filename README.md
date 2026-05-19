# MSBA AI Agents Demo

This project is a LangGraph + LangChain multi-agent demo for specialty medicine dispatch planning.

The app:
- reads business rules and KPI definitions from the dispatch playbook PDF
- analyzes shipment data from the CSV file
- checks route weather risk
- runs disruption simulations
- generates an executive PDF report

## Project Structure

```text
data/                  Input PDF and CSV files
src/                   Application code
src/main.py            Main entry point
chroma_db/             Local vector database cache
requirements.txt       Python dependencies
.env.example           Example environment variables
.env                   Local secrets file, not committed
```

## Requirements

Use Python 3.11 or newer. Python 3.13 also works.

You also need:
- an OpenAI API key
- internet access while running the app

The app calls external APIs for OpenAI embeddings, LLM responses, and weather data. If your network blocks those calls, the app may fail during the `PDF Context` or `Weather Risk` step.

## Setup

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you are on Windows, use:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Variables

Create a local `.env` file:

```bash
cp .env.example .env
```

Then open `.env` and set:

```text
OPENAI_API_KEY="your_openai_api_key_here"
```

The email and LangSmith variables in `.env.example` are optional unless you want to use those integrations.

## Run

Make sure the virtual environment is activated, then run:

```bash
python src/main.py --disruption demand_spike
```

Other supported disruption scenarios:

```bash
python src/main.py --disruption driver_shortage --shortage-pct 30
python src/main.py --disruption warehouse_closure --location Boston-MGH
python src/main.py --disruption weather_event --risk-score 2
```

The app prints progress for each pipeline step and writes a PDF report into the folder where you launched the command.

Example output:

```text
SeeWeeS Ops Intelligence
==================================================
  Demand Spike  x1.2

  [1/8] PDF Context             done
  [2/8] CSV Analysis            done
  ...
  Report: /path/to/project/dispatch_report_YYYYMMDD_HHMMSS.pdf
```

## Common Issues

### `zsh: command not found: python`

On some Macs, the command is `python3`, not `python`.

Use this for setup:

```bash
python3 -m venv .venv
```

After activating the virtual environment, `python` should work.

```

### `Error: Missing OpenAI credentials`

The app did not find `OPENAI_API_KEY`.

Check that `.env` exists and contains:

```text
OPENAI_API_KEY="your_openai_api_key_here"
```

### `openai.APIConnectionError: Connection error`

The app could not reach the OpenAI API. Check that:
- you are connected to the internet
- your API key is valid
- your network, VPN, firewall, or classroom Wi-Fi is not blocking external API calls

## Notes for Sharing

Do not share your `.env` file or OpenAI API key.

If you share the project with classmates, they should create their own `.env` file and use their own API key.
