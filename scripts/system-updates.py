#!/usr/bin/env python3

from dataclasses import dataclass, field
from pathlib import Path
from polybar import glyphs, util
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
import argparse
import json
import os
import re
import sys

class Package(NamedTuple):
    BrewType: Optional[str] = None
    CurrentVersion: Optional[str] = None
    InstalledVersions: List[str] = field(default_factory=list)
    PreviousVersion: Optional[str] = None
    Name: Optional[str] = None

def find_apt_updates():
    """
    Execute apt to search for new updates
    """
    data = {
        'success' : True,
        'packages': [],
        'error'   : None,
    }
    binary = 'apt'
    command = f'{binary} list --upgradable'

    if util.is_binary_installed(binary):
        rc, stdout, stderr = util.run_piped_command(command)
        if rc == 0:
            lines = stdout.strip().split('\n')
            # libegl-mesa0/noble-updates 25.0.7-0ubuntu0.24.04.2 amd64 [upgradable from: 25.0.7-0ubuntu0.24.04.1]
            for line in lines[1:]:
                # bits = re.split(r'\s+', line)
                pattern = re.compile(
                    r'^([^/]+)/\S+\s+(\S+)\s+\S+\s+\[upgradable from:\s+(\S+)\]'
                )
                match = pattern.search(line)
                if match:
                    package_name, new_version, old_version = match.groups()
                    data['packages'].append(
                        Package(
                            CurrentVersion=new_version,
                            PreviousVersion=old_version,
                            Name=package_name
                        )
                    )
        else:
            data['success'] = False
            data['error'] = f'Failed to execute "{command}"'
    else:
        data['success'] = False
        data['error'] = f'{binary} is not installed'

    return data

# -> Tuple[Union[Dict[str, List[Package]], None], Union[str, None]]:
def find_brew_updates():
    """
    Execute brew to search for new updates
    """
    data = {
        'success' : True,
        'packages': [],
        'error'   : None,
    }
    binary = 'brew'

    if util.is_binary_installed(binary):
        command = f'{binary} update'
        rc, _, stderr = util.run_piped_command(command)
        if rc != 0:
            data['success'] = False
            data['error'] = f'Failed to execute "{command}"'
            return data
        
        command = f'{binary} list --installed-on-request'
        rc, stdout, _ = util.run_piped_command(command)
        if rc != 0:
            data['success'] = False
            data['error'] = f'Failed to execute "{command}"'
            return data
        manually_installed = {line for line in stdout.splitlines()}

        command = f'{binary} outdated --json'
        rc, stdout, _ = util.run_piped_command(command)
        if rc != 0:
            data['success'] = False
            data['error'] = f'Failed to execute "{command}"'
            return data
        
        try:
            brew_data = json.loads(stdout)
        except Exception as e:
            data['success'] = False
            data['error'] = f'failed to parse JSON from {command}: {e}'
            return data

        for obj in brew_data['formulae']:
            # Just for testing, normally  ,
            if obj['name'] in manually_installed or not obj['name'] in manually_installed:
                data['packages'].append(
                    Package(
                        BrewType='formulae',
                        CurrentVersion=obj['current_version'],
                        InstalledVersions=obj['installed_versions'],
                        Name=obj['name'],
                    )
                )
        for obj in brew_data['casks']:
            data['packages'].append(
                Package(
                    BrewType='cask',
                    CurrentVersion=obj['current_version'],
                    InstalledVersions=obj['installed_versions'],
                    Name=obj['name'],
                )
            )

    else:
        data['success'] = False
        data['error'] = f'{binary} is not installed'

    return data

def find_dnf_updates():
    """
    Execute dbf to search for new updates
    """
    data = {
        'success' : True,
        'packages': [],
        'error'   : None,
    }
    # binary = 'dnf'
    # command = f'{binary} check-update'

    # if util.is_binary_installed(binary):
    #     rc, stdout, stderr = util.run_piped_command(command)
    #     if rc == 0:
    #         _, after = stdout.strip().split('Repositories loaded.', 1)
    #         lines = after.lstrip().strip().split('\n')
    #         for line in lines:
    #             bits = re.split(r'\s+', line)
    #             data['packages'].append(
    #                 Package(
    #                     CurrentVersion=bits[1],
    #                     Name=bits[0]
    #                 )
    #             )
    #     else:
    #         data['success'] = False
    #         data['error'] = f'Failed to execute "{command}"'
    # else:
    #     data['success'] = False
    #     data['error'] = f'{binary} is not installed'

    # This is here to test locally as I don't have yum
    with open(os.path.join(util.get_config_directory(), 'yum-output.txt'), 'r', encoding='utf-8') as f:
        stdout = f.read()
        _, after = stdout.strip().split('Repositories loaded.', 1)
        lines = after.lstrip().strip().split('\n')
        for line in lines:
            bits = re.split(r'\s+', line)
            data['packages'].append(
                Package(
                    CurrentVersion=bits[1],
                    Name=bits[0]
                )
            )

    return data

