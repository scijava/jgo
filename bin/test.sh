#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

if [ $# -gt 0 ]
then
  uv run python -m pytest -p no:faulthandler $@
else
  uv run python -m pytest -p no:faulthandler tests/
fi
