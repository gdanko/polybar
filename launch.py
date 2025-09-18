#!/usr/bin/env python3

from pathlib import Path, PurePosixPath
from pprint import pprint
from scripts.polybar import util
import click
import configparser
import getpass
import json
import logging
import os
import psutil
import re
import signal
import subprocess
import sys
import time

# Constants
BAR_NAME = 'main'
CONFIG_FILE = Path(PurePosixPath(util.get_config_directory())) / 'config.ini'
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
LOGFILE = Path.home() / f'polybar-{BAR_NAME}.log'
STATEFILE = Path.home() / '.polybar-launch-state.json'

# Globals
CONFIG : configparser.ConfigParser | None = None
IPC_ENABLED : bool | None = None
PROCESS_NAME : str | None = None

class RightPadFormatter(logging.Formatter):
    def __init__(self, levelnames):
        self.max_len = max(len(name) for name in levelnames)
        fmt = '[%(levelname)s] %(pad)s%(message)s'
        super().__init__(fmt)

    def format(self, record):
        # Spaces after the closing bracket
        pad_len = self.max_len - len(record.levelname)
        record.pad = ' ' * (pad_len + 1)  # +1 for spacing
        return super().format(record)

#----------------------------
# Common helpers
#----------------------------
def get_duration(created: int=0) -> str:
    d, h, m, s = util.duration(int(time.time()) - created)
    if d > 0:
        return f'[{d:02d}d {h:02d}h {m:02d}m {s:02d}s]'
    else:
        return f'[{h:02d}h {m:02d}m {s:02d}s]'

def get_background_scripts():
    processes = []
    for proc in psutil.process_iter(attrs=['cmdline', 'create_time', 'name', 'pid', 'username']):
        try:
            if proc.info.get('cmdline') is not None and len(proc.info.get('cmdline')) > 0:
                cmdline = ' '.join(list(proc.info['cmdline']))
                if len(proc.info['cmdline']) > 2:
                    cmd_short = ' '.join(list(proc.info['cmdline'][:2]))
                if cmdline.startswith('python3') and util.get_script_directory() in cmdline and proc.info.get('username') == getpass.getuser():
                    new_process = {
                        'cmd_short': cmd_short,
                        'created'  : int(proc.info.get('create_time')) if proc.info.get('create_time') is not None else 0,
                        'pid'      : proc.info.get('pid'),
                        'username' : proc.info.get('username'),
                    }

                    processes.append(new_process)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes

def polybar_is_running():
    binary = util.is_binary_installed('polybar')
    for proc in psutil.process_iter(attrs=['cmdline', 'create_time', 'name', 'pid', 'username']):
        try:
            if proc.info.get('cmdline') is not None:
                cmd = ' '.join(list(proc.info['cmdline']))
                if cmd == f'{binary} {BAR_NAME}' and proc.info.get('username') == getpass.getuser():
                    return {
                        'cmd'      : cmd,
                        'cmdline'  : list(proc.info.get('cmdline')) if proc.info.get('cmdline') is not None else [],
                        'created'  : int(proc.info.get('create_time')),
                        'modules'  : get_background_scripts(),
                        'pid'      : proc.info.get('pid'),
                        'username' : proc.info.get('username'),
                    }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def process_is_alive(pid: int=0, command: str=None):
    try:
        proc = psutil.Process(pid)
        proc_info = proc.as_dict(attrs=['cmdline', 'create_time', 'name', 'pid', 'username'])
        cmd = ' '.join(proc_info.get('cmdline')) if proc_info.get('cmdline') is not None else None
        output = {
            'cmd'      : cmd,
            'cmdline'  : list(proc_info.get('cmdline')) if proc_info.get('cmdline') is not None else [],
            'created'  : int(proc_info.get('create_time')),
            'pid'      : proc_info.get('pid'),
            'username' : proc_info.get('username'),
        }
    except:
        return False 
    
    if command:
        return output if (proc.pid == pid and cmdline == command and proc_info.get('username') == getpass.getuser()) else None
    else:
        return output if (proc.pid == pid and proc_info.get('username') == getpass.getuser()) else None

