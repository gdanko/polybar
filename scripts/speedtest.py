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

def get_icon(speed: float=0.0) -> str:
    # 100000000 is 100 mbit
    if speed < 100000000:
        return glyphs.md_speedometer_slow
    elif speed >= 100000000 and speed < 500000000:
        return glyphs.md_speedometer_medium
    elif speed >= 500000000:
        return glyphs.md_speedometer_fast

def main():
    speedtest_data = {
        'down': {
            'success': False,
            'speed'  : 0.0,
            'error'  : None,
        },
        'up': {
            'success': False,
            'speed'  : 0.0,
            'error'  : None,
        }
    }

    errors = []
    tester = speedtest.Speedtest(secure=True)

    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true', help='Test upload speed', required=False)
    parser.add_argument('--upload', action='store_true', help='Test upload speed', required=False)
    parser.add_argument('--bytes', action='store_true', help='Use bytes instead of bits')
    args = parser.parse_args()

    if not args.download and not args.upload:
        print(f'{util.color_title(glyphs.md_speedometer_slow)} {util.color_error("please specify --download and/or --upload")}')
        sys.exit(1)

    if args.download:
        try:
            tester.download()
            speedtest_data['down']['success'] = True
            speedtest_data['down']['speed'] = tester.results.download
        except Exception as e:
            errors.append(e)

    if args.upload:
        try:
            tester.upload(pre_allocate=False)
            speedtest_data['up']['success'] = True
            speedtest_data['up']['speed'] = tester.results.upload
        except Exception as e:
            errors.append(e)

    output = []
    if speedtest_data['down']['success']:
        output.append(f'{glyphs.cod_arrow_small_down}{util.network_speed(tester.results.download, args.bytes)}')

    if speedtest_data['up']['success']:
        output.append(f'{glyphs.cod_arrow_small_up}{util.network_speed(tester.results.upload, args.bytes)}')

    if len(output) == 0:
         print(f'{util.color_title(glyphs.md_speedometer_fast)} {util.color_error('All tests failed')}')
         sys.exit(1)

    # Determine the icon based on average up/down speed
    if speedtest_data['down']['success'] and speedtest_data['up']['success']:
        icon = get_icon( (speedtest_data['down']['speed'] + speedtest_data['up']['speed']) / 2 )

    elif speedtest_data['down']['success'] and not speedtest_data['up']['success']:
        icon = get_icon( speedtest_data['down']['speed'] )

    elif not speedtest_data['down']['success'] and speedtest_data['up']['success']:
        icon = get_icon( speedtest_data['up']['speed'] )

    if len(output) > 0:
        print(f'{util.color_title(icon)} {' '.join(output)}')
    else:
        print(f'{util.color_title(icon)} {util.color_error('All tests failed')}')

if __name__ == '__main__':
    main()
