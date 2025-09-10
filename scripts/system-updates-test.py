#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, util
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
import inspect
import logging
import os
import re
import signal
import subprocess
import sys
import time
import json

modules = ['click']
missing = []

for module in modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    util.print_error(icon=glyphs.md_network_off_outline, message=f'Please install via pip: {", ".join(missing)}')
    sys.exit(1)

class Package(NamedTuple):
    BrewType: Optional[str] = None
    CurrentVersion: Optional[str] = None
    InstalledVersions: List[str] = None
    PreviousVersion: Optional[str] = None
    Name: Optional[str] = None

class SystemUpdates(NamedTuple):
    success  : Optional[bool] = False
    error    : Optional[str]  = None
    count    : Optional[int]  = 0
    packages : Optional[List[Package]] = None

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
VALID_TYPES = ['apt', 'brew', 'dnf', 'flatpak', 'mintupdate', 'pacman', 'snap', 'yay', 'yay-aur', 'yum']
LOGFILE = Path.home() / '.polybar-system-update-result.log'
LOADING = f'{util.color_title(glyphs.md_package_variant)} Checking updates...'

logging.basicConfig(
    filename=LOGFILE,
    filemode='a',  # 'a' = append, 'w' = overwrite
    format='%(asctime)s [%(levelname)-5s] - %(message)s',
    level=logging.INFO
)

def get_lockfile(package_type: str) -> Path:
    """
    Return the name of the lockfile
    """
    return Path.home() / f'.polybar-system-update-{package_type}.lock'

def worker_cleanup(lockfile: Path):
    if lockfile.exists():
        lockfile.unlink()
        logging.info(f'[worker] lockfile removed for {lockfile.stem}')

def get_tempfile_name(package_type: str = None):
    return os.path.join(
        Path.home(),
        f'.polybar-system-update-{package_type}.result.txt',
    )

def write_tempfile(filename: str = None, text: str = None):
    with open(filename, 'w') as f:
        f.write(text)

def read_tempfile(filename: str = None) -> str:
    with open(filename, 'r') as f:
        return f.read()

