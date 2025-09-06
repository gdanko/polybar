#!/usr/bin/env python3

from polybar import glyphs, state, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import os
import re
import sys
import time

class MemoryInfo(NamedTuple):
    success   : Optional[bool]  = False
    error     : Optional[str]   = None
    total     : Optional[int]   = 0
    used      : Optional[int]   = 0
    free      : Optional[int]   = 0
    shared    : Optional[int]   = 0
    buffers   : Optional[int]   = 0
    cache     : Optional[int]   = 0
    available : Optional[int]   = 0
    pct_total : Optional[int]   = 0
    pct_used  : Optional[int]   = 0
    pct_free  : Optional[int]   = 0

def get_statefile_name() -> str:
    statefile = os.path.basename(__file__)
    statefile_no_ext = os.path.splitext(statefile)[0]
    return os.path.join(
        util.get_home_directory(),
        f'.polybar-{statefile_no_ext}-state'
    )

def get_memory_usage():
    """
    Execute free -b -w and return a namedtuple with its values
    """

    command = 'free -b -w | sed -n "2p"'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        if stdout != '':
            values    = re.split(r'\s+', stdout)
            total     = int(values[1])
            shared    = int(values[4])
            buffers   = int(values[5])
            cache     = int(values[6])
            available = int(values[7])
            used      = total - available
            free      = total - used
            pct_total = 100
            pct_used  = int(((total - available) / total) * 100)
            pct_free  = pct_total - pct_used

            mem_info = MemoryInfo(
                success   = True,
                total     = total,
                shared    = shared,
                buffers   = buffers,
                cache     = cache,
                available = available,
                pct_total = 100,
                pct_used  = pct_used,
                pct_free  = pct_free,
                used      = used,
                free      = free,
            )
        else:
            mem_info = MemoryInfo(
                success = False,
                error   = 'no output from free',
            )
    else:
        if stderr != '':
            mem_info = MemoryInfo(
                success = False,
                error   = stderr.strip(),
            )
        else:
            mem_info = MemoryInfo(
                success = False,
                error   = f'failed to execute {command}',
            )

    return mem_info

def main():
    mode_count = 3
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    parser.add_argument('-i', '--interval', help='The update interval (in seconds)', required=False, default=2, type=int)
    parser.add_argument('-d', '--daemonize', action='store_true', help='Daemonize', required=False)
    args = parser.parse_args()

    # Daemon mode: periodic updates
    if args.daemonize:
        # Wait a bit to let Polybar fully initialize
        time.sleep(1)
        while True:
            if not util.polybar_is_running():
                sys.exit(0)
            _, _, _ = util.run_piped_command('polybar-msg action memory-usage-clickable hook 0')
            time.sleep(args.interval)
        sys.exit(0)
    else:
        statefile_name = get_statefile_name()
        mode = state.next_state(statefile_name=statefile_name, mode_count=mode_count) if args.toggle else state.read_state(statefile_name=statefile_name)
        memory_info = get_memory_usage()

        if memory_info.success:
            pct_total = f'{memory_info.pct_total}%'
            pct_used  = f'{memory_info.pct_used}%'
            pct_free  = f'{memory_info.pct_free}%'
            total     = util.byte_converter(number=memory_info.total, unit=args.unit)
            used      = util.byte_converter(number=memory_info.used, unit=args.unit)
            free      = util.byte_converter(number=memory_info.free, unit=args.unit)

            if mode == 0:
                output = f'{util.color_title(glyphs.fa_memory)} {used} / {total}'
            elif mode == 1:
                output = f'{util.color_title(glyphs.fa_memory)} {pct_used} used'
            elif mode == 2:
                output = f'{util.color_title(glyphs.fa_memory)} {used} used / {free} free'
            print(output)
            sys.exit(0)
        else:
            output = f'{util.color_title(glyphs.fa_memory)} {util.color_error(memory_info.error)}'
            print(output)
            sys.exit(1)

if __name__ == "__main__":
    main()
