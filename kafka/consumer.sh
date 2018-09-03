#!/bin/bash

# Simple wrapper for (docked) message consumption from kafka

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
OFFSET="${KAFKA_OFFSET:-earliest}"
ISOLATION_LEVEL="${KAFKA_ISOLATION_LEVEL:-read_committed}"

TOPIC="${1:-${KAFKA_TOPIC:-$(whoami)-test}}"

echo "${YELLOW}Reading from $TOPIC at $BROKERS...$RESET"

docker run --rm --entrypoint kafka-console-consumer.sh --net host $IMAGE \
  --topic "$TOPIC" \
  --bootstrap-server "$BROKERS" \
  --group "$(whoami)-docked-console-consumer-group" \
  --skip-message-on-error
