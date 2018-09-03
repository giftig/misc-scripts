#!/bin/bash

# Simple wrapper for listing kafka topics with docker

YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)

IMAGE='wurstmeister/kafka:latest'
ZK_HOSTS="${ZK_HOSTS:-localhost:2181}"

usage() {
  echo 'Usage: list-consumer-groups [-z] [ZK_HOSTS]'
  echo ''
  echo 'ZK_HOSTS             The zookeeper hosts list.'
  echo '                     You can also use the $ZK_HOSTS var.'
}

while [[ "$1" != '' ]]; do
  case "$1" in
    -z|--zookeeper)
      shift
      ZK_HOSTS="$1"
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
      ZK_HOSTS="$1"
      shift
      ;;
  esac
done

docker run -i --rm --entrypoint kafka-topics.sh --net host $IMAGE \
  --zookeeper "$ZK_HOSTS" \
  --list
