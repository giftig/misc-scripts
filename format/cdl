#!/bin/bash

CARDINAL_IMAGE="${CARDINAL_IMAGE:-giftig/cardinal:latest}"

if [[ "$1" == '' ]]; then
  cat /dev/stdin | docker run -i -e TERM --rm "$CARDINAL_IMAGE"
else
  docker run -i --rm giftig/cardinal:latest "$@"
fi
