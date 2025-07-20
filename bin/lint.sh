#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

exitCode=0
uv run validate-pyproject pyproject.toml
code=$?; test $code -eq 0 || exitCode=$code
uv run black src tests
code=$?; test $code -eq 0 || exitCode=$code
uv run isort src tests
code=$?; test $code -eq 0 || exitCode=$code
uv run python -m flake8 src tests
code=$?; test $code -eq 0 || exitCode=$code
exit $exitCode
