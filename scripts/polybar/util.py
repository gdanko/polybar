from pathlib import Path
from pprint import pprint as pp
from typing import List, Tuple, Optional, Union
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys

modules = ['psutil']
missing = []

for module in modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    error_exit(icon=glyphs.md_network_off_outline, message=f'Please install via pip: {", ".join(missing)}')
    sys.exit(1)

def pprint(input):
    pp(input)

def run_piped_command(command: str=None, background: bool=False) -> Union[
    Tuple[int, bytes, bytes],  # blocking mode
    List[subprocess.Popen]     # background mode
]:
    """
    Run a shell-like command with pipes using subprocess.

    Args:
        command (str): The pipeline command, e.g. "echo hi | grep h".
        background (bool): If True, run in background (detached).

    Returns:
        - If background=False: (return_code, stdout, stderr)
        - If background=True : list of Popen objects (pipeline)
    """
    # Split pipeline into stages
    parts = [shlex.split(cmd.strip()) for cmd in command.split('|')]
    processes = []
    prev_stdout = None

    for i, part in enumerate(parts):
        try:
            proc = subprocess.Popen(
                part,
                stdin=prev_stdout,
                stdout=subprocess.PIPE if not background else subprocess.DEVNULL,
                stderr=subprocess.PIPE if not background and i == len(parts) - 1 else subprocess.DEVNULL,
                preexec_fn=os.setpgrp if background else None
            )

            if prev_stdout:
                prev_stdout.close()
            prev_stdout = proc.stdout
            processes.append(proc)
        except FileNotFoundError as e:
            return 1, None, e

    if background:
        # Don't wait; return process list so caller can manage if needed
        return processes

    # Foreground (blocking) mode
    stdout, stderr = processes[-1].communicate()
    for p in processes[:-1]:
        p.wait()

    return processes[-1].returncode, stdout.decode().strip(), stderr.decode().strip()

def polybar_is_running() -> bool:
    rc, stdout, _ = run_piped_command('pgrep -x polybar')
    return True if rc == 0 and stdout != '' else False

def process_is_running(name: str=None, full: bool=False):
    flag = 'f' if full else 'x'
    command = f'pgrep -{flag} "{name}"'
    rc, stdout, stderr = run_piped_command(command)
    if rc == 0 and stdout != '':
        pids = stdout.split('\n')
        return True, pids
    else:
        return False, []

def surrogatepass(code):
    return code.encode('utf-16', 'surrogatepass').decode('utf-16')

def pad_float(number: int=0) -> str:
    """
    Pad a float to two decimal places.
    """
    return '{:.2f}'.format(float(number))

def get_valid_units() -> list:
    """
    Return a list of valid storage units
    """
    return ['K', 'Ki', 'M', 'Mi', 'G', 'Gi', 'T', 'Ti', 'P', 'Pi', 'E', 'Ei', 'Z', 'Zi', 'auto']

def network_speed(number: int=0, bytes: bool=False, no_suffix: bool=False) -> str:
    """
    Intelligently determine network speed
    """
    # test this with dummy numbers
    suffix = 'iB/s' if bytes else 'bit/s'

    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if abs(number) < 1024.0:
            if bytes:
                return f'{round(number / 8, 2)} {unit}{suffix}'
            return f'{round(number, 2)} {unit}{suffix}'
        number = number / 1024

def byte_converter(number: int=0, unit: Optional[str] = None, use_int: bool=False) -> str:
    """
    Convert bytes to the given unit.
    """
    if unit is None:
        unit = 'auto'
    suffix = 'B'

    if unit == 'auto':
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi']:
            if abs(number) < 1024.0:
                return f'{pad_float(number)} {unit}{suffix}'
            number = number / 1024
        return f'{pad_float(number)} Yi{suffix}'
    else:
        prefix = unit[0]
        divisor = 1000
        if len(unit) == 2 and unit.endswith('i'):
            divisor = 1024

        prefix_map = {'K': 1, 'Ki': 1, 'M': 2, 'Mi': 2,  'G': 3, 'Gi': 3, 'T': 4, 'Ti': 4, 'P': 5, 'Pi': 5, 'E': 6, 'Ei': 6, 'Z': 7, 'Zi': 7}
        if unit in prefix_map.keys():
            if use_int:
                return f'{int(number / (divisor ** prefix_map[prefix]))}{unit}{suffix}'
            else:
                return f'{pad_float(number / (divisor ** prefix_map[prefix]))} {unit}{suffix}'
        else:
            return f'{number} {suffix}'

