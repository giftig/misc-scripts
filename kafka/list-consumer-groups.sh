#!/bin/bash
# Simple wrapper for listing kafka consumer groups with docker

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"

usage() {
  echo 'Usage: list-consumer-groups [-b] [BROKERS]'
  echo ''
  echo 'BROKERS              The kafka broker list to initially use to identify the cluster.'
  echo '                     You can also use the $KAFKA_BROKERS var.'
}

while [[ "$1" != '' ]]; do
  case "$1" in
    -b|--brokers|--bootstrap-server)
      shift
      BROKERS="$1"
      shift
      ;;
    --help)
      shift
      usage
      exit 0
      ;;
    -*)
      echo "Unrecognised flag $1" >&2
      exit 1
      ;;
    *)
      BROKERS="$1"
      shift
      ;;
  esac
done

docker run --rm --entrypoint kafka-consumer-groups.sh --net host $IMAGE \
  --bootstrap-server "$BROKERS" \
  --list