def parse_statefile():
    if STATEFILE.exists():
        try:
            return json.loads(STATEFILE.read_text())
        except:
            return None
    return None

def compare_statefile_with_proc(state=None, proc=None):
    if not state:
        state = parse_statefile()
    if not proc:
        proc = polybar_is_running()

    return (
        state.get('pid') == proc.get('pid') and
        state.get('cmdline') == proc.get('cmdline') and
        state.get('username') == proc.get('username') and
        state.get('created') == proc.get('created')
    )

def show_module_differences(state=None, proc=None):
    if not state:
        state = parse_statefile()
    if not proc:
        proc = polybar_is_running()

    differences = []
    for i, (left, right) in enumerate(zip(state, proc)):
        for k in set(left) | set(right):
            if left.get(k) != right.get(k):
                differences.append({
                    'item'  : json.dumps(left),
                    'state' : left.get(k),
                    'proc'  : right.get(k)
                })

#----------------------------
# Setup and configuration
#----------------------------
def configure_logging(debug: bool=False):
    """
    Set up the logging
    """
    all_levels = [logging.getLevelName(lvl) for lvl in range(0, 60) if isinstance(logging.getLevelName(lvl), str)]
    handler = logging.StreamHandler()
    handler.setFormatter(RightPadFormatter(all_levels))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) if debug else logger.setLevel(logging.INFO)
    logger.addHandler(handler)

def parse_config():
    """
    Parse config.ini and return it as a ConfigParser object
    """
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(CONFIG_FILE)
    except Exception as e:
        logging.error(f'failed to parse the config file {CONFIG_FILE}: {e}')
        sys.exit(1)

    return parser

def setup(debug: bool=False):
    """
    Run some quick checks and return relevant bits
    """
    global CONFIG, IPC_ENABLED, PROCESS_NAME

    for binary in ['polybar', 'polybar-msg']:
        if not util.is_binary_installed(binary):
            logging.error(f'{binary} is not installed')
            sys.exit(1)

    configure_logging(debug=debug)


    PROCESS_NAME = f'{util.is_binary_installed('polybar')} {BAR_NAME}'
    CONFIG = parse_config()

    if f'bar/{BAR_NAME}' in CONFIG:
        if 'enable-ipc' in CONFIG[f'bar/{BAR_NAME}']:
            IPC_ENABLED = True if CONFIG[f'bar/{BAR_NAME}']['enable-ipc'] == 'true' else False

#----------------------------
# Start functions
#----------------------------
def start_polybar():
    """
    A simple wrapper for starting polybar
    """
    proc = polybar_is_running()
    if proc:
        print(f'polybar is running with PID {proc.get("pid")}; please use stop or restart')

        state = parse_statefile()
        if not compare_statefile_with_proc(proc=proc, state=state):
            print(f'the statefile doesn\'t align with the current process; rewriting the file')
            write_launch_state(pid=proc.get('pid'))
        sys.exit(0)

    print('starting polybar')
    stop_scripts()
    pid = launch_polybar()
    background_processes()
    time.sleep(2)
    write_launch_state(pid=pid)

def launch_polybar():
    """
    Attempt to launch polybar
    """
    binary = util.is_binary_installed('polybar')

    # Here we'll simulate what's done in launch.sh
    # Step 1: Append '---' to the log file
    # echo "---" | tee -a /tmp/polybar-${BAR_NAME}.log
    try:
        with open(LOGFILE, 'a') as f:
            f.write('---\n')
    except Exception as e:
        logging.error(f'failed to append the log file {LOGFILE}: {e}')
        sys.exit(1)

    # Step 2: Start polybar, redirect output, and run it in the background detached
    # polybar ${BAR_NAME} 2>&1 | tee -a /tmp/polybar-${BAR_NAME}.log & disown
    command = [binary, BAR_NAME]
    try:
        with open(LOGFILE, 'a') as f:
            proc = subprocess.Popen(command,
                stdout     = f,
                stderr     = subprocess.STDOUT,
                preexec_fn = os.setpgrp  # Detach like 'disown'
            )
            print(f'successfully launched polybar with PID {proc.pid}')
            return proc.pid
    except Exception as e:
        logging.error(f'failed to launch polybar: {e}')
        sys.exit(1)

