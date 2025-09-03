#!/usr/bin/env python3

from polybar import glyphs, state, util
import argparse
import os
import re
import sys

# memory-usage-clickable
# This is a version of the memory-usage.py script that has a > 1 output formats.
# Clicking on the item in bar will toggle the output.
# This is experimental!

def get_statefile_name() -> str:
    statefile = os.path.basename(__file__)
    statefile_no_ext = os.path.splitext(statefile)[0]
    return os.path.join(
        util.get_home_directory(),
        f'.polybar-{statefile_no_ext}-state'
    )

def get_memory_usage():
    """
    Execute free -b -w and return a dictionary with its values
    """

    rc, stdout, stderr = util.run_piped_command('free -b -w | sed -n "2p"')
    if rc == 0:
        if stdout != '':
            values = re.split(r'\s+', stdout)
            mem_dict = {
                'success'   : True,
                'total'     : int(values[1]),
                'shared'    : int(values[4]),
                'buffers'   : int(values[5]),
                'cache'     : int(values[6]),
                'available' : int(values[7]),
                'pct_total' : 100,
            }
            # used = total - available
            mem_dict['used'] = mem_dict['total'] - mem_dict['available']
            mem_dict['free'] = mem_dict['total'] - mem_dict['used']
            # percent_used = (total - available) / total * 100
            mem_dict['pct_used'] = round(((mem_dict['total'] - mem_dict['available']) / mem_dict['total']) * 100)
            mem_dict['pct_free'] = mem_dict['pct_total'] - mem_dict['pct_used']

        else:
            mem_dict = {
                'success': False,
                'error'  : 'no output from free'
            }
    else:
        if stderr != '':
            mem_dict = {
                'success': False,
                'error'  : stderr.strip(),
            }
        else:
            mem_dict = {
                'success': False,
                'error'  : 'non-zero exit code'
            }

    return mem_dict

def main():
    mode_count = 3
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    args = parser.parse_args()

    statefile_name = get_statefile_name()

    memory_info = get_memory_usage()
    mode = state.next_state(statefile_name=statefile_name, mode_count=mode_count) if args.toggle else state.read_state(statefile_name=statefile_name)

    if memory_info['success']:
        pct_total = f'{memory_info["pct_total"]}%'
        pct_used  = f'{memory_info["pct_used"]}%'
        pct_free  = f'{memory_info["pct_free"]}%'
        total     = util.byte_converter(number=memory_info['total'], unit=args.unit)
        used      = util.byte_converter(number=memory_info['used'], unit=args.unit)
        free      = util.byte_converter(number=memory_info['free'], unit=args.unit)

        if mode == 0:
            memory_usage = f'{util.color_title(glyphs.md_memory)} {used} / {total}'
        elif mode == 1:
            memory_usage = f'{util.color_title(glyphs.md_memory)} {pct_used} used'
        elif mode == 2:
            memory_usage = f'{util.color_title(glyphs.md_memory)} {used} used / {free} free'
    else:
        memory_usage = f'{util.color_title(glyphs.md_memory)} {util.color_error(memory_info['error'])}'
    
    print(memory_usage)

if __name__ == "__main__":
    main()
