#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

python -m pytest tests/ -p no:faulthandler $@
