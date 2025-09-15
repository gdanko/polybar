#!/bin/bash
# Watch for session resume and restart Polybar

SESSION=$(loginctl | grep $(whoami) | awk '{print $1}')

last_state="inactive"

while true; do
    # Check IdleHint from loginctl (false = active)
    idle=$(loginctl show-session "$SESSION" -p IdleHint | cut -d= -f2)

    if [[ "$last_state" == "true" && "$idle" == "false" ]]; then
        # Session just became active (resume from lock/suspend)
        # polybar-msg cmd restart
        ${HOME}/.config/polybar/launch.py stop
        # Make sure to clean up the errant scripts, I will loop and test
        ${HOME}/.config/polybar/launch.py start
    fi

    last_state="$idle"
    sleep 5
done
