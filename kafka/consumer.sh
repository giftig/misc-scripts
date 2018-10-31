#!/bin/bash

# Simple wrapper for (docked) message consumption from kafka

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
OFFSET="${KAFKA_OFFSET:-earliest}"
ISOLATION_LEVEL="${KAFKA_ISOLATION_LEVEL:-read_committed}"
FROM_BEGINNING_FLAG=''

TOPIC="${1:-${KAFKA_TOPIC:-$(whoami)-test}}"

usage() {
  echo 'Usage: consumer [OPTIONS]'
  echo ''
  echo 'OPTIONS:'
  echo ''
  echo '-b, --brokers,'
  echo '--bootstrap-server   The kafka broker list to initially use to identify the cluster.'
  echo '                     You can also use the $KAFKA_BROKERS var.'
  echo ''
  echo '--from-beginning     Pass the "from beginning" flag through to the console consumer'
  echo ''
  echo '-g, --group,         The consumer group ID to use to consume'
  echo '--consumer-group'
  echo ''
  echo '--isolation          read_committed or read_uncommitted. Defaults to the former.'
  echo '                     See kafka docs. You can also use the $ISOLATION_LEVEL var.'
  echo ''
  echo '-o, --offset         The kafka offset to use if none exists for the consumer group.'
  echo '                     Defaults to earliest'
  echo ''
  echo '-t, --topic TOPIC    The kafka topic to spaff; you can also use the $KAFKA_TOPIC env var'
  echo "                     If neither is set, defaults to $(whoami)-test"
}

# Parse args
while [[ "$1" != '' ]]; do
  case "$1" in
    -b|--brokers|--bootstrap-server)
      shift
      BROKERS="$1"
      shift
      ;;
    --from-beginning)
      shift
      FROM_BEGINNING_FLAG='--from-beginning'
      ;;
    -g|--group|--consumer-group)
      shift
      GROUP="$1"
      shift
      ;;
    --isolation)
      shift
      ISOLATION_LEVEL="$1"
      shift
      ;;
    -o|--offset)
      shift
      OFFSET="$1"
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


echo "${YELLOW}Reading from $TOPIC at $BROKERS...$RESET"

docker run --rm --entrypoint kafka-console-consumer.sh --net host $IMAGE \
  --topic "$TOPIC" \
  --bootstrap-server "$BROKERS" \
  --group "${GROUP:-"$(whoami)-docked-console-consumer-group"}" \
  $FROM_BEGINNING_FLAG \
  --skip-message-on-error
