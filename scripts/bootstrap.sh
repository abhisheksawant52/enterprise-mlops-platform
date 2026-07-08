#!/usr/bin/env bash
#
# Bootstrap a local development environment for the Enterprise MLOps Platform.
# Creates a virtualenv, installs the package with dev extras, and wires up
# pre-commit hooks. Safe to re-run.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

echo "==> Creating virtualenv in ${VENV_DIR}"
"$PYTHON" -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "==> Installing package with dev dependencies"
python -m pip install --upgrade pip
pip install -e ".[dev]"

echo "==> Installing pre-commit hooks"
pre-commit install || echo "pre-commit not available; skipping"

if [ ! -f .env ]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
fi

echo "==> Bootstrap complete. Activate with: source ${VENV_DIR}/bin/activate"
