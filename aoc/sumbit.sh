#!/bin/bash

# Script to submit Advent of Code answers
# Usage: ./submit_aoc_answer.sh YEAR DAY LEVEL ANSWER

set -a # automatically export all variables
source .env
set +a

# Validate that the session cookie is set
if [ -z "$SESSION_COOKIE" ]; then
    echo "Error: Session cookie is not set. Please update the script with your session cookie."
    exit 1
fi

set -e
set -x

if [ -z "$4" ]
then
    YEAR=$(date '+%Y')
else
    YEAR="$4"
fi
if [ -z "$3" ]
then
    DAY=$(TZ=':US/Eastern' date '+%-d')
else
    DAY="$3"
fi

# The URL for the POST request
URL="https://adventofcode.com/${YEAR}/day/${DAY}/answer"
LEVEL="$1"
ANSWER="$2"
echo "$LEVEL $ANSWER"
read
# Perform the POST request
response=$(curl --trace-ascii - -v -X POST "$URL" \
    -H "Cookie: session=$SESSION_COOKIE" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "level=${LEVEL}" \
    --data-urlencode "answer=${ANSWER}")


response=${response#*<main>}
response=${response%</main>*}
echo "$response"

