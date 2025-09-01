#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, util
import argparse
import os
import re
import sys

def get_status_icon(signal):
    """
    Return a wifi icon based on signal strength
    """

    if signal >= 30:
        return glyphs.md_wifi_strength_4
    elif signal >= -50:
        return glyphs.md_wifi_strength_3
    elif signal >= -60:
        return glyphs.md_wifi_strength_2
    elif signal >= -70:
        return glyphs.md_wifi_strength_1
    elif signal >= -80:
        return glyphs.md_wifi_strength_outline
    elif signal >= -90:
        return glyphs.md_wifi_strength_alert_outline

def get_wifi_status(interfaces):
    """
    Execute iwconfig against each interface to get its status
    """

    binary = 'iwconfig'
    statuses = []

    if util.is_binary_installed(binary):
        for interface in interfaces:
            rc, stdout, stderr = util.run_piped_command(f'{binary} {interface}')
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
    else:
        status_dict = {
            'success':   False,
            'interface': '',
            'error':     f'please install {binary}'
        }
        statuses.append(status_dict)
    
    return statuses

def main():
    config_file = util.get_config_file_path('wifi-status.json')
    config, err = util.parse_config_file(config_file)
    if err != '':
        print(f'WiFi Status: {err}')
        sys.exit(1)

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
            wifi_icon = get_status_icon(status["signal"])
            output.append(f'{util.color_title(wifi_icon)} {status["interface"]} {status["signal"]} dBm')
        else:
            wifi_icon = glyphs.md_wifi_strength_alert_outline
            output.append(f'{util.color_title(wifi_icon)} {status["interface"]} {status["error"]}')
    
    print(' | '.join(output))

if __name__ == "__main__":
    main()
