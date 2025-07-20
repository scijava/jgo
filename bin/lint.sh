#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

exitCode=0

# Check for errors and capture non-zero exit codes.
uv run validate-pyproject pyproject.toml
code=$?; test $code -eq 0 || exitCode=$code
uv run ruff check >/dev/null 2>&1
code=$?; test $code -eq 0 || exitCode=$code
uv run ruff format --check >/dev/null 2>&1
code=$?; test $code -eq 0 || exitCode=$code

# Do actual code reformatting.
uv run ruff check --fix
code=$?; test $code -eq 0 || exitCode=$code
uv run ruff format
code=$?; test $code -eq 0 || exitCode=$code

exit $exitCode
