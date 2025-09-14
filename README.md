# polybar

## Introduction
I use [Xbar](https://xbarapp.com) and [SwiftBar](https://swiftbar.app) on my Macs and I really enjoy their functionality. I was looking for something similar in the Linux world and stumbled across [Polybar](https://polybar.github.io). While it doesn't offer quite the same level as power that the others do, e.g, hierarchical menus and so forth, it suits my needs nicely. In this repo, I've ported many of my Mac equivalents to Linux as Polybar scripts, written in Python. I use [NerdFonts](https://www.nerdfonts.com) to display glyphs for most of the scripts. I hope you enjoy my work.

## Installation
* `cd` to `~/.config`
* Clone this repository

## The scripts
* `cpu-usage.py` - This script shows CPU utilization in the format: `user 2.13%, sys 0.92%, idle 96.73%`. It relies on `mpstat` which is part of the `sysstat` package. If `mpstat` isn't available, you'll be asked to install `sysstat`.
* `filesystem-usage.py` - Filesystem usage module that allows you to click on the item in the bar to cycle through several output formats.
* `memory-usage.py` - Memory usage module that allows you to click on the item in the bar to cycle through several output formats.
* `speedtest.py` - This script connects to [speedtest.net](https://speedtest.net) and displays current upload and download speeds. It's an enhanced version of this awseome [script](https://github.com/haideralipunjabi/polybar-speedtest/tree/main). I added another hack [here](#speedtest-hack) for putting a `Loading...` placeholder while the script fetches the data.
* `stock-quotes.py` - This script shows basic information about a given stock symbol. It shows the symbol, last price, change amount and percent. It uses [Yahoo! Finance](https://finance.yahoo.com) to gather the data so please use a sane interval as Yahoo! is quick to rate-limit you.
* `swap-usage.py` - Swap usage module that allows you to click on the item in the bar to cycle through several output formats.
* `system-updates.py` - This script is able to query a number of different package managers and return the number of available updates. Currently supported are: `apt`, `brew`, `dnf`, `flatpak`, `mintupdate`, `pacman`, `snap`, `yay`, `yay-aur`, and `yum`. Please see the [permissions](#permissions) section before implementing this module.
* `weather.py` - This script pulls weather data from [Weather API](https://weatherapi.com). You will need to get a free API key from this site to use it. This module allows you to left click on its item in the bar to change formats. Right clicking will simply update the current view.
* `wifi-status.py` - This script uses `iwconfig` to display the current signal strength for the specified interface.

### Notes
* The `filesystem-usage.py`, `memory-usage.py`, and `swap-usage.py` scripts have a `--unit` flag that allows you to force the unit the output is displayed in.
* Valid units for the `--unit` flag are `K, Ki, M, Mi, G, Gi, T, Ti, P, Pi, E, Ei, Z, Zi, auto` with the default being `auto`.
* The `auto` option will intelligently determine which unit to use, depending on the number. For example, if you're using 50.2 GiB on a 4 TiB drive, `auto` would render the output to look like this `50.2 GiB / 4.0 TiB`, where selecting the `Ti` unit would give you `0.05 TiB / 4.0 Tib`. While I enjoy having the flexibility, I think it's a little easier to read the results when using `auto` as a unit.
* Some scripts use a hack to allow both clickability AND running on an interval. Use cases include when I want to click on my CPU usage module to see different output formats. This will be explained in the [Clickability](#clickability) section.
* The `filesystem-usage.py` and `weather.py` modules have a required `--label` flag which allows the script to save its state and output in files that are unique to the instance it's running. The label should be the last portion of the module's defined name, e.g., with `[module/filesystem-usage-root]`, the label should be `root`. This is to allow the `filesystem-usage.py` script to properly invoke `polybar-msg` to manipulate the module.

## Clickability
My goal was to have a module that would both run on an interval and also be clickable. By default, it seems these two are mutually exclusive. The `custom/script` type allows me to use the `interval` parameter but doesn't allow me use the features of `custom/ipc`, such as sending messages via `polybar-msg`. You can see my frustration. Fortunately I was able to find a workaround in the form of a bit of a hack. Let's look at a single example.
```
[module/memory-usage]
type = custom/ipc
label = %output%
initial = 1
hook-0 = ~/.config/polybar/scripts/memory-usage.py --unit auto
click-left = ~/.config/polybar/scripts/memory-usage.py --unit auto --toggle && polybar-msg action memory-usage hook 0
background = true
background-arg-interval = 5
```
When the module is executed, `hook-0` is called, which simply displays the default output. The `click-left` action executes the script with `--toggle`, which updates the output format via state file. It also displays the output in the new format.

To accomplish executing these scripts on an interval, I've added two flags, `--background` and `--interval`. The `background-*` parameters are parsed by `launch.py` (which is invoked by the required `launch.sh`). There is logic to manage these scripts so that there aren't multiple copies of them running, etc. Anyhow, when `launch.py` is executed, there is a function that launch modules that currently support this in background. In a future release, `launch.py` will do this without them being hardcoded.

Upon invocation, `launch.py` does the following:
1. Configures the logger
2. Verifies both `polybar` and `polybar-msg` are in the PATH
3. Determines the path of the configuration file
4. Parses the configuration file
5. Determines if IPC is enabled and kills polybar using either `polybar-msg` or `kill`
6. Re-launches polybar
7. Launches scripts that support being launched into the background

If any step in the process fails, the script exits with an explanation as to what caused the failure.

Note, at every interval, a backgrounded script will check to see if polybar is running. If it is not running, the script exits on its own. Scripts with a longer interval, e.g., `polybar-speedtest` will take a fair amount of time to exit on their own because it may be in a sleep state.

## Speedtest Hack
If there is an official way of doing this, please do tell me. :) I wrote the Speedtest script, but the output wouldn't render until the script completed. It didn'tlike that because the module would just pop in and say "Hello! I'm all done, here are the results!" I wanted something to say show, "Hey, I'm doing work here, please hang tight."
```
[module/speedtest]
type = custom/ipc
label = %output%
initial = 2
hook-0 = ~/.config/polybar/scripts/speedtest.py show
hook-1 = ~/.config/polybar/scripts/speedtest.py run
click-left = ~/.config/polybar/scripts/speedtest.py run
```
When executed, `hook-1` is executed because `initial = 2`. The `run` action first writes the loading test to the temp file and then executes the test in the backround and immediately exectutes `hook-0`, which executions the script with the `show` action.

## Permissions
You will need to add yourself to `/etc/sudoers` in order to execute some commands. Do something like this. Obviously pick only the ones you need.
```
# mint has a wrapper in /usr/local/bin
user ALL=(ALL) NOPASSWD: /usr/local/bin/apt
user ALL=(ALL) NOPASSWD: /usr/bin/apt
user ALL=(ALL) NOPASSWD: /usr/bin/dnf
user ALL=(ALL) NOPASSWD: /usr/bin/flatpak
user ALL=(ALL) NOPASSWD: /usr/bin/mintupdate-cli
user ALL=(ALL) NOPASSWD: /usr/bin/snap
user ALL=(ALL) NOPASSWD: /usr/bin/yay
user ALL=(ALL) NOPASSWD: /usr/bin/yum
user ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode
```

## Configuration
Please see `config.ini.example` to see how I wired everything

## To Do
Dynamically parse the bars and launch them all
