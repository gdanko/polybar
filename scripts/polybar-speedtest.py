#!/usr/bin/env python3

from polybar import glyphs, util
import argparse
import importlib
import os
import sys

try:
    import speedtest
except ImportError:
    print(f'Please install speedtest-cli via pip')
    sys.exit(1)

def get_formatted_speed(s,bytes=False):
    unit = ''
    if s > 1024**3:
        s = s / 1024**3
        unit = 'G'
    elif s > 1024**2:
        s = s / 1024**2
        unit = 'M'
    elif s > 1024:
        s = s / 1024
        unit = 'K'
    if bytes:
        return f'{(s/8):.2f} {unit}iB/s'
    return f'{s:.2f} {unit}bps'

def main():
    output = []
    s = speedtest.Speedtest()

    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true', help='Test upload speed', required=False)
    parser.add_argument('--upload', action='store_true', help='Test upload speed', required=False)
    parser.add_argument('--bytes', action='store_true', help='Use bytes instead of bits')
    args= parser.parse_args()

    if not args.download and not args.upload:
        print(f'{util.color_title(glyphs.md_speedometer_slow)} {util.color_error("please specify --download and/or --upload")}')
        sys.exit(1)

    if args.download:
        s.download()
        output.append(f'{glyphs.cod_arrow_small_down} {get_formatted_speed(s.results.download, args.bytes)}')

    if args.upload:
        s.upload(pre_allocate=False)
        output.append(f'{glyphs.cod_arrow_small_up} {get_formatted_speed(s.results.upload, args.bytes)}')
    
    print(f'{util.color_title(glyphs.md_speedometer_fast)} {' '.join(output)}')

if __name__ == '__main__':
    main()
