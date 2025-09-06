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
    Execute free -b -w and return a dictionary with its values
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
            swap_info = SwapInfo(
                success = False,
                error   = 'non-zero exit code',
            )

    return swap_info

def main():
    valid_tokens = ['^pct_total', '^pct_used', '^pct_free', '^total', '^used', '^free']
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-f', '--format', help=f'Output format, e.g., {{^free / ^total}}; valid tokens are: {', '.join(valid_tokens)} ', required=False, default='{^free / ^total}')
    args = parser.parse_args()

    swap_info = get_swap_usage()

    if swap_info.success:
        token_map = {
            '^pct_total': f'{swap_info.pct_total}%',
            '^pct_used' : f'{swap_info.pct_used}%',
            '^pct_free': f'{swap_info.pct_free}%',
            '^total': util.byte_converter(number=swap_info.total, unit=args.unit),
            '^used': util.byte_converter(number=swap_info.used, unit=args.unit),
            '^free': util.byte_converter(number=swap_info.free, unit=args.unit),
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
                print(f'{util.color_title(glyphs.cod_arrow_swap)} {util.color_error(error)}')
                sys.exit(1)

            for idx, token in enumerate(valid):
                output = output.replace(token, token_map[token])

    if swap_info.success:
        print(f'{util.color_title(glyphs.cod_arrow_swap)} {output}')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.cod_arrow_swap)} {util.color_error(swap_info['error'])}')
        sys.exit(1)

if __name__ == "__main__":
    main()
