#!/usr/bin/env python3

from polybar import util
import platform
import re
import subprocess
import sys

def get_cpu_usage():
    """
    Execute mpstat'
    """

    binary = 'mpstat'

    # make sure mpstat is installed
    if util.is_binary_installed(binary):
        rc, stdout, stderr = util.run_piped_command(f'{binary} | tail -n 1')
        if rc == 0:
            if stdout != '':
                values = re.split(r'\s+', stdout)

                cpu_dict = {
                    'success': True,
                    'user':    values[3],
                    'nice':    values[4],
                    'sys':     values[5],
                    'iowait':  values[6],
                    'irq':     values[7],
                    'soft':    values[8],
                    'steal':   values[9],
                    'guest':   values[10],
                    'gnice':   values[11],
                    'idle':    values[12]
                }
                
            else:
                cpu_dict = {
                    'success':     False,
                    'error':       f'no output from mpstat'
                }
        else:
            if stderr != '':
                cpu_dict = {
                    'success':     False,
                    'error':       stderr.strip(),
                }
            else:
                cpu_dict = {
                    'success':     False,
                    'error':       'non-zero exit code'
                }
    else:
        cpu_dict = {
            'success':     False,
            'error':       f'please install {binary}'
        }  

    return cpu_dict

def main():
    start_colorize = '%{F#F0C674}'
    end_colorize = '%{F-}'
    start_nerdfont = '%{T3}'
    end_nerdfont = '%{T-}'

    if platform.machine() == 'x86':
        cpu_icon = util.surrogatepass('\udb83\udedf')
    elif platform.machine() == 'x86_64':
        cpu_icon = util.surrogatepass('\udb83\udee0')
    else:
        cpu_icon = '\uf4bc'

    cpu_info = get_cpu_usage()

    if cpu_info['success']:
        cpu_usage = f'{start_colorize}{start_nerdfont}{cpu_icon}{end_nerdfont}{end_colorize} user {cpu_info["user"]}%, sys {cpu_info["sys"]}%, idle {cpu_info["idle"]}%'
    else:
        cpu_usage = f'{start_colorize}{start_nerdfont}{cpu_icon}{end_nerdfont}{end_colorize} {cpu_info["error"]}'

    print(cpu_usage)

if __name__ == "__main__":
    main()
