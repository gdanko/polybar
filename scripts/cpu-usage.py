#!/usr/bin/env python3

from polybar import glyphs, util
import platform
import re
import subprocess
import sys

def get_cpu_usage():
    """
    Execute mpstat'
    """

    if platform.machine() == 'x86':
        icon = glyphs.md_cpu_32_bit
    elif platform.machine() == 'x86_64':
        icon = glyphs.md_cpu_64_bit
    else:
        icon = glyphs.oct_cpu

    binary = 'mpstat'

    # make sure mpstat is installed
    if util.is_binary_installed(binary):
        rc, stdout, stderr = util.run_piped_command(f'{binary} | tail -n 1')
        if rc == 0:
            if stdout != '':
                values = re.split(r'\s+', stdout)

                cpu_dict = {
                    'success' : True,
                    'icon'    : icon,
                    'user'    : values[3],
                    'nice'    : values[4],
                    'sys'     : values[5],
                    'iowait'  : values[6],
                    'irq'     : values[7],
                    'soft'    : values[8],
                    'steal'   : values[9],
                    'guest'   : values[10],
                    'gnice'   : values[11],
                    'idle'    : values[12]
                }

            else:
                cpu_dict = {
                    'success': False,
                    'error'  : f'no output from mpstat',
                    'icon'   : icon,
                }
        else:
            if stderr != '':
                cpu_dict = {
                    'success': False,
                    'error'  : stderr.strip(),
                    'icon'   : icon,
                }
            else:
                cpu_dict = {
                    'success': False,
                    'error'  : 'non-zero exit code',
                    'icon'   : icon,
                }
    else:
        cpu_dict = {
            'success': False,
            'error'  : f'please install the sysstat package',
            'icon'   : icon,
        }  

    return cpu_dict

def main():
    cpu_info = get_cpu_usage()

    if cpu_info['success']:
        print(f'{util.color_title(cpu_info["icon"])} user {cpu_info["user"]}%, sys {cpu_info["sys"]}%, idle {cpu_info["idle"]}%')
        sys.exit(0)
    else:
        print(f'{util.color_title(cpu_info["icon"])} {util.color_error(cpu_info["error"])}')
        sys.exit(1)

if __name__ == "__main__":
    main()
