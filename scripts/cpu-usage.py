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
    try:
        # Run df -k for the specified mount point
        result = subprocess.run(['mpstat'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) != 4:
            print('CPU Error!')
        
        bits = re.split(r'\s+', lines[3])

        cpu_dict = {
            'user':   bits[3],
            'nice':   bits[4],
            'sys':    bits[5],
            'iowait': bits[6],
            'irq':    bits[7],
            'soft':   bits[8],
            'steal':  bits[9],
            'guest':  bits[10],
            'gnice':  bits[11],
            'idle':   bits[12]
        }

        return cpu_dict
            
    except subprocess.CalledProcessError as e:
        print(f"Error running mpstat: {e}", file=sys.stderr)
        sys.exit(1)

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

    cpu_usage = f'{start_colorize}{start_nerdfont}{cpu_icon}{end_nerdfont}{end_colorize} user {cpu_info["user"]}%, sys {cpu_info["sys"]}%, idle {cpu_info["idle"]}%'
    print(cpu_usage)

if __name__ == "__main__":
    main()
