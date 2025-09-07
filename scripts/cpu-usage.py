#!/usr/bin/env python3

from polybar import glyphs, util
from typing import Any, Dict, List, Optional, NamedTuple
import platform
import re
import sys

class CpuInfo(NamedTuple):
    success   : Optional[bool]  = False
    error     : Optional[str]   = None
    idle      : Optional[float] = 0.0
    nice      : Optional[float] = 0.0
    system    : Optional[float] = 0.0
    user      : Optional[float] = 0.0
    iowait    : Optional[float] = 0.0
    irq       : Optional[float] = 0.0
    softirq   : Optional[float] = 0.0
    steal     : Optional[float] = 0.0
    guest     : Optional[float] = 0.0
    guestnice : Optional[float] = 0.0

def get_icon():
    if platform.machine() == 'x86':
        return glyphs.md_cpu_32_bit
    elif platform.machine() == 'x86_64':
        return glyphs.md_cpu_64_bit
    else:
        return glyphs.oct_cpu

def get_cpu_usage():
    """
    Execute mpstat'
    """

    command = f'mpstat | tail -n 1'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        if stdout != '':
            values = re.split(r'\s+', stdout)
            cpu_info = CpuInfo(
                success   = True,
                idle      = util.pad_float(values[12]),
                nice      = util.pad_float(values[4]),
                system    = util.pad_float(values[5]),
                user      = util.pad_float(values[3]),
                iowait    = util.pad_float(values[6]),
                irq       = util.pad_float(values[7]),
                softirq   = util.pad_float(values[7]),
                steal     = util.pad_float(values[9]),
                guest     = util.pad_float(values[10]),
                guestnice = util.pad_float(values[11]),
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
                error     = f'failed to execute {command}'
            )

    return cpu_info

def main():
    cpu_info = get_cpu_usage()

    if cpu_info.success:
        print(f'{util.color_title(get_icon())} user {cpu_info.user}%, sys {cpu_info.system}%, idle {cpu_info.idle}%')
        sys.exit(0)
    else:
        print(f'{util.color_title(get_icon())} {util.color_error(cpu_info.error)}')
        sys.exit(1)

if __name__ == "__main__":
    main()
