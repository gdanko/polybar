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
    used      : Optional[int]   = 0
    free      : Optional[int]   = 0
    shared    : Optional[int]   = 0
    buffers   : Optional[int]   = 0
    cache     : Optional[int]   = 0
    available : Optional[int]   = 0
    pct_total : Optional[int]   = 0
    pct_used  : Optional[int]   = 0
    pct_free  : Optional[int]   = 0

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
                error   = stderr,
            )
        else:
            mem_info = MemoryInfo(
                success = False,
                error   = f'failed to execute {command}',
            )

    return mem_info

def main():
    missing = util.missing_binaries(['free', 'sed'])
    if len(missing) > 0:
        error = f'please install: {", ".join(missing)}'
        output = f'{util.color_title(glyphs.fa_memory)} {util.color_error(error)}'
        print(output)
        sys.exit(1)

    valid_tokens = ['^pct_total', '^pct_used', '^pct_free', '^total', '^used', '^free']
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-f', '--format', help=f'Output format, e.g., {{^free / ^total}}; valid tokens are: {', '.join(valid_tokens)} ', required=False, default='{^free / ^total}')
    args = parser.parse_args()

    memory_info = get_memory_usage()

    if memory_info.success:
        token_map = {
            '^pct_total': f'{memory_info.pct_total}%',
            '^pct_used' : f'{memory_info.pct_used}%',
            '^pct_free': f'{memory_info.pct_free}%',
            '^total': util.byte_converter(number=memory_info.total, unit=args.unit),
            '^used': util.byte_converter(number=memory_info.used, unit=args.unit),
            '^free': util.byte_converter(number=memory_info.free, unit=args.unit),
        }

        # For when the format is blank
        if not args.format or args.format == '':
            args.format = '{^used / ^total}'

        if args.format and args.format != '':
            output = args.format.replace('{','').replace('}', '')
            valid = []
            invalid = []
            tokens = re.findall(r"\^\w+", args.format)
            for token in tokens:
                if token in valid_tokens:
                    valid.append(token)
                else:
                    invalid.append(token)
            if len(invalid) > 0 or len(tokens) == 0:
                error = f'Invalid format: {args.format}'
                print(f'{util.color_title(glyphs.fa_memory)} {util.color_error(error)}')
                sys.exit(1)

            for idx, token in enumerate(valid):
                output = output.replace(token, token_map[token])

    if memory_info.success:
        print(f'{util.color_title(glyphs.fa_memory)} {output}')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.fa_memory)} {util.color_error(memory_info['error'])}')
        sys.exit(1)

if __name__ == "__main__":
    main()
