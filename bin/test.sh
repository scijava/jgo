#!/usr/bin/env bash

dir=$(dirname "$0")
cd "$dir/.."

pytest_args=()
prysk_args=()

if [ $# -eq 0 ]; then
  # No args: run both on tests directory
  pytest_args+=("tests")
  prysk_args+=("tests")
else
  # Partition args: .py and ::* go to pytest, .t to prysk, others to both
  for arg in "$@"; do
    case "$arg" in
      *.py|*::*)
        pytest_args+=("$arg")
        ;;
      *.t)
        prysk_args+=("$arg")
        ;;
      *)
        # Flags or directories - add to both
        pytest_args+=("$arg")
        prysk_args+=("$arg")
        ;;
    esac
  done
fi

# Track overall exit status
exit_status=0

# Run pytest if we have args
if [ ${#pytest_args[@]} -gt 0 ]; then
  uv run python -m pytest -v -p no:faulthandler "${pytest_args[@]}"
  pytest_status=$?
  if [ $pytest_status -ne 0 ]; then
    exit_status=$pytest_status
  fi
fi

# Run prysk if we have args and prysk is installed
if [ ${#prysk_args[@]} -gt 0 ] && command -v prysk; then
  # NB: We cannot add prysk to pyproject.toml because
  # prysk depends on an incompatible version of rich.
  # Use `uv tool install prysk` instead.
  #
  # We set COLOR=never by default to avoid ANSI codes in test output.
  # This is especially important for CI, which may or may not detect
  # as ANSI-color-compatible compared to local usage of prysk.
  # Tests can override this (e.g., color.t does).
  COLOR="${COLOR:-never}" prysk -v "${prysk_args[@]}"
  prysk_status=$?
  if [ $prysk_status -ne 0 ]; then
    exit_status=$prysk_status
  fi
fi

# Exit with appropriate status
exit $exit_status
