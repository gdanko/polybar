#!/usr/bin/env python3

from polybar import glyphs, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import re
import sys

class SwapInfo(NamedTuple):
    success   : Optional[bool]  = False
    error     : Optional[str]   = None
    total     : Optional[int]   = 0
    used      : Optional[int]   = 0
    free      : Optional[int]   = 0
    pct_total : Optional[int]   = 0
    pct_used  : Optional[int]   = 0
    pct_free  : Optional[int]   = 0

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
        if stderr != '':
            swap_info = SwapInfo(
                success = False,
                error   = stderr.strip(),
            )
        else:
            swap_info = MemoryInfo(
                success = False,
                error   = f'failed to execute {command}',
            )

    return swap_info

def main():
    parser = argparse.ArgumentParser(description='Get swap usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    args = parser.parse_args()

    swap_info = get_swap_usage()

    if swap_info.success:
        print(f'{util.color_title(glyphs.cod_arrow_swap)} {util.byte_converter(swap_info.used, unit=args.unit)} / {util.byte_converter(swap_info.total, unit=args.unit)}')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.cod_arrow_swap)} {util.color_error(swap_info.error)}')
        sys.exit(1)

if __name__ == "__main__":
    main()
