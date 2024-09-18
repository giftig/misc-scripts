#!/bin/bash

# Quick script to install symlinks for rcfiles in this repo into the correct places
# You'll have to fix any failures yourself, as it won't attempt to overwrite anything
# you already have in place to be on the safe side

DIR=$(readlink -f "$(dirname "$0")")

install_rcfile() {
  f=$(basename "$1")
  echo -n "Installing rcfiles/$f... "
  ln -s "$1" "$HOME/.$f"

  if [[ "$?" == 0 ]]; then
    echo ''
  fi
}

find "$DIR" -maxdepth 1 -type f | grep -Fv 'install.sh' | grep -Ev '\.swp$' | while read f; do
  install_rcfile "$f"
done
