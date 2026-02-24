#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

uv run \
  --with-requirements docs/requirements.txt \
  sphinx-build -b html docs docs/_build/html
