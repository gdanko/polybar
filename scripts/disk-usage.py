#!/usr/bin/env python3

from polybar import glyphs, util
import argparse
import os
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
                'error':       f'does not exist'
            }  

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

    return filesystem_dict

def main():
    parser = argparse.ArgumentParser(description="Get disk info from df(1)")
    parser.add_argument("-m", "--mountpoint", help="The mountpoint to check", required=True)
    parser.add_argument("-u", "--unit", help="The unit to use for display", choices=util.get_valid_units(), required=False)
    args = parser.parse_args()
    
    disk_info = get_disk_usage(args.mountpoint)

    if disk_info['success']:
        filesystem_usage = f'{util.colorize(glyphs.md_harddisk)} {disk_info["mountpoint"]} {util.byte_converter(number=disk_info["used"], unit=args.unit)} / {util.byte_converter(number=disk_info["total"], unit=args.unit)}'
    else:
        filesystem_usage = f'{util.colorize(glyphs.md_harddisk)} {disk_info["mountpoint"]} {disk_info["error"]}'

    print(filesystem_usage)

if __name__ == "__main__":
    main()
