#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

uv run \
  --with sphinx \
  --with sphinx-rtd-theme \
  --with "myst-parser>=3.0" \
  --with sphinx-copybutton \
  --with "sphinx-design>=0.6" \
  sphinx-build -b html docs docs/_build/html