def write_launch_state(pid: int=0):
    try:
        proc = psutil.Process(pid)
        proc_info = proc.as_dict(attrs=['cmdline', 'create_time', 'name', 'pid', 'username'])
    except:
        logging.error(f'hmmmm PID {pid} doesn\'t seem to exist')
        sys.exit(1)

    launch_state = {
        'cmd'      : ' '.join(list(proc_info.get('cmdline'))) if proc_info.get('cmdline') is not None else None,
        'cmdline'  : list(proc_info.get('cmdline')) if proc_info.get('cmdline') is not None else [],
        'created'  : int(proc_info.get('create_time')),
        'modules'  : get_background_scripts(),
        'pid'      : proc_info.get('pid'),
        'username' : proc_info.get('username'),
    }
    STATEFILE.write_text(json.dumps(launch_state, indent=4))

def background_processes():
    """
    Find all of the modules that are defined in config.ini, determine which are
    defined in modules-left/right, and if they are configured to run in the 
    background, attempt to do so
    """
    global CONFIG

    all_modules = sorted([section.replace('module/', '') for section in CONFIG.sections() if section.startswith('module/')])
    common_modules = sorted(list(set(find_enabled_modules()) & set(all_modules)))
    for module_name in common_modules:
        background(module_name=module_name)

def find_enabled_modules() -> list:
    """
    Return a list of enabled modules from config.ini
    """
    enabled_modules = []

    for orientation in ['left', 'right']:
        command = f'polybar --dump=modules-{orientation}'
        rc, stdout, _ = util.run_piped_command(command)
        if rc == 0:
            for module in re.split(r'\s+', stdout):
                if len(module) > 0:
                    enabled_modules.append(module)
        else:
            print(f'failed to execute "{command}"')
            sys.exit(1)

    return sorted(enabled_modules)

def background(module_name: str=None):
    """
    Attempt to put a module into the background with its configured flags
    """
    global CONFIG

    try:
        module_config = dict(CONFIG[f'module/{module_name}'])
        if 'background' in module_config:
            module_config['background'] = True if module_config['background'] == 'true' else False
    except Exception as e:
        logging.error(f'failed to parse the configuration for module/{module_name}: {e}')
        sys.exit(1)

    if 'background-script' in module_config:
        script_name = os.path.join(util.get_script_directory(), f'{module_config["background-script"]}')
    else:
        script_name = os.path.join(util.get_script_directory(), f'{module_name}.py')

    if 'background' in module_config:
        if module_config['background']:
            if not util.file_exists(script_name):
                logging.error(f'the script {script_name} doesn\'t exist')
                sys.exit(1)

            if not util.file_is_executable(script_name):
                logging.error(f'the script {script_name} isn\'t executable')
                sys.exit(1)

            command_bits = [ script_name ]

            if 'background-action' in module_config:
                command_bits.append(module_config['background-action'])

            for key, value in module_config.items():
                if key.startswith('background-arg-'):
                    command_bits.append(f'--{key.split('background-arg-')[1]}')
                    if value and value != '':
                        command_bits.append(value)
            command_bits.append('--background')
            command = ' '.join(command_bits)

            try:
                logging.debug(f'attempting to launch {os.path.basename(script_name)} in the background with "{command}"')
                _ = util.run_piped_command(command=command, background=True)
            except Exception as e:
                logging.error(f'failed to execute "{command}": {e}')
                sys.exit(1)
        else:
            logging.warning(f'the module {module_name} cannot be launched in the background due to a configuration setting')

#----------------------------
# Stop functions
#----------------------------
def stop_polybar(pid: str=None):
    """
    A simple wrapper for stopping polybar
    """
    pid = polybar_is_running()
    if not pid:
        print('polybar isn\'t running')
        sys.exit(0)

    print('stopping polybar')
    kill_polybar_if_running(pid=pid)
    time.sleep(.5)
    stop_scripts()

