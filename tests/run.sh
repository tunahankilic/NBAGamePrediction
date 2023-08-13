#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

PROJECT_PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Set the path to the integration_test.py file
INTEGRATION_TEST_FILE="$PROJECT_PARENT_DIR/tests/integration-test.py"

# Change directory to the parent project folder (where pipenv is used)
cd "$SCRIPT_DIR/.."


# Run the integration test file using pipenv with the provided argument
pipenv run python "$INTEGRATION_TEST_FILE" "$@"

RESULT=$?

if [ $RESULT -eq 0 ]; then
  echo INTEGRATION TEST SUCCESSFUL
else
  echo INTEGRATION TEST FAILED
fi


#TO RUN: ./tests/run.sh 2023
# Prefect must be running
