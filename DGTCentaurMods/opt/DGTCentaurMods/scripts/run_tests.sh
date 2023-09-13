#!/usr/bin/env bash

# Usage: scripts/run_tests.sh
# Runs all unit tests in test/ directory

python -m unittest discover --start-directory test/
