#!/usr/bin/env python3

from polybar import glyphs, util
import argparse
import re

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
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    args = parser.parse_args()

    memory_info = get_memory_usage()

    if memory_info['success']:
        memory_usage = f'{util.color_title(glyphs.md_memory)} {util.byte_converter(memory_info["used"], unit=args.unit)} / {util.byte_converter(memory_info["total"], unit=args.unit)}'
    else:
        memory_usage = f'{util.color_title(glyphs.md_memory)} {util.color_error(memory_info['error'])}'

    print(memory_usage)

if __name__ == "__main__":
    main()
