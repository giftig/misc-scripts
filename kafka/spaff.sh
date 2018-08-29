#!/bin/bash

# Spaff a kafka topic with 10000 (or some other number of) messages

GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

MSG="$1"
NUM="${2:-10000}"
TOPIC="${3:-$KAFKA_TOPIC}"

if [[ "$1" == '' ]]; then
  echo 'Missing message argument' >&2
  exit 1
fi

echo "${YELLOW}Sending $NUM messages to $TOPIC...$RESET"
for i in $(seq 1 "$NUM"); do echo "$MSG"; done | $(dirname $0)/producer.sh /dev/stdin "$TOPIC"
echo "${GREEN}Done!$RESET"
