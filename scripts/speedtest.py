#!/usr/bin/env python3
from pathlib import Path
from polybar import glyphs, util
from typing import Any, Dict, List, Optional, NamedTuple
import click
import logging
import re
import subprocess

try:
    import speedtest
except ImportError:
    print(f'Please install speedtest-cli via pip')
    sys.exit(1)

try:
    import click
except ImportError:
    print(f'Please install click via pip')
    sys.exit(1)

class TestResult(NamedTuple):
    success : Optional[bool] = False
    error   : Optional[str]  = None
    bps     : Optional[int]  = -1

TMPFILE = Path.home() / ".polybar-speedtest-result.txt"
LOGFILE = Path.home() / ".polybar-speedtest-result.log"
LOADING = f'{util.color_title(glyphs.fa_arrow_rotate_right)} Speedtest running...'

logging.basicConfig(
    filename = LOGFILE,
    filemode = 'a', # 'a' = append, 'w' = overwrite
    format   = '%(asctime)s [%(levelname)-5s] - %(message)s',
    level    = logging.INFO      # Minimum level to log
)

def get_icon(speed: int=0) -> str:
    # 100000000 is 100 mbit
    if speed < 100000000:
        return glyphs.md_speedometer_slow
    elif speed >= 100000000 and speed < 500000000:
        return glyphs.md_speedometer_medium
    elif speed >= 500000000:
        return glyphs.md_speedometer_fast

def get_bits_per_second(text: str=None, key: str=None):
    unit_map = {
        'Kbit/s': 1_000,
        'Mbit/s': 1_000_000,
        'Gbit/s': 1_000_000_000,
    }

    try:
        match = re.search(rf"{key}:\s+([\d.]+)\s+([KMG]bit/s)", text)
        if match:
            value = float(match.group(1))
            unit  = match.group(2)
            return int(value * unit_map[unit])
        return None
    except:
        return None
    
def parse_speedtest_output(output: str=None, download: bool=False, upload: bool=False, bytes: bool=False) -> str:
    """
    Parse speedtest-cli output and return formatted string
    """
    logging.info(f'[in parse_speedtest_output] output={output.replace("\n", " | ")}, download={download}, upload={upload}, bytes={bytes}')

    icon = glyphs.md_speedometer_slow

    if download:
        download_speed = get_bits_per_second(output, 'Download')
    
    if upload:
        upload_speed = get_bits_per_second(output, 'Upload')
    
    if download and upload:
        if download_speed and upload_speed:
            icon = get_icon(speed=int((download_speed + upload_speed) / 2))
    elif download and not upload:
        if download_speed:
            icon = get_icon(speed=download_speed)
    elif upload and not download:
        if upload_speed:
            icon = get_icon(speed=upload_speed)
    
    parts = []
    if download:
        if download_speed:
            parts.append(f'{glyphs.cod_arrow_small_down}{util.network_speed(number=download_speed, bytes=bytes)}')
    
    if upload:
        if upload_speed:
            parts.append(f'{glyphs.cod_arrow_small_up}{util.network_speed(number=upload_speed, bytes=bytes)}')
    
    if len(parts) > 0:
        return f'{util.color_title(icon)} {' '.join(parts)}'
    else:
        return f'{util.color_title(icon)} {util.color_error("All tests failed")}'

def run_speedtest(download=True, upload=True, bytes=False):
    """
    Run speedtest-cli and save results to TMPFILE
    """
    logging.info(f'[in run_speedtest] download={download}, upload={upload}, bytes={bytes}')

    command = [
        'speedtest-cli',
        '--simple',
    ]

    if not download:
        command.append('--no-download')

    if not upload:
        command.append('--no-upload')
    
    logging.info(f'[in run_speedtest] command: "{" ".join(command)}"')

    try:
        output = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            text=True
        )

        logging.info(f'[in run_speedtest] success! output={output.replace("\n", " | ")}')
        
        module_output = parse_speedtest_output(output=output, download=download, upload=upload, bytes=bytes)
        logging.info(f'[in run_speedtest] output received: {module_output}')
        TMPFILE.write_text(module_output)
    except Exception as e:
        logging.error(f'[in run_speedtest] error! error={e}')
        TMPFILE.write_text(f'{glyphs.oct_alert} {util.color_error(e)}')
    finally:
        subprocess.run(['polybar-msg', 'action', '#speedtest.hook.0'])

@click.group()
def cli():
    """Polybar Speedtest CLI"""
    pass

@cli.command()
def show():
    """
    Show last result (hook-0)
    """
    if TMPFILE.exists():
        logging.info(f'[in show] TMPFILE exists')
        print(TMPFILE.read_text().strip())
    else:
        logging.info(f'[in show] TMPFILE does not exist')
        print(LOADING)

@cli.command()
@click.option("--download", is_flag=True, help="Run only download test")
@click.option("--upload", is_flag=True, help="Run only upload test")
@click.option("--bytes", is_flag=True, help="Display output using bytes instead of bits")
@click.option("--background", is_flag=True, help="Run this plugin in the background")
@click.option("--interval", is_flag=True, help="When in the background, re-run every x seconds")
def run(download, upload, bytes, background, interval):
    """
    Run speedtest in the background
    """

    TMPFILE.write_text(LOADING)

    # Default to both if neither flag is set
    if not upload and not download:
        upload = download = True

    logging.info('Starting')
    logging.info(f'[in run] download={download}, upload={upload}, bytes={bytes}')

    # Spawn fully detached background process
    subprocess.Popen(
        [__file__,  'worker', f'{int(download)}', f'{int(upload)}', f'{int(bytes)}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True
    )

    subprocess.run(["polybar-msg", "action", "#speedtest.hook.0"])

@cli.command(name="worker")
@click.argument("download", type=int)
@click.argument("upload", type=int)
@click.argument("bytes", type=int)
def worker(download, upload, bytes):
    """
    Internal worker
    """
    logging.info(f'[in worker] download={download}, upload={upload}, bytes={bytes}')
    run_speedtest(download=bool(download), upload=bool(upload), bytes=bool(bytes))

if __name__ == "__main__":
    cli()
