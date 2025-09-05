#!/usr/bin/env bash

POLYBAR_ROOT="${HOME}/.config/polybar"
POLYBAR_SCRIPTS="${POLYBAR_ROOT}/scripts"
POLYBAR_CONFIG="${POLYBAR_ROOT}/config.ini"
BAR_NAME="top"

# Terminate already running bar instances
if grep -q "ipc = true" ${POLYBAR_CONFIG}; then
    polybar-msg cmd quit
else
    killall -q polybar
fi

echo "---" | tee -a /tmp/polybar-${BAR_NAME}.log
polybar ${BAR_NAME} 2>&1 | tee -a /tmp/polybar-${BAR_NAME}.log & disown

echo "Bars launched..."
