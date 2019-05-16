#!/bin/bash

# Simple wrapper for (docked) message producing to kafka

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
BROKERS="${KAFKA_BROKERS:-localhost:9092}"
MESSAGE_FILE=/dev/stdin
TOPIC="${KAFKA_TOPIC:-$(whoami)-test}"
ACK_ALL=0

usage() {
  echo 'Usage: producer [OPTIONS]'
  echo ''
  echo 'OPTIONS:'
  echo ''
  echo '-a, --ack-all        Require acknowledgements from multiple nodes'
  echo '                     (equal to min.insync.replicas in broker settings)'
  echo ''
  echo '-b, --brokers,'
  echo '--bootstrap-server   The kafka broker list to initially use to identify'
  echo '                     the cluster.'
  echo '                     You can also use the $KAFKA_BROKERS var.'
  echo ''
  echo '-f                   The file to read; should contain one message per '
  echo '                     line. Defaults to stdin'
  echo ''
  echo '-t, --topic TOPIC    The kafka topic to write to; you can also use the '
  echo '                     $KAFKA_TOPIC env var.'
  echo "                     If neither is set, defaults to $(whoami)-test"
}

while [[ "$1" != '' ]]; do
  case "$1" in
    -a|--ack-all)
      shift
      ACK_ALL=1
      ;;
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

EXTRA_PROPS=''
if [[ "$ACK_ALL" == 1 ]]; then
  EXTRA_PROPS="$EXTRA_PROPS --producer-property acks=all"
fi

cat "$MESSAGE_FILE" | docker run -i --rm --entrypoint kafka-console-producer.sh --net host $IMAGE \
  --topic "$TOPIC" \
  --broker-list "$BROKERS" \
  $EXTRA_PROPS

echo ''
