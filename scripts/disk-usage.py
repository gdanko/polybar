#!/usr/bin/env python3

from pathlib import Path
from polybar import util
import argparse
import os
import re
import sys

def get_disk_usage(mountpoints: list) -> list:
    """
    Execute df -k against a mount point and return a dictionary with its values
    """

    filesystems = []

    for mountpoint in mountpoints:
        rc, stdout, stderr = util.run_piped_command(f'df -B 1 {mountpoint} | sed -n "2p"')
        if rc == 0:
            if stdout != '':
                values = re.split(r'\s+', stdout)
                filesystem_dict = {
                    'success':     True,
                    'mountpoint':  mountpoint,
                    'filesystem':  values[0],
                    'total':       int(values[1]),
                    'used':        int(values[2]),
                    'free':        int(values[3]),
                    'use_percent': values[4],
                }
                
            else:
                filesystem_dict = {
                    'success':     False,
                    'mountpoint':  mountpoint,
                    'error':       f'no output from df -B 1 {mountpoint}'
                }
        else:
            if stderr != '':
                filesystem_dict = {
                    'success':     False,
                    'mountpoint':  mountpoint,
                    'error':       stderr.strip(),
                }
            else:
                filesystem_dict = {
                    'success':     False,
                    'mountpoint':  mountpoint,
                    'error':       'non-zero exit code'
                }
        filesystems.append(filesystem_dict)

    return filesystems

def main():
    disk_icon = util.surrogatepass('\udb80\udeca')

    parser = argparse.ArgumentParser(description="Get disk info from df(1)")
    parser.add_argument("-m", "--mountpoint", action='append', help="The mountpoint to check; can be used multiple times", required=True)
    parser.add_argument("-u", "--unit", help="The unit to use for display", choices=util.get_valid_units(), required=False)
    args = parser.parse_args()
    
    disk_info = get_disk_usage(args.mountpoint)

    output = []
    for filesystem in disk_info:
        if filesystem['success']:
            filesystem_usage = f'{util.colorize(disk_icon)} {filesystem["mountpoint"]} {util.byte_converter(number=filesystem["used"], unit=args.unit)} / {util.byte_converter(number=filesystem["total"], unit=args.unit)}'
        else:
            filesystem_usage = f'{util.colorize(disk_icon)} {filesystem["mountpoint"]} {filesystem["error"]}'
        output.append(filesystem_usage)

    print(' | '.join(output))

if __name__ == "__main__":
    main()
