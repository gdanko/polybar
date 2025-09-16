#!/usr/bin/env python3

from pprint import pprint
from scripts.polybar import util
import click
import configparser
import getpass
import logging
import os
import psutil
import re
import signal
import subprocess
import sys
import time

BAR_NAME = 'main'
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

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

def parse_config(filename: str=None):
    """
    Parse config.ini and return it as a ConfigParser object
    """
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(filename)
    except Exception as e:
        logging.error(f'failed to parse the config file {filename}: {e}')
        sys.exit(1)

    return parser

def setup(debug: bool=False):
    """
    Run some quick checks and return relevant bits
    """
    for binary in ['polybar', 'polybar-msg']:
        if not util.is_binary_installed(binary):
            logging.error(f'{binary} is not installed')
            sys.exit(1)

    configure_logging(debug=debug)

    polybar_config_file = os.path.join(util.get_config_directory(), 'config.ini')
    polybar_config = parse_config(filename=polybar_config_file)

    if f'bar/{BAR_NAME}' in polybar_config:
        if 'enable-ipc' in polybar_config[f'bar/{BAR_NAME}']:
            ipc_enabled = True if polybar_config[f'bar/{BAR_NAME}']['enable-ipc'] == 'true' else False

    return polybar_config, ipc_enabled

#----------------------------
# Start functions
#----------------------------
def start_polybar(polybar_config=None, bar_name: str=None, ipc_enabled: bool=False, debug: bool=False, pid: str=None):
    """
    A simple wrapper for starting polybar
    """
    pid = polybar_is_running()
    if pid:
        print(f'polybar is running with PID {pid}; please use stop or restart')
        sys.exit(0)

    print('starting polybar')
    stop_scripts()
    launch_polybar(bar_name=bar_name)
    background_processes(polybar_config=polybar_config)

def polybar_is_running():
    for proc in psutil.process_iter(attrs=['pid', 'cmdline', 'username']):
        try:
            if proc.info.get('cmdline') is not None and len(proc.info.get('cmdline')) > 0:
                cmdline = ' '.join(list(proc.info['cmdline']))
                if cmdline == f'polybar {BAR_NAME}' and proc.info.get('username') == getpass.getuser():
                    return proc.info.get('pid')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def launch_polybar(bar_name: str=None):
    """
    Attempt to launch polybar
    """
    # Here we'll simulate what's done in launch.sh
    logfile_name = os.path.join(
        util.get_home_directory(),
        f'polybar-{bar_name}.log',
    )

    # Step 1: Append '---' to the log file
    # echo "---" | tee -a /tmp/polybar-${BAR_NAME}.log
    try:
        with open(logfile_name, 'a') as f:
            f.write('---\n')
    except Exception as e:
        logging.error(f'failed to append the log file {logfile_name}: {e}')
        sys.exit(1)

    # Step 2: Start polybar, redirect output, and run it in the background detached
    # polybar ${BAR_NAME} 2>&1 | tee -a /tmp/polybar-${BAR_NAME}.log & disown
    command = ['polybar', bar_name]
    try:
        with open(logfile_name, 'a') as f:
            proc = subprocess.Popen(command,
                stdout     = f,
                stderr     = subprocess.STDOUT,
                preexec_fn = os.setpgrp  # Detach like 'disown'
            )
            print(f'successfully launched polybar with PID {proc.pid}')
    except Exception as e:
        logging.error(f'failed to launch polybar: {e}')
        sys.exit(1)

def background_processes(polybar_config=None):
    """
    Find all of the modules that are defined in config.ini, determine which are
    defined in modules-left/right, and if they are configured to run in the 
    background, attempt to do so
    """
    all_modules = sorted([section.replace('module/', '') for section in polybar_config.sections() if section.startswith('module/')])
    common_modules = sorted(list(set(find_enabled_modules()) & set(all_modules)))
    for module_name in common_modules:
        background(module_name=module_name, polybar_config=polybar_config)

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

