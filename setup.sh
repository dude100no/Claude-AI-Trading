#!/usr/bin/env bash
set -e

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "ERROR: Python 3 not found." && exit 1
fi

PYTHON=$(command -v python3 || command -v python)

[ ! -d ".venv" ] && $PYTHON -m venv .venv

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
  VENV_PIP=".venv/Scripts/pip.exe"
  VENV_PYTHON=".venv/Scripts/python.exe"
else
  VENV_PIP=".venv/bin/pip"
  VENV_PYTHON=".venv/bin/python"
fi

$VENV_PIP install --upgrade pip --quiet
$VENV_PIP install -r requirements.txt --quiet

[ ! -f "config.json" ] && echo "ERROR: config.json not found." && exit 1

mkdir -p memory
for f in memory/positions.json memory/session_log.jsonl memory/performance.json memory/market_context.md; do
  [ ! -f "$f" ] && touch "$f"
done

$VENV_PYTHON -m pytest tests/ -q 2>&1