def file_exists(filename: str='') -> bool:
    return True if (os.path.exists(filename) and os.path.isfile(filename)) else False

def file_is_executable(filename: str='') -> bool:
    return True if os.access(filename, os.X_OK) else False

def get_home_directory() -> str:
    return Path.home()

def get_config_directory() -> str:
    return os.path.join(
        Path.home(),
        '.config',
        'polybar',
    )

def get_script_directory() -> str:
    return os.path.join(
        get_config_directory(),
        'scripts',
    )

def parse_config_file(filename: str='', required_keys: list=[]):
    # Does the file exist?
    if not file_exists(filename):
        return {}, f'{filename} does not exist'

    # Can we parse the JSON?
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
    except Exception as e:
        return {}, e

    # Check for missing required keys
    if len(required_keys) > 0:
        missing = []
        for required_key in required_keys:
            if not required_key in config:
                missing.append(required_key)
        if len(missing) > 0:
            return {}, f'required keys missing from config: {','.join(missing)}'

    return config, ''

def is_binary_installed(binary_name: str) -> bool:
    return shutil.which(binary_name) is not None

def missing_binaries(binaries: list=[]):
    missing = []
    for binary in binaries:
        if not is_binary_installed(binary):
            missing.append(binary)
    return missing

def parse_json_string(input: str=''):
    try:
        json_data = json.loads(input)
        return json_data, None
    except Exception as err:
        return None, err, 

def color_title(text: str='') -> str:
    start_color_title = '%{F#F0C674}'
    end_color_title = '%{F-}'
    return f'{start_color_title}{text}{end_color_title}'

def color_error(text: str='') -> str:
    start_color_title = '%{F#707880}'
    end_color_title = '%{F-}'
    return f'{start_color_title}{text}{end_color_title}'

def network_is_reachable():
    host = '8.8.8.8'
    port = 53
    timeout = 3
    try:
        socket.setdefaulttimeout(timeout)
        with socket.create_connection((host, port)):
            return True
    except OSError:
        return False

def to_snake_case(s: str) -> str:
    # Replace anything that's not a letter or number with underscore
    s = re.sub(r'[^0-9a-zA-Z]+', '_', s)
    # Add underscore between camelCase or PascalCase boundaries
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    # Collapse multiple underscores into one
    s = re.sub(r'_+', '_', s)
    # Strip leading/trailing underscores, lowercase
    return s.strip('_').lower()

def is_worker_running(lockfile: Path) -> bool:
    """
    Determine if a worker for a given module is running
    """

    if not lockfile.exists():
        return False
    try:
        pid = int(lockfile.read_text())
        proc = psutil.Process(pid)
        cmdline = proc.cmdline()
        # Only consider it running if it's our script with 'worker' arg
        if __file__ in cmdline[0] and 'worker' in cmdline:
            return True
        else:
            lockfile.unlink()
            return False
    except (ValueError, FileNotFoundError, psutil.NoSuchProcess, PermissionError):
        # Stale lockfile
        try:
            lockfile.unlink()
        except Exception:
            pass
        return False

def error_exit(icon: str=None, message: str=None):
    print(f'{color_title(icon)} {color_error(message)}')
    sys.exit(1)

def check_network():
    if not network_is_reachable():
        # How to immport glyphs?
        error_exit(
            icon    = surrogatepass('\udb83\udc9c'),
            message = 'the network is unreachable',
        )

def validate_requirements(required: list=[]):
    missing = []

    for module in required:
        if importlib.util.find_spec(module) is None:
            missing.append(module)

    if missing:
        icon = surrogatepass('\udb80\udc26')
        error_exit(
            icon    = icon,
            message = f'Please install via pip: {", ".join(missing)}',
        )
