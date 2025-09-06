#!/usr/bin/env python3

from scripts.polybar import util
import configparser
import logging
import os
import re
import subprocess
import sys

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

def configure_logging(debug: bool=False):
    all_levels = [logging.getLevelName(lvl) for lvl in range(0, 60) if isinstance(logging.getLevelName(lvl), str)]
    handler = logging.StreamHandler()
    handler.setFormatter(RightPadFormatter(all_levels))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) if debug else logger.setLevel(logging.INFO)
    logger.addHandler(handler)

def initialize():
    for binary in ['polybar', 'polybar-msg']:
        if not util.is_binary_installed(binary):
            logging.error(f'{binary} is not installed')
            sys.exit(1)

def parse_config(filename: str=None):
    try:
        parser = configparser.ConfigParser()
        parser.read(filename)
    except:
        logging.error(f'Failed to parse the config file {filename}')
        sys.exit(1)

    return parser

def kill_polybar_if_running(ipc_enabled):
    command = 'polybar-msg cmd quit' if ipc_enabled else 'killall -q polybar'
    rc, _, stderr = util.run_piped_command(command)
    if rc != 0:
        if stderr == 'polybar-msg: No active ipc channels':
            logging.info(f'Polybar isn\'t running')
            return
        else:
            logging.error(f'Failed to execute {command}: {stderr}')
            sys.exit(1)

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
            logging.info(f'Successfully launched Polybar with PID {proc.pid}')
    except Exception as e:
        logging.error(f'Failed to launch Polybar: {e}')
        sys.exit(1)

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

def kill_if_running(ps_command_string: str=None):
    command = f'pgrep -f "{ps_command_string}"'
    rc, pid, stderr = util.run_piped_command(command)
    if rc == 0 and pid != '':
        logging.debug(f'Attempting to kill "{ps_command_string}" (pid {pid})')
        command = f'kill {pid}'
        rc, _, stderr = util.run_piped_command(command)
        if rc == 0:
            return
        else:
            if stderr:
                logging.error(f'Failed to kill pid {pid}: {stderr}')
                sys.exit(1)
            else:
                logging.error(f'Failed to kill pid {pid}: Unknown error')
                sys.exit(1)
    else:
        return

def daemonize(module_name: str=None, args: dict={}):
    script_name = os.path.join(util.get_script_directory(), f'{module_name}.py')

    if not util.file_exists(script_name):
        logging.error(f'The script {script_name} doesn\'t exist')
        sys.exit(1)

    if not util.file_is_executable(script_name):
        logging.error(f'The script {script_name} isn\'t executable')
        sys.exit(1)

    command_bits = [ script_name ]
    for flag, value in args.items():
        command_bits.append(flag)
        if value:
            command_bits.append(value)
    command_bits.append('--daemonize')
    
    command = ' '.join(command_bits)
    ps_command_string = f'python3 {command}'

    kill_if_running(ps_command_string=ps_command_string)

    try:
        logging.debug(f'Attempting to daemonize {os.path.basename(script_name)} with {command}')
        _ = util.run_piped_command(command=command, background=True)
    except Exception as e:
        logging.error(f'Failed to execute {command}: {e}')
        sys.exit(1)

def daemonize_processes():
    # Now we need to daemonize those plugins that need daemonizing
    enabled_modules = find_enabled_modules()

    module_name = 'cpu-usage-clickable'
    cpu_usage_interval = 2
    if module_name in enabled_modules:
        daemonize(module_name,
        {
            '--interval': str(cpu_usage_interval),
        })
    
    module_name = 'memory-usage-clickable'
    memory_usage_interval = 2
    if module_name in enabled_modules:
        daemonize(module_name,
        {
            '--interval' : str(memory_usage_interval),
        })
    
    module_name = 'polybar-speedtest'
    polybar_speedtest_interval = 300
    if module_name in enabled_modules:
        daemonize(module_name,
        {
            '--upload'   : None,
            '--download' : None,
            '--interval' : str(polybar_speedtest_interval),
        })
    
    module_name = 'filesystem-usage-clickable'
    filesystem_usage_interval = 2
    filesystems = [module for module in enabled_modules if module.startswith('filesystem-usage-clickable-')]
    for filesystem in filesystems:
        daemonize(module_name,
        {
            '--name'     : filesystem.split('-')[3],
            '--interval' : str(filesystem_usage_interval),
        })

def main():
    debug = True
    configure_logging(debug=debug)
    initialize()
    bar_name = 'main'

    polybar_config_file = os.path.join(util.get_config_directory(), 'config.ini')
    polybar_config = parse_config(filename=polybar_config_file)

    # dynamically get all bar names and handle them accordingly!
    if 'bar/main' in polybar_config:
        if 'enable-ipc' in polybar_config['bar/main']:
            ipc_enabled = True if polybar_config['bar/main']['enable-ipc'] == 'true' else False
    
    kill_polybar_if_running(ipc_enabled=ipc_enabled)
    launch_polybar(bar_name=bar_name)
    daemonize_processes()

if __name__ == '__main__':
    main()
