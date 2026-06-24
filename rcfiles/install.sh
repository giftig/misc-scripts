#!/bin/bash

# Quick script to install symlinks for rcfiles in this repo into the correct places
# You'll have to fix any failures yourself, as it won't attempt to overwrite anything
# you already have in place to be on the safe side

cd "$(dirname "$0")"

install_rcfile() {
  f=$(basename "$1")
  echo -n "Installing rcfiles/$f... "
  ln -sT $(readlink -f "$1") "$HOME/.$f"

  if [[ "$?" == 0 ]]; then
    echo ''
  fi
}

gc() {
  git config --global "$1" "$2"
}

ls -1 | grep -Fv 'install.sh' | grep -Fv 'kitty' | grep -Ev '\.swp$' | while read f; do
  install_rcfile "$f"
done

echo 'Installing kitty conf...'
mkdir -p "$HOME/.config/kitty" && ln -s "$DIR/kitty/kitty.conf" "$HOME/.config/kitty/kitty.conf"
mkdir -p "$HOME/.kitty" && touch "$HOME/.kitty/default.session"

echo 'Setting default gitignore_global...'
gc core.excludesfile "$HOME/.gitignore_global"

echo 'Adding gitconfig include...'
gc include.path "$HOME/.gitconfig_common"
