#!/usr/bin/env bash

dir=$(dirname "$0")
cd "$dir/.."

# The .t (prysk) tests are collected by the pytest-prysk plugin;
# tests/conftest.py gives them the environment they expect (a per-test
# TMPDIR, COLOR=never, NO_PROGRESS=1, and no JGO_CONFIG_FILE).
# The -p no:faulthandler flag avoids spurious warnings on some platforms.
uv run python -m pytest -v -p no:faulthandler "${@:-tests}"
