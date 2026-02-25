#!/bin/bash
# Quick start script for Grading Bot Streamlit app

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Navigate to the py directory (parent of gradingBot)
PY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PY_DIR"
export PYTHONPATH="$PY_DIR:$PYTHONPATH"
streamlit run gradingBot/gui_web.py