def background(module_name: str=None, str=None, polybar_config=None):
    """
    Attempt to put a module into the background with its configured flags
    """
    try:
        module_config = dict(polybar_config[f'module/{module_name}'])
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
def stop_polybar(ipc_enabled: bool=False, pid: str=None):
    """
    A simple wrapper for stopping polybar
    """
    pid = polybar_is_running()
    if not pid:
        print('polybar isn\'t running')
        sys.exit(0)

    print('stopping polybar')
    kill_polybar_if_running(ipc_enabled=ipc_enabled, pid=pid)
    time.sleep(.5)
    stop_scripts()

def kill_polybar_if_running(ipc_enabled: bool=False, pid: str=None):
    """
    Kill polybar if it's running
    """
    pid = polybar_is_running()
    if polybar_is_running():
        if pid:
            command = f'polybar-msg -p {pid} cmd quit' if ipc_enabled else f'kill {pid}'
        else:
            # FIND THE RUNNING PID FOR BAR_NAME
            command = f'polybar-msg cmd quit' if ipc_enabled else 'killall -q polybar'

        rc, _, stderr = util.run_piped_command(command)
        if rc != 0:
            error = stderr if stderr != '' else 'unknown error'
            logging.error(f'failed to execute "{command}": {error}')
            sys.exit(1)
    else:
        print('polybar isn\'t running')
        sys.exit(0)

def get_background_scripts():
    script_directory = util.get_script_directory()
    processes = []
    for proc in psutil.process_iter(attrs=['pid', 'cmdline', 'username']):
        try:
            if proc.info.get('cmdline') is not None and len(proc.info.get('cmdline')) > 0:
                cmdline = ' '.join(list(proc.info['cmdline']))
                if cmdline.startswith('python3') and script_directory in cmdline and proc.info.get('username') == getpass.getuser():
                    processes.append({
                        'cmd'      : cmdline,
                        'pid'      : proc.info.get('pid'),
                        'username' : proc.info.get('username')
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes

def stop_scripts():
    """
    The scripts should die on their own if polybar dies, but if the
    interval is long, there will be a fair amount of time before it dies
    """
    processes = get_background_scripts()

    if len(processes) > 0:
        print(f'stopping {len(processes)} background {"script" if len(processes) == 1 else "scripts"}')
        for process in processes:
            cmd = process['cmd']
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
    polybar_config, ipc_enabled = setup(debug=debug)
    start_polybar(polybar_config=polybar_config, bar_name=BAR_NAME, ipc_enabled=ipc_enabled, debug=debug, pid=pid)

@cli.command(name='stop', help='Stop polybar and its backgound modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def stop(debug, pid):
    _, ipc_enabled = setup(debug=debug)
    stop_polybar(ipc_enabled=ipc_enabled, pid=pid)

@cli.command(name='restart', help='Restart polybar and its backgound modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def restart(debug, pid):
    polybar_config, ipc_enabled = setup(debug=debug)
    stop_polybar(ipc_enabled=ipc_enabled)
    time.sleep(.5)
    start_polybar(polybar_config=polybar_config, bar_name=BAR_NAME, ipc_enabled=ipc_enabled,debug=debug, pid=pid)

@cli.command(name='status', help='Get the status of polybar and its background modules')
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def status(debug, pid):
    polybar_config, ipc_enabled = setup(debug=debug)
    pid = polybar_is_running()
    if pid:
        message = f'polybar is running with PID {pid}'
        processes = get_background_scripts()
        pids = [str(process['pid']) for process in processes if process.get('pid') is not None]
        if len(pids) > 0:
            message += f' and has {len(pids)} background script {"PID" if len(pids) == 1 else "PIDs"} ({", ".join(pids)})'
        print(message)
        sys.exit(0)
    else:
        print('polybar isn\'t running running')

@cli.command(name='dummy', help='I am a dummy', hidden=(getpass.getuser() != 'gdanko'))
@click.option('-d', '--debug', is_flag=True, help='Show debug logging')
@click.option('-p', '--pid', help='Specify a pid')
def dummy(debug, pid):
    polybar_config, ipc_enabled = setup(debug=debug)
    print('i do nothing')

if __name__ == '__main__':
    cli()