def kill_polybar_if_running(pid: str=None):
    """
    Kill polybar if it's running
    """
    global IPC_ENABLED

    proc = polybar_is_running()
    if polybar_is_running():
        if proc:
            command = f'polybar-msg -p {proc.get("pid")} cmd quit' if IPC_ENABLED else f'kill {proc.get("pid")}'
        else:
            # FIND THE RUNNING PID FOR BAR_NAME
            command = f'polybar-msg cmd quit' if IPC_ENABLED else 'killall -q polybar'

        rc, _, stderr = util.run_piped_command(command)
        if rc != 0:
            error = stderr if stderr != '' else 'unknown error'
            logging.error(f'failed to execute "{command}": {error}')
            sys.exit(1)
        

    else:
        print('polybar isn\'t running')
        sys.exit(0)

def stop_scripts():
    """
    The scripts should die on their own if polybar dies, but if the
    interval is long, there will be a fair amount of time before it dies
    """
    processes = get_background_scripts()

    if len(processes) > 0:
        print(f'stopping {len(processes)} background {"script" if len(processes) == 1 else "scripts"}')
        for process in processes:
            cmd = process['cmd_short']
            pid = process['pid']

            try:
                logging.debug(f'attempting to stop "{cmd}" (PID {pid})')
                proc = psutil.Process(pid)
                proc.send_signal(signal.SIGTERM)
            except psutil.NoSuchProcess:
                logging.debug(f'no such process with PID {pid}')
            except psutil.AccessDenied:
                logging.error(f'permission denied stopping PID {pid}')

            time.sleep(.5)

            # Make sure it's gone
            try:
                proc = psutil.Process(pid)
                logging.error(f'process "{cmd}" with PID ({pid}) was not successfully stopped')
            except psutil.NoSuchProcess:
                logging.debug(f'successfully stopped PID {pid}')

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass

@cli.command(name='start', help='Start polybar and its backgound modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def start(debug, pid):
    setup(debug=debug)
    start_polybar()

@cli.command(name='stop', help='Stop polybar and its backgound modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def stop(debug, pid):
    setup(debug=debug)
    stop_polybar(pid=pid)

@cli.command(name='restart', help='Restart polybar and its backgound modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def restart(debug, pid):
    setup(debug=debug)
    stop_polybar()
    time.sleep(.5)
    start_polybar()

@cli.command(name='status', help='Get the status of polybar and its background modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
@click.option('--detail', is_flag=True, help='Show detailed information about any running background modules')
def status(debug, pid, detail):
    setup(debug=debug)
    proc = polybar_is_running()
    state = parse_statefile()

    if proc:
        message = f'polybar is running with PID {proc["pid"]}'
        # Rewerite the state file if the two mismatch, eventually compare module differences as well
        if not compare_statefile_with_proc(state=state, proc=proc):
            print(f'the state file "{STATEFILE}" doesn\'t match the current state; rewriting')
            write_launch_state(pid = proc.get('pid'))

        pids = [str(process['pid']) for process in proc.get('modules') if process.get('pid') is not None]
        if len(pids) > 0:
            message += f' and is managing {len(pids)} background {"module" if len(pids) == 1 else "modules"}'
        print(message)

        if detail:
            longest_duration = 0
            longest_pid = 0
            for process in proc.get('modules'):
                process['duration'] = get_duration(created=process['created'])
                longest_duration = len(process['duration']) if len(process['duration']) > longest_duration else longest_duration

            for process in proc.get('modules'):
                print(f'{process["pid"]:{longest_pid}} {process["duration"]:<{longest_duration}} {process["cmd_short"]}')
    else:
        print('polybar isn\'t running running')

    sys.exit(0)

@cli.command(name='dummy', help='I am a dummy', hidden=(getpass.getuser() != 'gdanko'))
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def dummy(debug, pid):
    setup(debug=debug)
    print('i do nothing')

if __name__ == '__main__':
    cli()
