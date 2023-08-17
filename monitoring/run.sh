#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_PARENT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT_NAME="run.sh"

cd "$(dirname "$0")"

# Make the file executable
chmod +x $SCRIPT_NAME

#Getting Evidently up
docker-compose up -d

# Change directory to the parent project folder (where pipenv is used)
cd $PROJECT_PARENT_DIR

# Run the integration test file using pipenv with the provided argument
pipenv run python monitoring/evidently_monitoring.py

#Getting Evidently down
#docker-compose -f monitoring/docker-compose.yaml down
