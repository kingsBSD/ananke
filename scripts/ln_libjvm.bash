#!/bin/bash
# https://gist.github.com/solidsnack/7569266
set -o errexit -o nounset -o pipefail
function -h {
cat <<USAGE
 USAGE: ln_libjvm.bash
  Symlink a likely libjvm.so into /usr/bin.
USAGE
}; function --help { -h ;}
export LC_ALL=en_US.UTF-8

function main {
  ln_libjvm
}

function ln_libjvm {
  # Expand glob to get likely SOs.
  local libjvms=( /usr/lib/jvm/java-*-openjdk-*/jre/lib/*/server/libjvm.so )
  if [[ -f ${libjvms[0]} ]]
  then sudo ln -nsf "${libjvms[0]}" /usr/lib/libjvm.so
  else err "Not a file: ${libjvms[0]}"
  fi
}

function msg { out "$*" >&2 ;}
function err { local x=$? ; msg "$*" ; return $(( $x == 0 ? 1 : $x )) ;}
function out { printf '%s\n' "$*" ;}

if [[ ${1:-} ]] && declare -F | cut -d' ' -f3 | fgrep -qx -- "${1:-}"
then "$@"
else main "$@"
fi