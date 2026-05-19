#!/usr/bin/env bash
# Launches the SeeWeeS Streamlit frontend and opens the browser automatically.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting SeeWeeS Ops Command Center..."

# Install streamlit if missing
if ! python3 -m streamlit --version &>/dev/null 2>&1; then
  echo "Installing streamlit..."
  pip3 install "streamlit>=1.35.0"
fi

exec python3 -m streamlit run src/app.py \
  --server.port 8501 \
  --server.headless false \
  --browser.gatherUsageStats false
