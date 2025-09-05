#!/usr/bin/env python3

from polybar import glyphs, state, util
import argparse
import json
import os
import re
import sys

def get_disk_uuid(mountpoint: str='') -> str:
    # Make this foolproof
    rc, stdout, stderr = util.run_piped_command(f'findmnt {mountpoint}')
    # TARGET    SOURCE                      FSTYPE    OPTIONS
    # /         /dev/mapper/vgmint-root     ext4      rw,relatime,errors=remount-ro
    if rc == 0:
        lines = stdout.strip().split('\n')
        fs = re.split(r'\s+', lines[1])[1]
        if fs != '':
            rc, stdout, stderr = util.run_piped_command(f'blkid {fs}')
            # /dev/mapper/vgmint-root: UUID="6dc8d2cd-8977-4fa3-8357-23ced5f9dd4b" BLOCK_SIZE="4096" TYPE="ext4"
            if rc == 0:
                match = re.search(r'UUID="([^"]+)"', stdout.strip())
                if match:
                    return match.group(1)
            else:
                return ''
        else:
            return ''
    else:
        print(f'{util.color_title(glyphs.md_harddisk)} {util.color_error(f"{mountpoint} is an invalid mountpoint")}')
        sys.exit(1)

def get_statefile_name(mountpoint: str='') -> str:
    uuid = get_disk_uuid(mountpoint=mountpoint)

    if uuid != '':
        statefile = os.path.basename(__file__)
        statefile_no_ext = os.path.splitext(statefile)[0]
        filename = os.path.join(util.get_home_directory(), f'.polybar-{statefile_no_ext}-{uuid}-state')
        return filename
    else:
        mountpoint = mountpoint.replace('/', '_slash') if mountpoint.endswith('/') else mountpoint.replace('/', '_slash_')
        statefile = os.path.basename(__file__)
        statefile_no_ext = os.path.splitext(statefile)[0]
        filename = os.path.join(util.get_home_directory(), f'.polybar-{statefile_no_ext}{mountpoint}-state')
        return filename

def generate_toggle_script(args):
    toggle_script = os.path.expanduser(args.toggle_script)
    with open(toggle_script, 'w') as f:
        f.write('#/bin/sh\n')
        f.write(f'{f'{os.path.join(util.get_config_directory(), os.path.basename(__file__))}'} --mountpoint "{args.mountpoint}" --unit "{args.unit}" --toggle\n')
    os.chmod(toggle_script, 0o755)

def get_disk_usage(mountpoint: str) -> list:
    """
    Execute df -B 1 against a mount point and return a dictionary with its values
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
            filesystem_dict['pct_used'] = round((filesystem_dict['used'] / (filesystem_dict['used'] + filesystem_dict['free'])) * 100)
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
    mode_count = 3
    parser = argparse.ArgumentParser(description='Get disk info from df(1)')
    parser.add_argument('-m', '--mountpoint', help='The mountpoint to check', required=False)
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-n', '--name', help='For now we need to pass a friendly mountpoint name', required=False)
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    parser.add_argument('-d', '--daemon', action='store_true', help='Daemonize', required=False)
    args = parser.parse_args()

    statefile_name = get_statefile_name(mountpoint=args.mountpoint)
    mode = state.next_state(statefile_name=statefile_name, mode_count=mode_count) if args.toggle else state.read_state(statefile_name=statefile_name)

    # Daemon mode: periodic updates
    if args.daemon:
        # Wait a bit to let Polybar fully initialize
        time.sleep(1)
        while True:
            _, _, _ = util.run_piped_command(f'polybar-msg action filesystem-usage-clickable-{args.name} hook 0')
            time.sleep(2)
        sys.exit(0)
    else:
        disk_info = get_disk_usage(args.mountpoint)

        if disk_info['success']:
            pct_total = f'{disk_info["pct_total"]}%'
            pct_used  = f'{disk_info["pct_used"]}%'
            pct_free  = f'{disk_info["pct_free"]}%'
            total     = util.byte_converter(number=disk_info['total'], unit=args.unit)
            used      = util.byte_converter(number=disk_info['used'], unit=args.unit)
            free      = util.byte_converter(number=disk_info['free'], unit=args.unit)

            if mode == 0:
                output = f'{util.color_title(glyphs.md_harddisk)} {util.color_title(args.mountpoint)} {used} / {total}'
            elif mode == 1:
                output = f'{util.color_title(glyphs.md_harddisk)} {util.color_title(args.mountpoint)} {pct_used} used'
            elif mode == 2:
                output = f'{util.color_title(glyphs.md_harddisk)} {util.color_title(args.mountpoint)} {used} used / {free} free'
            print(output)
            sys.exit(0)
        else:
            output = f'{util.color_title(glyphs.md_harddisk)} {util.color_error(args.mountpoint)} {util.color_error(disk_info["error"])}'
            print(output)
            sys.exit(1)

if __name__ == "__main__":
    main()
