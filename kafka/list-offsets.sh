#!/bin/bash
# Simple wrapper for listing kafka offsets with docker

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
GROUP=${1:-${CONSUMER_GROUP:-"$(whoami)-docked-console-consumer-group"}}

docker run -i --rm --entrypoint kafka-consumer-groups.sh --net host $IMAGE \
  --bootstrap-server "$BROKERS" \
  --offsets \
  --describe \
  --group "$GROUP"

