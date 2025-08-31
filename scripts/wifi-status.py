#!/usr/bin/env python3

from pathlib import Path
from polybar import util
import argparse
import os
import re
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

def get_wifi_status(interfaces):
    """
    Execute iwconfig against each interface to get its status
    """

    statuses = []

    for interface in interfaces:
        rc, stdout, stderr = util.run_piped_command(f'iwconfig {interface}')
        if rc == 0:
            if stdout != '':
                match = re.search(r"Signal level=(-?\d+)\s*dBm", stdout)
                if match:
                    status_dict = {
                        'success':   True,
                        'interface': interface,
                        'signal':    int(match.group(1)),
                    }
                else:
                    status_dict = {
                        'success':   False,
                        'interface': interface,
                        'error':     f'regex failure on output',
                    }
            else:
                status_dict = {
                    'success':   False,
                    'interface': interface,
                    'error':     f'no output from iwconfig {interface}',
                }
        else:
            if stderr != '':
                status_dict = {
                    'success':   False,
                    'interface': interface,
                    'error':     stderr.strip(),
                }
            else:
                status_dict = {
                    'success':   False,
                    'interface': interface,
                    'error':     f'non-zero exit code',
                }
        statuses.append(status_dict)
    
    return statuses

def main():
    config_file = os.path.join(Path.cwd(), 'wifi-status.json')
    config, err = util.parse_config_file(config_file)
    if err != '':
        print(f'WiFi Status: {err}')
        sys.exit(1)

    start_colorize = '%{F#F0C674}'
    end_colorize = '%{F-}'
    start_nerdfont = '%{T3}'
    end_nerdfont = '%{T-}'

    parser = argparse.ArgumentParser(description="Get WiFi status from iwconfig(8)")
    parser.add_argument("-i", "--interface", action='append', help="The interface to check; can be used multiple times", required=False)
    args = parser.parse_args()

    if args.interface:
        interfaces = args.interface
    else:
        if len(config['interfaces']) == 0:
            print('WiFi Status: No interfaces defined')
            sys.exit(1)
        else:
            interfaces = config['interfaces']
    
    wifi_statuses = get_wifi_status(interfaces)
    
    output = []
    for status in wifi_statuses:
        if status['success']:
            # add the icon!
            output.append(f'{start_colorize}{status["interface"]}{end_colorize} {status["signal"]} dBm')
        else:
            output.append(f'{start_colorize}{status["interface"]}{end_colorize} {status["error"]}')
    
    print(' | '.join(output))

if __name__ == "__main__":
    main()
