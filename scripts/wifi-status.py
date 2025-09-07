#!/usr/bin/env python3

from polybar import glyphs, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
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

class WifiStatus(NamedTuple):
    success   : Optional[bool] = False
    error     : Optional[str]  = None
    interface : Optional[str]  = None
    signal    : Optional[int]  = 0

def get_wifi_status(interface):
    """
    Execute iwconfig against each interface to get its status as a namedtuple
    """

    statuses = []
    command = f'iwconfig {interface}'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        if stdout != '':
            match = re.search(r"Signal level=(-?\d+)\s*dBm", stdout)
            if match:
                wifi_status = WifiStatus(
                    success   = True,
                    interface = interface,
                    signal    = int(match.group(1)),
                )
            else:
                wifi_status = WifiStatus(
                    success   = False,
                    interface = interface,
                    error     = f'regex failure on output',
                )
        else:
            status_dict = {
                'success':   False,
                'interface': interface,
                'error':     f'no output from iwconfig {interface}',
            }
    else:
        if stderr != '':
            wifi_status = WifiStatus(
                success   = False,
                interface = interface,
                error     = stderr,
            )
        else:
            wifi_status = WifiStatus(
                success   = False,
                interface = interface,
                error     = f'failed to execute {command}',
            )
    
    return wifi_status

def main():
    parser = argparse.ArgumentParser(description="Get WiFi status from iwconfig(8)")
    parser.add_argument("-i", "--interface", help="The interface to check", required=True)
    args = parser.parse_args()
    
    wifi_status = get_wifi_status(args.interface)

    if wifi_status.success:
        wifi_icon = get_status_icon(wifi_status.signal)
        print(f'{util.color_title(wifi_icon)} {wifi_status.interface} {wifi_status.signal} dBm')
        sys.exit(0)
    else:
        wifi_icon = glyphs.md_wifi_strength_alert_outline
        print(f'{util.color_title(wifi_icon)} {wifi_status.interface} {wifi_status.error}')
        sys.exit(1)

if __name__ == '__main__':
    main()
