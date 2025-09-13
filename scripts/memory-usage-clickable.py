#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, state, util
from typing import Any, Dict, List, Optional, NamedTuple
import argparse
import os
import re
import sys
import time

class DIMMInfo(NamedTuple):
    configured_voltage : Optional[str] = None
    data_width         : Optional[int] = 0
    form_factor        : Optional[str] = None
    locator            : Optional[str] = None
    maximum_voltage    : Optional[str] = None
    minimum_voltage    : Optional[str] = None
    part_number        : Optional[str] = None
    serial_number      : Optional[str] = None
    size               : Optional[int] = 0
    speed              : Optional[str] = None
    technology         : Optional[str] = None
    total_width        : Optional[int] = 0
    type               : Optional[str] = None
    volatile_size      : Optional[int] = 0

class MemoryType(NamedTuple):
    success : Optional[bool] = False
    error   : Optional[str] = None
    info    : Optional[List[DIMMInfo]] = None

class MemoryInfo(NamedTuple):
    success     : Optional[bool] = False
    error       : Optional[str]  = None
    total       : Optional[int]  = 0
    used        : Optional[int]  = 0
    free        : Optional[int]  = 0
    shared      : Optional[int]  = 0
    buffers     : Optional[int]  = 0
    cache       : Optional[int]  = 0
    available   : Optional[int]  = 0
    pct_total   : Optional[int]  = 0
    pct_used    : Optional[int]  = 0
    pct_free    : Optional[int]  = 0
    memory_type : Optional[List[MemoryType]] = None

def get_statefile() -> str:
    statefile = os.path.basename(__file__)
    statefile_no_ext = os.path.splitext(statefile)[0]
    return Path.home() / f'.polybar-{statefile_no_ext}-state'

def get_memory_type():
    command = 'sudo dmidecode -t memory'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0 and stdout != '':
        stanzas = re.split(r'^Handle.*', stdout, flags=re.MULTILINE)
        stanzas = [stanza.lstrip().rstrip() for stanza in stanzas if stanza.lstrip().rstrip().startswith('Memory Device')]
        if len(stanzas) > 0:
            dimms = []
            for stanza in stanzas:
                memory_block = {}
                for line in stanza.splitlines():
                    line = line.lstrip().rstrip()
                    if line.startswith('Handle'):
                        continue
                    bits = re.split(r'\s*:\s*', line)
                    if len(bits) == 2:
                        memory_block[util.to_snake_case(bits[0])] = bits[1]
                if len(memory_block.keys()) > 0:
                    data_width = -1
                    size = -1
                    total_width = -1
                    volatile_size = -1

                    if 'data_width' in memory_block and memory_block['data_width'] != '':
                        bits = re.split(r'\s+', memory_block['data_width'])
                        if len(bits) == 2:
                            try:
                                data_width = int(bits[0])
                            except:
                                data_width = -1

                    if 'total_width' in memory_block and memory_block['total_width'] != '':
                        bits = re.split(r'\s+', memory_block['total_width'])
                        if len(bits) == 2:
                            try:
                                total_width = int(bits[0])
                            except:
                                total_width = -1

                    if 'size' in memory_block and memory_block['size'] != '':
                        bits = re.split(r'\s+', memory_block['size'])
                        if len(bits) == 2:
                            try:
                                raw = int(bits[0])
                                if bits[1] == 'MB':
                                    size = int(raw * (1000**2))
                                if bits[1] == 'GB':
                                    size = int(raw * (1000**3))
                            except:
                                size = -1

                    if 'volatile_size' in memory_block and memory_block['volatile_size'] != '':
                        bits = re.split(r'\s+', memory_block['volatile_size'])
                        if len(bits) == 2:
                            try:
                                raw = int(bits[0])
                                if bits[1] == 'MB':
                                    volatile_size = int(raw * (1000**2))
                                if bits[1] == 'GB':
                                    volatile_size = int(raw * (1000**3))
                            except:
                                volatile_size = -1

                    dimms.append(DIMMInfo(
                        configured_voltage = memory_block['configured_voltage'] if 'configured_voltage' in memory_block else 'Unknown',
                        data_width         = data_width,
                        form_factor        = memory_block['form_factor'] if 'form_factor' in memory_block else 'Unknown',
                        locator            = memory_block['locator'] if 'locator' in memory_block else 'Unknown',
                        maximum_voltage    = memory_block['maximum_voltage'] if 'maximum_voltage' in memory_block else 'Unknown',
                        minimum_voltage    = memory_block['minimum_voltage'] if 'minimum_voltage' in memory_block else 'Unknown',
                        part_number        = memory_block['part_number'] if 'part_number' in memory_block else 'Unknown',
                        serial_number      = memory_block['serial_number'] if 'serial_number' in memory_block else 'Unknown',
                        size               = size,
                        speed              = memory_block['speed'] if 'speed' in memory_block else 'Unknown',
                        technology         = memory_block['memory_technology'] if 'memory_technology' in memory_block else 'Unknown',
                        total_width        = total_width,
                        type               = memory_block['type'] if 'type' in memory_block else 'Unknown',
                        volatile_size      = volatile_size,
                    ))
                memory_type = MemoryType(
                    success = True,
                    info    = dimms,
                )
        else:
            memory_type = MemoryType(
                success = False,
                error   = 'no information found about installed memory',
            )
    else:
        if stderr != '':
            memory_type = MemoryType(
                success = False,
                error   = stderr,
            )
        else:
            memory_type = MemoryType(
                success = False,
                error   = f'failed to execute {command}',
            )

    return memory_type

