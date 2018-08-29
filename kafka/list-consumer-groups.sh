#!/bin/bash
# Simple wrapper for listing kafka consumer groups with docker

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"

docker run -i --rm --entrypoint kafka-consumer-groups.sh --net host $IMAGE \
  --bootstrap-server "$BROKERS" \
  --list
