#!/usr/bin/env python3

from polybar import util
import argparse
import subprocess
import sys

def get_memory_usage():
    """
    Execute free -b -w and return a dictionary with its values
    """
    try:
        # Run free -b -w
        result = subprocess.run(['free', '-b', '-w'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        if len(lines) != 3:
            return {}

        # Split header and values
        values = lines[1].split()

        # Construct simplified dict
        mem_dict = {
            'total':     int(values[1]),
            'used':      int(values[2]),
            'free':      int(values[3]),
            'shared':    int(values[4]),
            'buffers':   int(values[5]),
            'cache':     int(values[6]),
            'available': int(values[7]),
        }
        return mem_dict
            
    except subprocess.CalledProcessError as e:
        print(f"Error running free -b -w: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    start_colorize = '%{F#F0C674}'
    end_colorize = '%{F-}'
    start_nerdfont = '%{T3}'
    end_nerdfont = '%{T-}'
    memory_icon = util.surrogatepass('\udb80\udf5b') # md_memory

    memory_info = get_memory_usage()
    memory_usage = f'{start_colorize}{start_nerdfont}{memory_icon}{end_nerdfont}{end_colorize} {util.byte_converter(memory_info["used"])} / {util.byte_converter(memory_info["total"])}'
    print(memory_usage)

if __name__ == "__main__":
    main()
