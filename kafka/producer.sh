#!/bin/bash

# Simple wrapper for (docked) message producing to kafka

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
MESSAGE_FILE=/dev/stdin
TOPIC="${KAFKA_TOPIC:-$(whoami)-test}"

usage() {
  echo 'Usage: consumer [OPTIONS]'
  echo ''
  echo 'OPTIONS:'
  echo ''
  echo '-b, --brokers,'
  echo '--bootstrap-server   The kafka broker list to initially use to identify the cluster.'
  echo '                     You can also use the $KAFKA_BROKERS var.'
  echo ''
  echo '-f                   The file to read; should contain one message per line. Defaults to stdin'
  echo ''
  echo '-t, --topic TOPIC    The kafka topic to spaff; you can also use the $KAFKA_TOPIC env var'
  echo "                     If neither is set, defaults to $(whoami)-test"
}

while [[ "$1" != '' ]]; do
  case "$1" in
    -b|--brokers|--bootstrap-server)
      shift
      BROKERS="$1"
      shift
      ;;
    -f)
      shift
      MESSAGE_FILE="$1"
      shift
      ;;
    -t|--topic)
      shift
      TOPIC="$1"
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
      echo "Unexpected argument $1" >&2
      exit 2
      ;;
  esac
done

if [[ -f "$MESSAGE_FILE" ]]; then
  echo "${YELLOW}Submitting $(wc -l $MESSAGE_FILE | sed -E 's/[^0-9]//g') messages to $TOPIC at $BROKERS...$RESET"
else
  echo "${YELLOW}Submitting messages from $MESSAGE_FILE to $TOPIC at $BROKERS...$RESET"
fi

cat "$MESSAGE_FILE" | docker run -i --rm --entrypoint kafka-console-producer.sh --net host $IMAGE \
  --topic "$TOPIC" \
  --broker-list "$BROKERS"

echo ''
