#!/usr/bin/env bash

dir=$(dirname "$0")
cd "$dir/.."

# COLOR/NO_PROGRESS defaults keep prysk (.t) test output clean of ANSI codes
# and progress bars. Individual tests can override (e.g. color.t sets its own
# COLOR). The -p no:faulthandler flag avoids spurious warnings on some platforms.
COLOR="${COLOR:-never}" NO_PROGRESS="${NO_PROGRESS:-1}" \
  uv run python -m pytest -v -p no:faulthandler "${@:-tests}"
