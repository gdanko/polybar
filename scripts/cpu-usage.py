#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, state, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import json
import os
import platform
import re
import sys
import time

class CpuInfo(NamedTuple):
    success        : Optional[bool]  = False
    error          : Optional[str]   = None
    model          : Optional[str]   = None
    freq           : Optional[str]   = None
    cores_logical  : Optional[int]   = 0
    cores_physical : Optional[int]   = 0
    idle           : Optional[float] = 0.0
    nice           : Optional[float] = 0.0
    system         : Optional[float] = 0.0
    user           : Optional[float] = 0.0
    iowait         : Optional[float] = 0.0
    irq            : Optional[float] = 0.0
    softirq        : Optional[float] = 0.0
    steal          : Optional[float] = 0.0
    guest          : Optional[float] = 0.0
    guestnice      : Optional[float] = 0.0
    load1          : Optional[float] = 0.0
    load5          : Optional[float] = 0.0
    load15         : Optional[float] = 0.0

def get_statefile() -> str:
    statefile = os.path.basename(__file__)
    statefile_no_ext = os.path.splitext(statefile)[0]
    return Path.home() / f'.polybar-{statefile_no_ext}-state'

def get_icon():
    if platform.machine() == 'x86':
        return glyphs.md_cpu_32_bit
    elif platform.machine() == 'x86_64':
        return glyphs.md_cpu_64_bit
    else:
        return glyphs.oct_cpu

def get_cpu_type():
    command = 'grep -m 1 "model name" /proc/cpuinfo'
    rc, stdout, _ = util.run_piped_command(command)
    if rc == 0:
        return re.split(r'\s*:\s*', stdout)[1]
    else:
        return 'Unknown CPU model'

def get_cpu_freq():
    command = f'lscpu | grep "CPU max MHz"'
    rc, stdout, _ = util.run_piped_command(command)
    if rc == 0:
        bits = re.split(r'\s*:\s*', stdout)
        if len(bits) == 2:
            # error checking
            freq = int(float(bits[1]))
            if freq < 1000:
                return f'{freq} MHz'
            else:
                return f'{util.pad_float(float(freq / 1000))} GHz'
        else:
            return 'Unknown CPU freq'
    else:
        return 'Unknown CPU freq'

def get_logical_cpu_cores():
    command = 'grep -c ^processor /proc/cpuinfo'
    rc, stdout, _ = util.run_piped_command(command)
    if rc == 0 and stdout != '':
        return int(stdout)

    return -1

def get_physical_cpu_cores():
    command = 'grep -m 1 "cpu cores" /proc/cpuinfo'
    rc, stdout, _ = util.run_piped_command(command)
    if rc == 0 and stdout != '':
        physical_cores = re.split(r'\s+:\s+', stdout)[1]
        return int(physical_cores)

    return -1

def get_load_averages():
    """
    Execute uptime and return the load averages
    """
    rc, stdout, stderr = util.run_piped_command('uptime')
    if rc == 0:
        if stdout != '':
            match = re.search(r"load average:\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)", stdout)
            if match:
                return [float(avg) for avg in list(match.groups())]

    return [-1.0, -1.0, -1.0]

def get_cpu_info() -> CpuInfo:
    """
    Gather information about the CPU and return it to main()
    """

    if platform.machine() == 'x86':
        icon = glyphs.md_cpu_32_bit
    elif platform.machine() == 'x86_64':
        icon = glyphs.md_cpu_64_bit
    else:
        icon = glyphs.oct_cpu

    # make sure mpstat is installed
    load_averages = get_load_averages()
    rc, stdout, stderr = util.run_piped_command(f'mpstat | tail -n 1')
    if rc == 0:
        if stdout != '':
            values = re.split(r'\s+', stdout)
            cpu_info = CpuInfo(
                success            = True,
                model              = get_cpu_type(),
                freq               = get_cpu_freq(),
                cores_logical      = get_logical_cpu_cores(),
                cores_physical     = get_physical_cpu_cores(),
                idle               = util.pad_float(values[12]),
                nice               = util.pad_float(values[4]),
                system             = util.pad_float(values[5]),
                user               = util.pad_float(values[3]),
                iowait             = util.pad_float(values[6]),
                irq                = util.pad_float(values[7]),
                softirq            = util.pad_float(values[7]),
                steal              = util.pad_float(values[9]),
                guest              = util.pad_float(values[10]),
                guestnice          = util.pad_float(values[11]),
                load1              = util.pad_float(load_averages[0]),
                load5              = util.pad_float(load_averages[1]),
                load15             = util.pad_float(load_averages[2]),
            )
        else:
            cpu_info = CpuInfo(
                success   = False,
                error     = f'no output from mpstat',
            )
    else:
        if stderr != '':
            cpu_info = CpuInfo(
                success   = False,
                error     = stderr,
            )
        else:
            cpu_info = CpuInfo(
                success   = False,
                error     = f'failed to execute {command}',
            )

    return cpu_info

def main():
    mode_count = 3
    parser = argparse.ArgumentParser(description='Get CPU usage from mpstat(1)')
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    parser.add_argument('-i', '--interval', help='The update interval (in seconds)', required=False, default=2, type=int)
    parser.add_argument('-b', '--background', action='store_true', help='Run this script in the background', required=False)
    args = parser.parse_args()

    # Daemon mode: periodic updates
    if args.background:
        # Wait a bit to let Polybar fully initialize
        time.sleep(1)
        while True:
            if not util.polybar_is_running():
                sys.exit(0)
            _, _, _ = util.run_piped_command('polybar-msg action cpu-usage hook 0')
            time.sleep(args.interval)
        sys.exit(0)
    else:
        if args.toggle:
            mode = state.next_state(statefile=get_statefile(), mode_count=mode_count)
        else:
            mode = state.read_state(statefile=get_statefile())

        cpu_info = get_cpu_info()

        if cpu_info.success:
            if mode == 0:
                output = f'{util.color_title(get_icon())} user {cpu_info.user}%, sys {cpu_info.system}%, idle {cpu_info.idle}%'
            elif mode == 1:
                output = f'{util.color_title(get_icon())} {cpu_info.cores_physical}C/{cpu_info.cores_logical}T x {cpu_info.model} @ {cpu_info.freq}'
            elif mode == 2:
                output = f'{util.color_title(get_icon())} load {cpu_info.load1},  {cpu_info.load5},  {cpu_info.load15}'
            print(output)
            sys.exit(0)
        else:
            output = f'{util.color_title(get_icon())} {util.color_error(cpu_info.error)}'
            print(output)
            sys.exit(1)

if __name__ == "__main__":
    main()