def find_apt_updates(package_type: str = None):
    """
    Execute apt to search for new updates
    """
    logging.info(f'[find_apt_updates] entering function, type={package_type}')

    command = f'sudo apt update'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc != 0:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    command = f'sudo apt list --upgradable'
    rc, stdout, stderr = util.run_piped_command(command)
    packages = []
    if rc == 0:
        lines = stdout.split('\n')
        pattern = re.compile(
            r'^([^/]+)/\S+\s+(\S+)\s+\S+\s+\[upgradable from:\s+(\S+)\]'
        )
        for line in lines[1:]:
            match = pattern.search(line)
            if match:
                package_name, new_version, old_version = match.groups()
                packages.append(
                    Package(
                        CurrentVersion=new_version,
                        PreviousVersion=old_version,
                        Name=package_name
                    )
                )

    logging.info(f'[find_apt_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_brew_updates(package_type: str = None):
    """
    Execute brew to search for new updates
    """
    logging.info(f'[find_brew_updates] entering function, type={package_type}')

    command = f'brew update'
    rc, _, stderr = util.run_piped_command(command)
    if rc != 0:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    command = f'brew list --installed-on-request'
    rc, stdout, _ = util.run_piped_command(command)
    if rc != 0:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    manually_installed = {line for line in stdout.splitlines()}

    command = f'brew outdated --json'
    rc, stdout, _ = util.run_piped_command(command)
    if rc != 0:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    try:
        brew_data = json.loads(stdout)
    except Exception as e:
        return SystemUpdates(success=False, error=f'failed to parse JSON from {command}: {e}')

    packages = []
    for obj in brew_data['formulae']:
        packages.append(
            Package(
                BrewType='formulae',
                CurrentVersion=obj['current_version'],
                InstalledVersions=obj['installed_versions'],
                Name=obj['name'],
            )
        )
    for obj in brew_data['casks']:
        packages.append(
            Package(
                BrewType='cask',
                CurrentVersion=obj['current_version'],
                InstalledVersions=obj['installed_versions'],
                Name=obj['name'],
            )
        )

    logging.info(f'[find_brew_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_dnf_updates(package_type: str=None):
    """
    Execute dnf to search for new updates
    """
    logging.info(f'[find_dnf_updates] entering function, type={package_type}')

    command = f'sudo dnf update -y'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc != 0:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    command = f'sudo dnf check-update'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        _, after = stdout.split('Repositories loaded.', 1)
        lines = after.lstrip().strip().split('\n')
        for line in lines:
            bits = re.split(r'\s+', line)
            packages.append(
                Package(
                    CurrentVersion=bits[1],
                    Name=bits[0]
                )
            )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    # This is here to test locally as I don't have dnf
    # with open(os.path.join(util.get_script_directory(), 'yum-output.txt'), 'r', encoding='utf-8') as f:
    #     stdout = f.read()
    #     _, after = stdout.split('Repositories loaded.', 1)
    #     lines = after.lstrip().strip().split('\n')
    #     for line in lines:
    #         bits = re.split(r'\s+', line)
    #         data['packages'].append(
    #             Package(
    #                 CurrentVersion=bits[1],
    #                 Name=bits[0]
    #             )
    #         )

    logging.info(f'[find_dnf_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_flatpak_updates(package_type: str=None):
    """
    Execute flatpak to search for new updates
    """
    logging.info(f'[find_flatpak_updates] entering function, type={package_type}')

    command = f'sudo flatpak update --appstream'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc != 0:
        data['success'] = False
        data['error'] = f'failed to execute {command}'
        return data

    command = f'sudo flatpak remote-ls --updates --columns=name,version'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        if stdout == '':
            logging.info(f'[find_flatpak_updates] returning data, package_type={package_type}')
            return SystemUpdates(success=True, count=len(packages), packages=packages)
        else:
            lines = stdout.split('\n')
            for line in lines:
                bits = re.split(r'\s+', line)
                packages.append(
                    Package(
                        CurrentVersion=bits[1],
                        Name=bits[0],
                    )
                )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')
 
    logging.info(f'[find_flatpak_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_mint_updates(package_type: str=None):
    """
    Execute mintupdate-cli to search for new updates
    """

    logging.info(f'[find_mint_updates] entering function, type={package_type}')

    command = f'sudo mintupdate-cli list -r'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        lines = stdout.split('\n')
        for line in lines:
            bits = re.split(r'\s+', line)
            packages.append(
                Package(
                    CurrentVersion=bits[2],
                    Name=bits[1]
                )
            )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    logging.info(f'[find_mint_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_pacman_updates(package_type: str=None):
    """
    Execute pacman to search for new updates
    """
    logging.info(f'[find_pacman_updates] entering function, type={package_type}')

    command = f'sudo pacman -Qu'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        _, after = stdout.split(':: Checking for updates...', 1)
        lines = after.lstrip().strip().split('\n')
        for line in lines:
            bits = re.split(r'\s+', line)
            packages.append(
                Package(
                    CurrentVersion=bits[1],
                    Name=bits[0],
                    PreviousVersion=bits[3],
                )
            )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    # This is here to test locally as I don't have pacman
    # with open(os.path.join(util.get_script_directory(), 'pacman-output.txt'), 'r', encoding='utf-8') as f:
    #     stdout = f.read()
    #     _, after = stdout.split(':: Checking for updates...', 1)
    #     lines = after.lstrip().strip().split('\n')
    #     for line in lines:
    #         bits = re.split(r'\s+', line)
    #         data['packages'].append(
    #             Package(
    #                 CurrentVersion=bits[3],
    #                 Name=bits[0],
    #                 PreviousVersion=bits[1],
    #             )
    #         )

    logging.info(f'[find_pacman_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_snap_updates(package_type: str=None):
    """
    Execute snap to search for new updates
    """
    logging.info(f'[find_snap_updates] entering function, type={package_type}')

    command = f'sudo snap refresh --list'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        lines = stdout.lstrip().strip().split('\n')
        for line in lines[1:]:
            bits = re.split(r'\s+', line)
            packages.append(
                Package(
                    CurrentVersion=bits[1],
                    Name=bits[0]
                )
            )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    # This is here to test locally as I don't have yum
    # with open(os.path.join(util.get_script_directory(), 'snap-output.txt'), 'r', encoding='utf-8') as f:
    #     stdout = f.read()
    #     lines = stdout.lstrip().strip().split('\n')
    #     for line in lines[1:]:
    #         bits = re.split(r'\s+', line)
    #         data['packages'].append(
    #             Package(
    #                 CurrentVersion=bits[1],
    #                 Name=bits[0]
    #             )
    #         )

    logging.info(f'[find_snap_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_yay_updates(package_type: str=None, aur: bool=False):
    """
    Execute yay to search for new updates
    """
    logging.info(f'[find_yay_updates] entering function, type={package_type}, aur={aur}')

    command = f'sudo yay -Qua'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        _, after = stdout.split(':: Checking for updates...', 1)
        lines = after.lstrip().strip().split('\n')

        if aur:
            lines = [line for line in lines if line.endswith('(AUR)')]
        else:
            lines = [line for line in lines if not line.endswith('(AUR)')]

        for line in lines:
            bits = re.split(r'\s+', line)
            packages.append(
                Package(
                    CurrentVersion=bits[3],
                    Name=bits[0],
                    PreviousVersion=bits[1],
                )
            )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    # This is here to test locally as I don't have yay
    # with open(os.path.join(util.get_script_directory(), 'yay-output.txt'), 'r', encoding='utf-8') as f:
    #     stdout = f.read()
    #     _, after = stdout.split(':: Checking for updates...', 1)
    #     lines = after.lstrip().strip().split('\n')

    #     if aur:
    #         lines = [line for line in lines if line.endswith('(AUR)')]
    #     else:
    #         lines = [line for line in lines if not line.endswith('(AUR)')]

    #     for line in lines:
    #         bits = re.split(r'\s+', line)
    #         data['packages'].append(
    #             Package(
    #                 CurrentVersion=bits[3],
    #                 Name=bits[0],
    #                 PreviousVersion=bits[1],
    #             )
    #         )

    logging.info(f'[find_yay_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_yum_updates(package_type: str=None):
    """
    Execute yum to search for new updates
    """
    logging.info(f'[find_yum_updates] entering function, type={package_type}')

    command = f'sudo yum update -y'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc != 0:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    command = f'sudo {binary} check-update'
    rc, stdout, stderr = util.run_piped_command(command)
    if rc == 0:
        packages = []
        _, after = stdout.split('Repositories loaded.', 1)
        lines = after.lstrip().strip().split('\n')
        for line in lines:
            bits = re.split(r'\s+', line)
            packages.append(
                Package(
                    CurrentVersion=bits[1],
                    Name=bits[0]
                )
            )
    else:
        return SystemUpdates(success=False, error=f'Failed to execute "{command}"')

    # This is here to test locally as I don't have yum
    # with open(os.path.join(util.get_script_directory(), 'yum-output.txt'), 'r', encoding='utf-8') as f:
    #     stdout = f.read()
    #     _, after = stdout.split('Repositories loaded.', 1)
    #     lines = after.lstrip().strip().split('\n')
    #     for line in lines:
    #         bits = re.split(r'\s+', line)
    #         data['packages'].append(
    #             Package(
    #                 CurrentVersion=bits[1],
    #                 Name=bits[0]
    #             )
    #         )

    logging.info(f'[find_yum_updates] returning data, package_type={package_type}')
    return SystemUpdates(success=True, count=len(packages), packages=packages)

def find_updates(package_type: str = ''):
    """
    Determine which function is required to get the updates
    """
    logging.info(f'[find_updates] type={package_type}')
    tempfile = get_tempfile_name(package_type=package_type)

    dispatch = {
        'apt'        : find_apt_updates,
        'brew'       : find_brew_updates,
        'dnf'        : find_dnf_updates,
        'flatpak'    : find_flatpak_updates,
        'mintupdate' : find_mint_updates,
        'pacman'     : find_pacman_updates,
        'snap'       : find_snap_updates,
        'yay-aur'    : lambda package_type: find_yay_updates(package_type=package_type, aur=True),
        'yay'        : lambda package_type: find_yay_updates(package_type=package_type, aur=False),
        'yum'        : find_yum_updates,
    }

    func = dispatch.get(package_type)
    data = func(package_type=package_type) if func else None
    
    if data:
        packages = 'package' if data.count == 1 else 'packages'
        message = f'{util.color_title(glyphs.md_package_variant)} {package_type} {data.count} outdated {packages}'
    else:
        message = f'{util.color_title(glyphs.md_package_variant)} {util.color_error(package_type)} {util.color_error("failed to find updates")}'
    
    logging.info(f'[find_updates] data received - output message={message}')

    write_tempfile(tempfile, message)
    subprocess.run(['polybar-msg', 'action', f'#system-updates-{package_type}.hook.0'])

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    System update checker
    """
    pass

@cli.command()
@click.option('-t', '--type', required=True, help=f'The type of update to query; valid choices are: {", ".join(VALID_TYPES)}')
def show(type):
    """
    Show the number of packages available
    """
    tempfile = get_tempfile_name(package_type=type)
    if util.file_exists(filename=tempfile):
        logging.info(f'[show] TMPFILE exists')
        print(read_tempfile(filename=tempfile))
    else:
        logging.info(f'[show] TMPFILE does not exist')
        print(LOADING)

@cli.command(help='Check available system updates from different sources')
@click.option('-t', '--type', required=True, help=f'The type of update to query; valid choices are: {", ".join(VALID_TYPES)}')
@click.option('-b', '--background', is_flag=True, default=False, help='Run in the background')
@click.option('-i', '--interval', type=int, default=300, show_default=True, help='The update interval (in seconds)')
def run(type, background, interval):
    """
    Run update check once or as a daemon
    """
    if not util.network_is_reachable():
        print(f'{util.color_title(glyphs.md_network_off_outline)} {util.color_error("the network is unreachable")}')
        sys.exit(1)

    tempfile = get_tempfile_name(package_type=type)
    write_tempfile(tempfile, LOADING)
    logging.info(f'[run] Starting - package_type={type}, background={background}, interval={interval}')

    lockfile = get_lockfile(type)

    if background:
        if util.is_worker_running(lockfile):
            logging.info(f'[run] worker already running for {type}, exiting')
            return

        subprocess.run(['polybar-msg', 'action', f'#system-updates-{type}.send.{LOADING}'])
        logging.info(f'[run] launching background worker - package_type={type}, interval={interval}')

        subprocess.Popen(
            [__file__, 'worker', type, '1', str(interval)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        subprocess.run(['polybar-msg', 'action', f'#system-updates-{type}.hook.0'])
    else:
        subprocess.run(['polybar-msg', 'action', f'#system-updates-{type}.send.{LOADING}'])
        logging.info(f'[run] running in foreground - package_type={type}')
        find_updates(package_type=type)
        subprocess.run(['polybar-msg', 'action', f'#system-updates-{type}.hook.0'])

@cli.command(name='worker')
@click.argument('package_type', type=str, required=True)
@click.argument('background', type=int, required=False)
@click.argument('interval', type=int, required=False)
def worker(package_type, background, interval):
    """
    Internal worker (can run once or loop forever if interval > 0)
    """
    lockfile = get_lockfile(package_type)
    pid = os.getpid()

    if background:
        if util.is_worker_running(lockfile):
            logging.info(f'[worker] worker already running for {package_type}, exiting')
            return

        # Create lockfile
        lockfile.write_text(str(pid))
        logging.info(f'[worker] background worker started for {package_type} (pid={pid})')

        # Setup signal handlers
        def handle_signal(signum, frame):
            logging.info(f'[worker] caught signal {signum}, exiting')
            worker_cleanup(lockfile)
            sys.exit(0)

        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, handle_signal)

        try:
            if interval and interval > 0:
                while True:
                    if not util.polybar_is_running():
                        logging.info(f'[worker] polybar not running, shutting down {package_type}')
                        break
                    logging.info(f'[worker] running find_updates - package_type={package_type}, interval={interval}')
                    subprocess.run(['polybar-msg', 'action', f'#system-updates-{package_type}.send.{LOADING}'])
                    find_updates(package_type=package_type)
                    time.sleep(interval)
        finally:
            if lockfile.exists():
                lockfile.unlink()
                logging.info(f'[worker] lockfile removed for {package_type}')
    else:
        logging.info(f'[worker] foreground worker - package_type={package_type}')
        find_updates(package_type=package_type)

if __name__ == '__main__':
    cli()
