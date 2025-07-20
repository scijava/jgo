#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

uv run python -m build
