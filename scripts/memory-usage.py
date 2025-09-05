#!/usr/bin/env python3

from polybar import glyphs, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import re
import sys

class MemoryInfo(NamedTuple):
    success   : Optional[bool]  = False
    error     : Optional[str]   = None
    total     : Optional[int]   = 0
    shared    : Optional[int]   = 0
    buffers   : Optional[int]   = 0
    cache     : Optional[int]   = 0
    available : Optional[int]   = 0
    pct_total : Optional[int]   = 0
    pct_used  : Optional[int]   = 0
    pct_free  : Optional[int]   = 0
    total     : Optional[int]   = 0
    used      : Optional[int]   = 0
    free      : Optional[int]   = 0

def get_memory_usage():
    """
    Execute free -b -w and return a dictionary with its values
    """

    rc, stdout, stderr = util.run_piped_command('free -b -w | sed -n "2p"')
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
                error   = 'non-zero exit code',
            )

    return mem_info

def main():
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    args = parser.parse_args()

    memory_info = get_memory_usage()

    if memory_info.success:
        print(f'{util.color_title(glyphs.fa_memory)} {util.byte_converter(memory_info.used, unit=args.unit)} / {util.byte_converter(memory_info.total, unit=args.unit)}')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.fa_memory)} {util.color_error(memory_info.error)}')
        sys.exit(1)

if __name__ == "__main__":
    main()
