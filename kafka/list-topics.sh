#!/bin/bash

# Simple wrapper for listing kafka topics with docker

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
ZK_HOSTS="${ZK_HOSTS:-localhost:2181}"
MESSAGE_FILE="${1:-/dev/stdin}"
TOPIC="${2:-${KAFKA_TOPIC:-giftig-test}}"

docker run -i --rm --entrypoint kafka-topics.sh --net host $IMAGE \
  --zookeeper "$ZK_HOSTS" \
  --list
