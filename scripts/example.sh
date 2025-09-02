#!/usr/bin/env bash
STATEFILE="/tmp/polybar-example-state"

toggle() {
    state=$(cat "$STATEFILE" 2>/dev/null || echo "0")
    next=$(( (state + 1) % 3 ))
    echo "$next" > "$STATEFILE"
}

reset() {
    echo "0" > "$STATEFILE"
}

output() {
    state=$(cat "$STATEFILE" 2>/dev/null || echo "0")
    case "$state" in
        0) echo "Format A" ;;
        1) echo "Format B" ;;
        2) echo "Format C" ;;
    esac
}

case "$1" in
    toggle) toggle ;;
    reset) reset ;;
esac

# Always print the current state
output
