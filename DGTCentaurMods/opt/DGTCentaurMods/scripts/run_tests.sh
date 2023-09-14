#!/usr/bin/env bash

# Usage: scripts/run_tests.sh
# Runs all unit tests in test/ directory

export PYTHONPATH=..
python -m unittest discover --start-directory test/
