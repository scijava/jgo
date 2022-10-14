#!/bin/sh

case "$CONDA_PREFIX" in
  */jgo-dev)
    ;;
  *)
    echo "Please run 'make setup' and then 'mamba activate jgo-dev' first."
    exit 1
    ;;
esac
