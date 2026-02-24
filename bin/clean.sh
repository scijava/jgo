#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

find . -name __pycache__ -type d | while read d
  do rm -rfv "$d"
done
rm -rfv \
  .cache \
  .mypy_cache \
  .pytest_cache \
  .ruff_cache \
  build \
  dist \
  docs/_build \
  src/*.egg-info
