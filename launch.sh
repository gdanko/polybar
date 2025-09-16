#!/usr/bin/env bash

POLYBAR_ROOT=${HOME}/.config/polybar
# ${POLYBAR_ROOT}/launch.py start --debug

#!/bin/sh

show_help() {
    cat << EOF
Usage: $(basename $0) (start|stop|restart|status) [OPTIONS]

Options:
  -d, --debug        Enable debug mode
  -h, --help         Show this help message and exit

Commands:
  restart  Restart polybar and its backgound modules
  start    Start polybar and its backgound modules
  status   Get the status of polybar and its background modules
  stop     Stop polybar and its backgound modules

EOF
}

# Enforce: positional first
export POSIXLY_CORRECT=1

if [ $# -lt 1 ]; then
    echo "no action was supplied, assuming \"start\""
    ${POLYBAR_ROOT}/launch.py start
    exit 0
fi

choice="$1"
shift

case "$choice" in
  start|stop|restart|status)
    action=$choice
    ;;
  -h|--help)
    show_help
    exit 0
    ;;
  *) 
    echo "error: invalid action '$choice'"
    show_help
    exit 1
    ;;
esac

# Parse options
OPTS=$(getopt -o dh --long debug,help -n "$0" -- "$@")
if [ $? != 0 ]; then
    echo "Try '$0 --help' for more information." >&2
    exit 1
fi

eval set -- "$OPTS"

file=""
debug=false

while true; do
  case "$1" in
    -d | --debug ) debug=true; shift ;;
    -h | --help ) show_help; exit 0 ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

command="${POLYBAR_ROOT}/launch.py ${action}"
if [ $debug == 'true' ]; then
    command="$command --debug"
fi

$command
