#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, state, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import os
import re
import sys
import time

class SwapInfo(NamedTuple):
    success   : Optional[bool]  = False
    error     : Optional[str]   = None
    total     : Optional[int]   = 0
    used      : Optional[int]   = 0
    free      : Optional[int]   = 0
    pct_total : Optional[int]   = 0
    pct_used  : Optional[int]   = 0
    pct_free  : Optional[int]   = 0

def get_statefile() -> str:
    statefile = os.path.basename(__file__)
    statefile_no_ext = os.path.splitext(statefile)[0]
    return Path.home() / f'.polybar-{statefile_no_ext}-state'

def get_swap_usage():
    """
    Execute free -b -w and return a namedtuple with its values
    """

    command = 'free -b -w | sed -n "3p"'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        if stdout != '':
            values    = re.split(r'\s+', stdout)
            total     = int(values[1])
            used      = int(values[2])
            free      = int(values[3])
            pct_total = 100
            pct_used  = int(used / total) * 100
            pct_free  = pct_total - pct_used

            swap_info = SwapInfo(
                success   = True,
                total     = total,
                used      = used,
                free      = free,
                pct_total = 100,
                pct_used  = pct_used,
                pct_free  = pct_free,

            )
        else:
            swap_info = SwapInfo(
                success = False,
                error   = 'no output from free',
            )
    else:
        swap_info = SwapInfo(
            success   = False,
            error     = stderr if stderr != '' else f'failed to execute "{command}"',
        )

    return swap_info

def main():
    mode_count = 3
    parser = argparse.ArgumentParser(description='Get swap usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    parser.add_argument('-i', '--interval', help='The update interval (in seconds)', required=False, default=2, type=int)
    parser.add_argument('-b', '--background', action='store_true', help='Run this script in the background', required=False)
    args = parser.parse_args()

    # Background mode: periodic updates
    if args.background:
        # Wait a bit to let Polybar fully initialize
        time.sleep(1)
        while True:
            if not util.polybar_is_running():
                sys.exit(0)
            _, _, _ = util.run_piped_command('polybar-msg action swap-usage hook 0')
            time.sleep(args.interval)
        sys.exit(0)

    else:
        if args.toggle:
            mode = state.next_state(statefile=get_statefile(), mode_count=mode_count)
        else:
            mode = state.read_state(statefile=get_statefile())

        swap_info = get_swap_usage()

        if swap_info.success:
            pct_total = f'{swap_info.pct_total}%'
            pct_used  = f'{swap_info.pct_used}%'
            pct_free  = f'{swap_info.pct_free}%'
            total     = util.byte_converter(number=swap_info.total, unit=args.unit)
            used      = util.byte_converter(number=swap_info.used, unit=args.unit)
            free      = util.byte_converter(number=swap_info.free, unit=args.unit)

            if mode == 0:
                output = f'{util.color_title(glyphs.cod_arrow_swap)} {used} / {total}'
            elif mode == 1:
                output = f'{util.color_title(glyphs.cod_arrow_swap)} {pct_used} used'
            elif mode == 2:
                output = f'{util.color_title(glyphs.cod_arrow_swap)} {used} used / {free} free'
            print(output)
            sys.exit(0)
        else:
            output = f'{util.color_title(glyphs.cod_arrow_swap)} {util.color_error(swap_info.error)}'
            print(output)
            sys.exit(1)

if __name__ == "__main__":
    main()
