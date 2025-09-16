#!/usr/bin/env python3

from pprint import pprint
from scripts.polybar import util
import click
import configparser
import logging
import os
import psutil
import re
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
    all_levels = [logging.getLevelName(lvl) for lvl in range(0, 60) if isinstance(logging.getLevelName(lvl), str)]
    handler = logging.StreamHandler()
    handler.setFormatter(RightPadFormatter(all_levels))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) if debug else logger.setLevel(logging.INFO)
    logger.addHandler(handler)

def parse_config(filename: str=None):
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(filename)
    except Exception as e:
        logging.error(f'Failed to parse the config file {filename}: {e}')
        sys.exit(1)

    return parser

def setup(debug: bool=False):
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
    A simple wrapper for starting
    """
    running, pids = util.process_is_running(name='polybar', full=False)
    if running and len(pids) > 0:
        if len(pids) == 1:
            message = f'polybar is already running with the pid {pids[0]}'
        elif len(pids) > 1:
            message = f'{len(pids)} instances of polybar are running with the following pids: {", ".join(pids)}'
        print(message)
        sys.exit(0)

    print('Starting polybar')
    kill_scripts()
    launch_polybar(bar_name=bar_name)
    background_processes(polybar_config=polybar_config)

def launch_polybar(bar_name: str=None):
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
        logging.error(f'Failed to append the log file {logfile_name}: {e}')
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
            print(f'Successfully launched Polybar with PID {proc.pid}')
    except Exception as e:
        logging.error(f'Failed to launch Polybar: {e}')
        sys.exit(1)

def background_processes(polybar_config=None):
    all_modules = sorted([section.replace('module/', '') for section in polybar_config.sections() if section.startswith('module/')])
    common_modules = sorted(list(set(find_enabled_modules()) & set(all_modules)))
    for module_name in common_modules:
        background(module_name=module_name, polybar_config=polybar_config)

def find_enabled_modules() -> list:
    enabled_modules = []

    for orientation in ['left', 'right']:
        command = f'polybar --dump=modules-{orientation}'
        rc, stdout, _ = util.run_piped_command(command)
        if rc == 0:
            for module in re.split(r'\s+', stdout):
                if len(module) > 0:
                    enabled_modules.append(module)
        else:
            print(f'failed to execute {command}')
            sys.exit(1)

    return sorted(enabled_modules)

def background(module_name: str=None, str=None, polybar_config=None):
    try:
        module_config = dict(polybar_config[f'module/{module_name}'])
        if 'background' in module_config:
            module_config['background'] = True if module_config['background'] == 'true' else False
    except Exception as e:
        logging.error(f'Failed to parse the configuration for module/{module_name}: {e}')
        sys.exit(1)

    if 'background-script' in module_config:
        script_name = os.path.join(util.get_script_directory(), f'{module_config["background-script"]}')
    else:
        script_name = os.path.join(util.get_script_directory(), f'{module_name}.py')

    if 'background' in module_config:
        if module_config['background']:
            if not util.file_exists(script_name):
                logging.error(f'The script {script_name} doesn\'t exist')
                sys.exit(1)

            if not util.file_is_executable(script_name):
                logging.error(f'The script {script_name} isn\'t executable')
                sys.exit(1)

            command_bits = [ script_name ]

            if 'background-action' in module_config:
                command_bits.append(module_config['background-action'])

            for key, value in module_config.items():
                if key.startswith('background-arg-'):
                    command_bits.append(f'--{key.split('-')[2]}')
                    if value and value != '':
                        command_bits.append(value)
            command_bits.append('--background')
            command = ' '.join(command_bits)

            try:
                logging.debug(f'Attempting to launch {os.path.basename(script_name)} in the background with {command}')
                _ = util.run_piped_command(command=command, background=True)
            except Exception as e:
                logging.error(f'Failed to execute {command}: {e}')
                sys.exit(1)
        else:
            logging.warning(f'The module {module_name} cannot be launched in the background due to a configuration setting')

#----------------------------
# Stop functions
#----------------------------
def stop_polybar(ipc_enabled: bool=False, pid: str=None):
    """
    A simple wrapper for stopping
    """
    print('Stopping polybar')
    kill_polybar_if_running(ipc_enabled=ipc_enabled, pid=pid)
    time.sleep(.5)
    kill_scripts()

def kill_polybar_if_running(ipc_enabled: bool=False, pid: str=None):
    if util.polybar_is_running():
        if pid:
            command = f'polybar-msg -p {pid} cmd quit' if ipc_enabled else f'kill {pid}'
        else:
            command = f'polybar-msg cmd quit' if ipc_enabled else 'killall -q polybar'

        rc, _, stderr = util.run_piped_command(command)
        if rc != 0:
            error = stderr if stderr != '' else 'Unknown error'
            logging.error(f'Failed to execute {command}: {error}')
            sys.exit(1)
    else:
        print('Not running')

def kill_scripts():
    """
    The scripts should die on their own if polybar dies, but if the
    interval is long, there will be a fair amount of time before it dies
    """
    script_directory = util.get_script_directory()
    processes = []
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            if proc.info.get('cmdline') is not None:
                if len(proc.info['cmdline']) > 0:
                    cmdline = ' '.join(list(proc.info['cmdline']))
                    if cmdline.startswith('python3') and script_directory in cmdline:
                        processes.append({
                            'cmd': cmdline,
                            'pid': proc.info.get('pid'),
                        })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for process in processes:
        cmd = process['cmd']
        pid = process['pid']

        try:
            logging.debug(f'Attempting to kill "{cmd}" (PID {pid})')
            proc = psutil.Process(pid)
            proc.kill()
        except psutil.NoSuchProcess:
            logging.warning(f'No such process with PID {pid}')
        except psutil.AccessDenied:
            logging.error(f'Permission denied killing PID {pid}')

        time.sleep(.5)

        # Make sure it's gone
        try:
            proc = psutil.Process(pid)
            pprint(proc.info)
            logging.error(f'Process "{cmd}" with PID ({pid}) was not successfully killed')
        except psutil.NoSuchProcess:
            logging.debug(f'Successfully killed PID {pid}')

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

if __name__ == '__main__':
    cli()
