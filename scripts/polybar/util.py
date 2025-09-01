from pathlib import Path
from pprint import pprint as pp
from typing import Optional
import json
import os
import shlex
import shutil
import subprocess

def pprint(input):
    pp(input)

def run_piped_command(command: str):
    """
    Run a shell-like command with pipes using subprocess.
    Returns (return_code, stdout, stderr).
    """
    # Split pipeline parts
    parts = [shlex.split(cmd.strip()) for cmd in command.split('|')]
    
    processes = []
    prev_stdout = None
    
    # Create subprocesses for each stage
    for i, part in enumerate(parts):
        proc = subprocess.Popen(
            part,
            stdin=prev_stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if i == len(parts) - 1 else subprocess.PIPE
        )
        
        if prev_stdout:
            prev_stdout.close()  # Allow upstream process to receive SIGPIPE
        prev_stdout = proc.stdout
        processes.append(proc)

    # Get output from the last process
    stdout, stderr = processes[-1].communicate()
    
    # Wait for all processes
    for p in processes[:-1]:
        p.wait()

    return processes[-1].returncode, stdout.decode(), stderr.decode()

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

def byte_converter(number: int=0, unit: Optional[str] = None) -> str:
    """
    Convert bytes to the given unit.
    """
    if unit is None:
        unit = 'auto'
    suffix = 'B'

    if unit == 'auto':
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(number) < 1024.0:
                return f'{round(number, 2)} {unit}{suffix}'
            number = number / 1024
        return f'{pad_float(number)} Yi{suffix}'
    else:
        prefix = unit[0]
        divisor = 1000
        if len(unit) == 2 and unit.endswith('i'):
            divisor = 1024

        prefix_map = {'K': 1, 'M': 2, 'G': 3, 'T': 4, 'P': 5, 'E': 6, 'Z': 7}
        return f'{pad_float(number / (divisor ** prefix_map[prefix]))} {unit}{suffix}'

def greet(name: str = "World", excited: bool = False) -> str:
    if excited:
        return f"Hello, {name}!"
    return f"Hello, {name}."

def file_exists(filename: str='') -> bool:
    if os.path.exists(filename) and os.path.isfile(filename):
        return True
    return False

def get_config_file_path(filename: str='') -> str:
    return os.path.join(
        Path.home(),
        '.config',
        'polybar',
        'scripts',
        filename
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
