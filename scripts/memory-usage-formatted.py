#!/usr/bin/env python3

from polybar import glyphs, util
import argparse
import re
import sys

def get_memory_usage():
    """
    Execute free -b -w and return a dictionary with its values
    """

    rc, stdout, stderr = util.run_piped_command('free -b -w | sed -n "2p"')
    if rc == 0:
        if stdout != '':
            values = re.split(r'\s+', stdout)
            mem_dict = {
                'success'   : True,
                'total'     : int(values[1]),
                'shared'    : int(values[4]),
                'buffers'   : int(values[5]),
                'cache'     : int(values[6]),
                'available' : int(values[7]),
                'pct_total' : 100,
            }
            # used = total - available
            mem_dict['used'] = mem_dict['total'] - mem_dict['available']
            mem_dict['free'] = mem_dict['total'] - mem_dict['used']
            # percent_used = (total - available) / total * 100
            mem_dict['pct_used'] = round(((mem_dict['total'] - mem_dict['available']) / mem_dict['total']) * 100)
            mem_dict['pct_free'] = mem_dict['pct_total'] - mem_dict['pct_used']

        else:
            mem_dict = {
                'success': False,
                'error'  : 'no output from free'
            }
    else:
        if stderr != '':
            mem_dict = {
                'success': False,
                'error'  : stderr.strip(),
            }
        else:
            mem_dict = {
                'success': False,
                'error'  : 'non-zero exit code'
            }

    return mem_dict

def main():
    valid_tokens = ['^pct_total', '^pct_used', '^pct_free', '^total', '^used', '^free']
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-f', '--format', help=f'Output format, e.g., {{^free / ^total}}; valid tokens are: {', '.join(valid_tokens)} ', required=False, default='{^free / ^total}')
    args = parser.parse_args()

    memory_info = get_memory_usage()

    if memory_info['success']:
        token_map = {
            '^pct_total': f'{memory_info["pct_total"]}%',
            '^pct_used' : f'{memory_info["pct_used"]}%',
            '^pct_free': f'{memory_info["pct_free"]}%',
            '^total': util.byte_converter(number=memory_info['total'], unit=args.unit),
            '^used': util.byte_converter(number=memory_info['used'], unit=args.unit),
            '^free': util.byte_converter(number=memory_info['free'], unit=args.unit),
        }

        # For when the format is blank
        if not args.format or args.format == '':
            args.format = '{^used / ^total}'

        if args.format and args.format != '':
            output = args.format.replace('{','').replace('}', '')
            valid = []
            invalid = []
            tokens = re.findall(r"\^\w+", args.format)
            for token in tokens:
                if token in valid_tokens:
                    valid.append(token)
                else:
                    invalid.append(token)
            if len(invalid) > 0 or len(tokens) == 0:
                error = f'Invalid format: {args.format}'
                print(f'{util.color_title(glyphs.md_harddisk)} {util.color_error(error)}')
                sys.exit(1)

            for idx, token in enumerate(valid):
                output = output.replace(token, token_map[token])

    if memory_info['success']:
        memory_usage = f'{util.color_title(glyphs.md_memory)} {output}'
    else:
        memory_usage = f'{util.color_title(glyphs.md_memory)} {util.color_error(memory_info['error'])}'

    print(memory_usage)

if __name__ == "__main__":
    main()
