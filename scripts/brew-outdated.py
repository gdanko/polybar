#!/usr/bin/env python3

from polybar import glyphs, util
from typing import Dict, List, NamedTuple, Tuple, Union
import json
import sys

class Package(NamedTuple):
    CurrentVersion: str
    InstalledVersions: List[str]
    Name: str

def get_brew_data() -> Tuple[Union[Dict[str, List[Package]], None], Union[str, None]]:
    if not util.is_binary_installed('brew'):
        return None, 'homebrew isn\'t installed'

    command = 'brew update'
    rc, _, stderr = util.run_piped_command(command)
    if rc != 0:
        if stderr != '':
            if 'process is already running' in stderr:
                return None, 'another "brew update" process is running'
        return None, f'Failed to execute "{command}"'
    
    command = 'brew list --installed-on-request'
    rc, stdout, _ = util.run_piped_command(command)
    if rc != 0:
        return None, f'Failed to execute "{command}"'
    manually_installed = {line for line in stdout.splitlines()}

    command = 'brew outdated --json'
    rc, stdout, _ = util.run_piped_command(command)
    if rc != 0:
        return None, f'Failed to execute "{command}"'
    
    try:
        formulae: List[Package] = []
        casks: List[Package] = []
        data = json.loads(stdout)
        for obj in data['formulae']:
            if obj['name'] in manually_installed:
                formulae.append(
                    Package(
                        Name=obj['name'],
                        CurrentVersion=obj['current_version'],
                        InstalledVersions=obj['installed_versions'],
                    )
                )
        for obj in data['casks']:
            casks.append(
                Package(
                    Name=obj['name'],
                    CurrentVersion=obj['current_version'],
                    InstalledVersions=obj['installed_versions'],
                )
            )

        if type(formulae) == list and type(casks) == list:
            return {'Formulae': formulae, 'Casks': casks}, None
        else:
            return None, 'Invalid data returned from brew'
    except Exception as e:
        return None, f'Failed to parse JSON output from "{command}": {e}'

def main() -> None:
    data, err = get_brew_data()
    if err:
        print(f'{util.color_title(glyphs.md_package_variant)} {util.color_error(err)}')
        sys.exit(1)

    total = len(data['Formulae']) + len(data['Casks'])
    packages = 'package' if total == 1 else 'packages'


    print(f'{util.color_title(glyphs.md_package_variant)} {util.color_title("brew")} {total} outdated {packages}')

if __name__ == '__main__':
    main()
