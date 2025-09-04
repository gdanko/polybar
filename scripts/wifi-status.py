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

def get_wifi_status(interface):
    """
    Execute iwconfig against each interface to get its status
    """

    binary = 'iwconfig'
    statuses = []

    if util.is_binary_installed(binary):
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
    else:
        status_dict = {
            'success':   False,
            'interface': '',
            'error':     f'please install {binary}'
        }
    
    return status_dict

def main():
    parser = argparse.ArgumentParser(description="Get WiFi status from iwconfig(8)")
    parser.add_argument("-i", "--interface", help="The interface to check", required=True)
    args = parser.parse_args()
    
    wifi_status = get_wifi_status(args.interface)

    if wifi_status['success']:
        wifi_icon = get_status_icon(wifi_status['signal'])
        print(f'{util.color_title(wifi_icon)} {wifi_status["interface"]} {wifi_status["signal"]} dBm')
        sys.exit(0)
    else:
        wifi_icon = glyphs.md_wifi_strength_alert_outline
        print(f'{util.color_title(wifi_icon)} {wifi_status["interface"]} {wifi_status["error"]}')
        sys.exit(1)

if __name__ == "__main__":
    main()
