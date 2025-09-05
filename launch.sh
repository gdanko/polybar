#!/usr/bin/env bash

POLYBAR_ROOT="${HOME}/.config/polybar"
POLYBAR_SCRIPTS="${POLYBAR_ROOT}/scripts"
POLYBAR_CONFIG="${POLYBAR_ROOT}/config.ini"

launch_shell() {
    BAR_NAME="main"
    MODULES_LEFT=$(polybar --dump=modules-left)
    MODULES_RIGHT=$(polybar --dump=modules-right)

    CPU_USAGE_INTERVAL=2
    FILESYSTEM_USAGE_INTERVAL=2
    MEMORY_USAGE_INTERVAL=2

    if grep -q "ipc = true" ${POLYBAR_CONFIG}; then
        polybar-msg cmd quit
    else
        killall -q polybar
    fi

    echo "---" | tee -a /tmp/polybar-${BAR_NAME}.log
    polybar ${BAR_NAME} 2>&1 | tee -a /tmp/polybar-${BAR_NAME}.log & disown

    echo "Bars launched..."

    # Launch the daemonized version of cpu-usage-clickable, but only if it's enabled
    if [[ $MODULES_LEFT =~ "cpu-usage-clickable" || $MODULES_RIGHT =~ "cpu-usage-clickable" ]]; then
        SCRIPT_NAME="${POLYBAR_SCRIPTS}/cpu-usage-clickable.py"
        if [ -f "${SCRIPT_NAME}" ]; then
            "${SCRIPT_NAME}" --interval ${CPU_USAGE_INTERVAL} --daemonize
        fi
    fi

    # Launch the daemonized version of every instance of filesystem-usage-clickable, but only if they're enabled
    FILESYSTEMS_LEFT=($(echo $MODULES_LEFT | grep -o 'filesystem-usage-clickable[^ ]*'))
    FILESYSTEMS_RIGHT=($(echo $MODULES_RIGHT | grep -o 'filesystem-usage-clickable[^ ]*'))
    FILESYSTEMS=("${FILESYSTEMS_LEFT[@]}" "${FILESYSTEMS_RIGHT[@]}")

    if [ ${#FILESYSTEMS[@]} -gt 0 ]; then
        for FILESYSTEM in "${FILESYSTEMS[@]}"; do
            NAME=$(echo ${FILESYSTEM} | awk -F "-" '{print $4}')
            SCRIPT_NAME="${POLYBAR_SCRIPTS}/filesystem-usage-clickable.py"
            if [ -f "${SCRIPT_NAME}" ]; then
                "${SCRIPT_NAME}" --name ${NAME} --interval ${FILESYSTEM_USAGE_INTERVAL} --daemonize
            fi
        done
    fi

    # Launch the daemonized version of memory-usage-clickable, but only if it's enabled
    if [[ $MODULES_LEFT =~ "memory-usage-clickable" || $MODULES_RIGHT =~ "memory-usage-clickable" ]]; then
        SCRIPT_NAME="${POLYBAR_SCRIPTS}/memory-usage-clickable.py"
        if [ -f "${SCRIPT_NAME}" ]; then
            "${SCRIPT_NAME}" --interval ${MEMORY_USAGE_INTERVAL} --daemonize
        fi
    fi
}

if [ -x "${POLYBAR_ROOT}/launch.py" ]; then
    "${POLYBAR_ROOT}/launch.py"
else
    echo Launching via shell...
    launch_shell
fi
