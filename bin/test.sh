#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

if [ $# -gt 0 ]
then
  python -m pytest -p no:faulthandler $@
else
  python -m pytest -p no:faulthandler tests/
fi
