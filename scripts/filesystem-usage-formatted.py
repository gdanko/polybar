#!/usr/bin/env python3

from polybar import glyphs, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import re
import sys

class FilesystemInfo(NamedTuple):
    success    : Optional[bool]  = False
    error      : Optional[str]   = None
    mountpoint : Optional[str]   = None
    filesystem : Optional[str]   = None
    pct_total  : Optional[int]   = 0
    pct_used   : Optional[int]   = 0
    pct_free   : Optional[int]   = 0
    total      : Optional[int]   = 0
    used       : Optional[int]   = 0
    free       : Optional[int]   = 0

def get_disk_usage(mountpoint: str) -> list:
    """
    Execute df -B 1 against a mount point and return a namedtuple with its values
    """

    rc, stdout, stderr = util.run_piped_command(f'findmnt {mountpoint}')
    if rc != 0:
        return FilesystemInfo(
            success    = False,
            mountpoint = mountpoint,
            error      = f'{mountpoint} does not exist'
        )

    command = f'df -B 1 {mountpoint} | sed -n "2p"'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        if stdout != '':
            values = re.split(r'\s+', stdout)

            filesystem = values[0]
            total      = int(values[1])
            used       = int(values[2])
            free       = int(values[3])
            pct_total  = 100
            pct_used   = round((used / (used + free)) * 100)
            pct_free   = pct_total - pct_used

            filesystem_info = FilesystemInfo(
                success    = True,
                mountpoint = mountpoint,
                filesystem = filesystem,
                total      = total,
                used       = used,
                free       = free,
                pct_total  = pct_total,
                pct_used   = pct_used,
                pct_free   = pct_free,
            )
        else:
            filesystem_info = FilesystemInfo(
                success    = False,
                mountpoint = mountpoint,
                error      = f'no output from {command}',
            )
    else:
        if stderr != '':
            filesystem_info = FilesystemInfo(
                success    = False,
                mountpoint = mountpoint,
                error      = stderr,
            )
        else:
            filesystem_info = FilesystemInfo(
                success    = False,
                mountpoint = mountpoint,
                error      = f'failed to execute {command}'
            )

    return filesystem_info

def main():
    missing = util.missing_binaries(['df', 'findmnt', 'sed'])
    if len(missing) > 0:
        error = f'please install: {", ".join(missing)}'
        output = f'{util.color_title(glyphs.md_harddisk)} {util.color_error(error)}'
        print(output)
        sys.exit(1)

    valid_tokens = ['^pct_total', '^pct_used', '^pct_free', '^total', '^used', '^free']
    parser = argparse.ArgumentParser(description='Get disk info from df(1)')
    parser.add_argument('-m', '--mountpoint', help='The mountpoint to check', required=True)
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-f', '--format', help=f'Output format, e.g., {{^free / ^total}}; valid tokens are: {', '.join(valid_tokens)} ', required=False, default='{^used / ^total}')
    args = parser.parse_args()
    
    disk_info = get_disk_usage(args.mountpoint)

    if disk_info.success:
        token_map = {
            '^pct_total': f'{disk_info.pct_total}%',
            '^pct_used' : f'{disk_info.pct_used}%',
            '^pct_free': f'{disk_info.pct_free}%',
            '^total': util.byte_converter(number=disk_info.total, unit=args.unit),
            '^used': util.byte_converter(number=disk_info.used, unit=args.unit),
            '^free': util.byte_converter(number=disk_info.free, unit=args.unit),
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
            if len(invalid) > 0 or len(valid) == 0:
                error = f'Invalid format: {args.format}'
                print(f'{util.color_title(glyphs.md_harddisk)} {util.color_error(error)}')
                sys.exit(1)

            for idx, token in enumerate(valid):
                output = output.replace(token, token_map[token])

    if disk_info.success:
        print(f'{util.color_title(glyphs.md_harddisk)} {util.color_title(disk_info.mountpoint)} {output}')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.md_harddisk)} {util.color_error(disk_info.error)}')
        sys.exit(1)

if __name__ == '__main__':
    main()
