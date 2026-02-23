#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

uv build