def find_flatpak_updates():
    """
    Execute flatpak to search for new updates
    """
    data = {
        'success' : True,
        'packages': [],
        'error'   : None        
    }
    binary = 'flatpak'
    command = f'{binary} remote-ls --updates'

    if util.is_binary_installed(binary):
        rc, stdout, stderr = util.run_piped_command(command)
        if rc == 0:
            lines = stdout.strip().split('\n')
            # fs = re.split(r'\s+', lines[1])[1]
            for line in lines:
                bits = re.split(r'\s+', line)
                data['packages'].append(
                    Package(
                        CurrentVersion=bits[2],
                        InstalledVersions=[],
                        Name=bits[0],
                    )
                )
        else:
            data['success'] = False
            data['error'] = f'failed to execute {command}'
    else:
        data['success'] = False
        data['error'] = f'{binary} is not installed'
 
    return data

def find_mint_updates():
    """
    Execute apt to search for new updates
    """
    data = {
        'success' : True,
        'packages': [],
        'error'   : None,
    }
    binary = 'mintupdate-cli'
    command = f'{binary} list -r'

    if util.is_binary_installed(binary):
        rc, stdout, stderr = util.run_piped_command(command)
        if rc == 0:
            lines = stdout.strip().split('\n')
            for line in lines:
                bits = re.split(r'\s+', line)
                data['packages'].append(
                    Package(
                        CurrentVersion=bits[2],
                        Name=bits[1]
                    )
                )
        else:
            data['success'] = False
            data['error'] = f'Failed to execute "{command}"'
    else:
        data['success'] = False
        data['error'] = f'{binary} is not installed'

    return data

def find_yum_updates():
    """
    Execute yum to search for new updates
    """
    data = {
        'success' : True,
        'packages': [],
        'error'   : None,
    }
    binary = 'yum'
    command = f'{binary} check-update'

    if util.is_binary_installed(binary):
        rc, stdout, stderr = util.run_piped_command(command)
        if rc == 0:
            _, after = stdout.strip().split('Repositories loaded.', 1)
            lines = after.lstrip().strip().split('\n')
            for line in lines:
                bits = re.split(r'\s+', line)
                data['packages'].append(
                    Package(
                        CurrentVersion=bits[1],
                        Name=bits[0]
                    )
                )
        else:
            data['success'] = False
            data['error'] = f'Failed to execute "{command}"'
    else:
        data['success'] = False
        data['error'] = f'{binary} is not installed'

    # This is here to test locally as I don't have yum
    # with open(os.path.join(util.get_config_directory(), 'yum-output.txt'), 'r', encoding='utf-8') as f:
    #     stdout = f.read()
    #     _, after = stdout.strip().split('Repositories loaded.', 1)
    #     lines = after.lstrip().strip().split('\n')
    #     for line in lines:
    #         bits = re.split(r'\s+', line)
    #         data['packages'].append(
    #             Package(
    #                 CurrentVersion=bits[1],
    #                 Name=bits[0]
    #             )
    #         )

    return data

def find_updates(package_type: str=''):
    if package_type == 'apt':
        return find_apt_updates()
    elif package_type == 'brew':
        return find_brew_updates()
    elif package_type == 'dnf':
        return find_dnf_updates()
    elif package_type == 'flatpak':
        return find_flatpak_updates()
    elif package_type == 'mintupdate':
        return find_mint_updates()
    elif package_type == 'yum':
        return find_yum_updates()
    # snap uses "snap refresh"

def main():
    valid_types = ['apt', 'brew', 'dnf', 'flatpak', 'mintupdate', 'snap', 'yum']
    parser = argparse.ArgumentParser(description='Check available system updates from different sources')
    parser.add_argument('-t', '--type', help=f'The type of update to query; valid choices are: {', '.join(valid_types)}', required=True)
    args = parser.parse_args()

    if not util.network_is_reachable():
        print(f'{util.color_title(glyphs.md_network_off_outline)} {util.color_error(args.type)} {util.color_error("the network is unreachable")}')
        sys.exit(1)

    update_info = find_updates(package_type=args.type)
    
    if update_info['success']:
        packages = 'package' if len(update_info['packages']) == 1 else 'packages'
        print(f'{util.color_title(glyphs.md_package_variant)} {util.color_title(args.type)} {len(update_info["packages"])} outdated {packages}')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.md_package_variant)} {util.color_error(args.type)} {util.color_error(update_info["error"])}')
        sys.exit(1)

if __name__ == "__main__":
    main()
