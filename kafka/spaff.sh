#!/bin/bash

# Spaff a kafka topic with 10000 (or some other number of) messages

GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

MSG=''
NUM=10000
TOPIC="${KAFKA_TOPIC:-$(whoami)-test}"

usage() {
  echo 'Usage: spaff [-t TOPIC] [-n NUM] message'
  echo ''
  echo '-t, --topic TOPIC    The kafka topic to spaff; you can also use the $KAFKA_TOPIC env var'
  echo "                     If neither is set, defaults to $(whoami)-test"
  echo ''
  echo '-n --num NUM         The number of messages to jam into the topic. Default is 10000'
}

# Parse args
while [[ "$1" != '' ]]; do
  case "$1" in
    -t|--topic)
      shift
      TOPIC="$1"
      shift
      ;;
    -n|--num)
      shift
      NUM="$1"
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
      if [[ "$MSG" != '' ]]; then
        usage
        exit 2
      fi

      MSG="$1"
      shift
      ;;
  esac
done

# Validate args
if [[ "$MSG" == '' ]]; then
  echo 'Message cannot be empty' >&2
  exit 1
fi
if [[ "$TOPIC" == '' ]]; then
  echo 'Topic cannot be empty' >&2
  exit 1
fi
if ! echo "$NUM" | grep -E '^[1-9][0-9]*$' &> /dev/null; then
  echo 'Number must be a positive integer'
  exit 1
fi

# Do the thing
echo "${YELLOW}Sending $NUM messages to $TOPIC...$RESET"
for i in $(seq 1 "$NUM"); do echo "$MSG"; done |
  $(dirname $0)/producer.sh -t "$TOPIC"
echo "${GREEN}Done!$RESET"
