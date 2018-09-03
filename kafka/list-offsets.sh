#!/bin/bash
# Simple wrapper for listing kafka offsets with docker

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
GROUP=${1:-${CONSUMER_GROUP:-"$(whoami)-docked-console-consumer-group"}}

usage() {
  echo 'Usage: list-offsets [OPTIONS]'
  echo ''
  echo 'OPTIONS:'
  echo ''
  echo '-b, --brokers,       The kafka broker list to initially use to identify the cluster.'
  echo '--bootstrap-server   You can also use the $KAFKA_BROKERS var.'
  echo ''
  echo '-g, --group,         The consumer group ID for which to check offsets'
  echo '--consumer-group'
  echo ''
  echo '-t, --topic TOPIC    The kafka topic to spaff; you can also use the $KAFKA_TOPIC env var'
  echo "                     If neither is set, defaults to $(whoami)-test"
}

docker run -i --rm --entrypoint kafka-consumer-groups.sh --net host $IMAGE \
  --bootstrap-server "$BROKERS" \
  --offsets \
  --describe \
  --group "$GROUP"

