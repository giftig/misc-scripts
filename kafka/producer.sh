#!/bin/bash

# Simple wrapper for (docked) message producing to kafka

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
MESSAGE_FILE="${1:-/dev/stdin}"
TOPIC="${2:-${KAFKA_TOPIC:-giftig-test}}"

if [[ -f "$MESSAGE_FILE" ]]; then
  echo "${YELLOW}Submitting $(wc -l $MESSAGE_FILE | sed -E 's/[^0-9]//g') messages to $TOPIC at $BROKERS...$RESET"
else
  echo "${YELLOW}Submitting messages from $MESSAGE_FILE to $TOPIC at $BROKERS...$RESET"
fi

cat "$MESSAGE_FILE" | docker run -i --rm --entrypoint kafka-console-producer.sh --net host $IMAGE \
  --topic "$TOPIC" \
  --broker-list "$BROKERS"

echo ''