def get_memory_usage():
    """
    Execute free -b -w and return a namedtuple with its values
    """

    command = 'free -b -w | sed -n "2p"'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        if stdout != '':
            values    = re.split(r'\s+', stdout)
            total     = int(values[1])
            shared    = int(values[4])
            buffers   = int(values[5])
            cache     = int(values[6])
            available = int(values[7])
            used      = total - available
            free      = total - used
            pct_total = 100
            pct_used  = int(((total - available) / total) * 100)
            pct_free  = pct_total - pct_used

            mem_info = MemoryInfo(
                success     = True,
                total       = total,
                shared      = shared,
                buffers     = buffers,
                cache       = cache,
                available   = available,
                pct_total   = 100,
                pct_used    = pct_used,
                pct_free    = pct_free,
                used        = used,
                free        = free,
                memory_type = get_memory_type()
            )
        else:
            mem_info = MemoryInfo(
                success = False,
                error   = 'no output from free',
            )
    else:
        if stderr != '':
            mem_info = MemoryInfo(
                success = False,
                error   = stderr,
            )
        else:
            mem_info = MemoryInfo(
                success = False,
                error   = f'failed to execute {command}',
            )

    return mem_info

def main():
    mode_count = 4
    parser = argparse.ArgumentParser(description='Get memory usage from free(1)')
    parser.add_argument('-u', '--unit', help='The unit to use for display', choices=util.get_valid_units(), required=False)
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    parser.add_argument('-i', '--interval', help='The update interval (in seconds)', required=False, default=2, type=int)
    parser.add_argument('-b', '--background', action='store_true', help='Run this script in the background', required=False)
    args = parser.parse_args()

    # Daemon mode: periodic updates
    if args.background:
        # Wait a bit to let Polybar fully initialize
        time.sleep(1)
        while True:
            if not util.polybar_is_running():
                sys.exit(0)
            _, _, _ = util.run_piped_command('polybar-msg action memory-usage-clickable hook 0')
            time.sleep(args.interval)
        sys.exit(0)
    else:
        if args.toggle:
            mode = state.next_state(statefile=get_statefile(), mode_count=mode_count)
        else:
            mode = state.read_state(statefile=get_statefile())

        memory_info = get_memory_usage()

        if memory_info.success:
            pct_total = f'{memory_info.pct_total}%'
            pct_used  = f'{memory_info.pct_used}%'
            pct_free  = f'{memory_info.pct_free}%'
            total     = util.byte_converter(number=memory_info.total, unit=args.unit)
            used      = util.byte_converter(number=memory_info.used, unit=args.unit)
            free      = util.byte_converter(number=memory_info.free, unit=args.unit)

            if mode == 0:
                output = f'{util.color_title(glyphs.fa_memory)} {used} / {total}'
            elif mode == 1:
                output = f'{util.color_title(glyphs.fa_memory)} {pct_used} used'
            elif mode == 2:
                output = f'{util.color_title(glyphs.fa_memory)} {used} used / {free} free'
            elif mode == 3:
                output = f'{util.color_title(glyphs.fa_memory)} {len(memory_info.memory_type.info)} x {util.byte_converter(memory_info.memory_type.info[0].size, unit='G', use_int=True)} {memory_info.memory_type.info[0].data_width}bit {memory_info.memory_type.info[0].form_factor} @ {memory_info.memory_type.info[0].speed}'
            print(output)
            sys.exit(0)
        else:
            output = f'{util.color_title(glyphs.fa_memory)} {util.color_error(memory_info.error)}'
            print(output)
            sys.exit(1)

if __name__ == "__main__":
    main()
