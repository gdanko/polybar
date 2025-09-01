#!/usr/bin/env python3

from polybar import glyphs, util
import argparse
import re
import sys

def get_disk_usage(mountpoint: str) -> list:
    """
    Execute df -k against a mount point and return a dictionary with its values
    """

    if util.is_binary_installed('findmnt'):
        rc, stdout, stderr = util.run_piped_command(f'findmnt {mountpoint}')
        if rc != 0:
            return {
                'success':     False,
                'mountpoint':  mountpoint,
                'error':       f'{mountpoint} does not exist'
            }  

    rc, stdout, stderr = util.run_piped_command(f'df -B 1 {mountpoint} | sed -n "2p"')
    if rc == 0:
        if stdout != '':
            values = re.split(r'\s+', stdout)
            filesystem_dict = {
                'success'    : True,
                'mountpoint' : mountpoint,
                'filesystem' : values[0],
                'total'      : int(values[1]),
                'used'       : int(values[2]),
                'free'       : int(values[3]),
                'pct_total'  : 100,
            }
            filesystem_dict['pct_used'] = round ((filesystem_dict['used'] / (filesystem_dict['used'] + filesystem_dict['free'])) * 100)
            filesystem_dict['pct_free'] = filesystem_dict['pct_total'] - filesystem_dict['pct_used']

        else:
            filesystem_dict = {
                'success'   : False,
                'mountpoint': mountpoint,
                'error'     : f'{mountpoint} no output from df -B 1 {mountpoint}'
            }
    else:
        if stderr != '':
            filesystem_dict = {
                'success'   : False,
                'mountpoint':  mountpoint,
                'error'     : f'{mountpoint} {stderr.strip()}',
            }
        else:
            filesystem_dict = {
                'success'   : False,
                'mountpoint': mountpoint,
                'error'     : f'{mountpoint} non-zero exit code'
            }

    return filesystem_dict

def main():
    valid_tokens = ['^pct_total', '^pct_used', '^pct_free', '^total', '^used', '^free']
    parser = argparse.ArgumentParser(description='Get disk info from df(1)')
    parser.add_argument('-m', '--mountpoint', help='The mountpoint to check', required=True)
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-f', '--format', help=f'Output format, e.g., {{^free / ^total}}; valid tokens are: {",".join(valid_tokens)} ', required=False, default='{^free / ^total}')
    args = parser.parse_args()
    
    disk_info = get_disk_usage(args.mountpoint)

    if disk_info['success']:
        token_map = {
            '^pct_total': f'{disk_info["pct_total"]}%',
            '^pct_used' : f'{disk_info["pct_used"]}%',
            '^pct_free': f'{disk_info["pct_free"]}%',
            '^total': util.byte_converter(number=disk_info['total'], unit=args.unit),
            '^used': util.byte_converter(number=disk_info['used'], unit=args.unit),
            '^free': util.byte_converter(number=disk_info['free'], unit=args.unit),
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

    if disk_info['success']:
        filesystem_usage = f'{util.color_title(glyphs.md_harddisk)} {util.color_title(disk_info["mountpoint"])} {output}'
    else:
        filesystem_usage = f'{util.color_title(glyphs.md_harddisk)} {util.color_error(disk_info["error"])}'

    print(filesystem_usage)

if __name__ == "__main__":
    main()
