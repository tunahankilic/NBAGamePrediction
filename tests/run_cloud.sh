#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_PARENT_DIR="$(dirname "$SCRIPT_DIR")"
INTEGRATION_TEST_FILE="$PROJECT_PARENT_DIR/tests/integration-test.py"
SCRIPT_NAME="run_cloud.sh"

cd "$(dirname "$0")"

export BUCKET_NAME="nba-predictions"
export OUTPUT_FILE_PATTERN="s3://${BUCKET_NAME}/out/nba-{season}-season-predictions.parquet"
export S3_ENDPOINT_URL="http://localhost:4566/"

# Make the file executable
chmod +x $SCRIPT_NAME

# Getting localstack up
docker-compose up -d

sleep 1

# creating bucket
aws s3 mb s3://${BUCKET_NAME} --endpoint-url ${S3_ENDPOINT_URL}

# Change directory to the parent project folder (where pipenv is used)
cd $PROJECT_PARENT_DIR

# Run the integration test file using pipenv with the provided argument
pipenv run python tests/integration-test.py 2023

RESULT=$?

if [ $RESULT -eq 0 ]; then
  echo INTEGRATION TEST SUCCESSFUL
else
  echo INTEGRATION TEST FAILED
fi

docker-compose -f tests/docker-compose.yaml down

#TO RUN: ./tests/run_cloud.sh
