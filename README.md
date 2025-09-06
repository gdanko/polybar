# polybar

## Introduction
I use [Xbar](https://xbarapp.com) and [SwiftBar](https://swiftbar.app) on my Macs and I really enjoy their functionality. I was looking for something similar in the Linux world and stumbled across [Polybar](https://polybar.github.io). While it doesn't offer quite the same level as power that the others do, e.g, hierarchical menus and so forth, it suits my needs nicely. In this repo, I've ported many of my Mac equivalents to Linux as Polybar scripts, written in Python. I use [NerdFonts](https://www.nerdfonts.com) to display glyphs for most of the scripts. I hope you enjoy my work.

## Installation
* `cd` to `~/.config`
* Clone this repository

## The scripts
* `cpu-usage.py` - This script shows CPU utilization in the format: `user 2.13%, sys 0.92%, idle 96.73%`. It relies on `mpstat` which is part of the `sysstat` package. If `mpstat` isn't available, you'll be asked to install `sysstat`.
* `filesystem-usage.py` - This script shows disk usage in the format: `<used> GiB / <total> GiB`. This script uses `df -B 1` to gather the data.
* `filesystem-usage-clickable.py` - This is a version of `filesystem-usage.py` that allows you to click on the item in the bar to cycle through several output formats.
* `filesystem-usage-formatted.py` - This is a version of `filesystem-usage.py` that has a `--format` flag which allows you to specify a custom output format. Formatting details will be discussed below.
* `memory-usage.py` - This script shows memory usage in the format: `<used> GiB / <total> GiB`. This script uses `free -b -w` to gather the data.
* `memory-usage-clickable.py` - This is a version of `memory-usage.py` that allows you to click on the item in the bar to cycle through several output formats.
* `memory-usage-formatted.py` - This is a version of `memory-usage.py` that has a `--format` flag which allows you to specify a custom output format. Formatting details will be discussed below.
* `polybar-speedtest.py` - This script connects to [speedtest.net](https://speedtest.net) and displays current upload and download speeds. It's an enhanced version of this awseome [script](https://github.com/haideralipunjabi/polybar-speedtest/tree/main). I added another hack [here](#speedtest-hack) for putting a `Loading...` placeholder while the script fetches the data.
* `stock-quotes.py` - This script shows basic information about a given stock symbol. It shows the symbol, last price, change amount and percent. It uses [Yahoo! Finance](https://finance.yahoo.com) to gather the data so please use a sane interval as Yahoo! is quick to rate-limit you.
* `system-updates.py` - This script is able to query a number of different package managers and return the number of available updates. Currently supported are: `apt`, `brew`, `dnf`, `flatpak`, `mintupdate`, `pacman`, `snap`, `yay`, `yay-aur`, and `yum`.
* `weather.py` - This script pulls weather data from [Weather API](https://weatherapi.com). You will need to get a free API key from this site to use it. The output shows location name, current temperature, and daily high and low temperatures.
* `wifi-status.py` - This script uses `iwconfig` to display the current signal strength for the specified interface.

### Notes
* The `filesystem-usage*.py` and `memory-usage*.py` scripts have a `--unit` flag that allows you to force the unit the output is displayed in.
* Valid units for the `--unit` flag are `K, Ki, M, Mi, G, Gi, T, Ti, P, Pi, E, Ei, Z, Zi, auto` with the default being `auto`.
* The `auto` option will intelligently determine which unit to use, depending on the number. For example, if you're using 50.2 GiB on a 4 TiB drive, `auto` would render the output to look like this `50.2 GiB / 4.0 TiB`, where selecting the `Ti` unit would give you `0.05 TiB / 4.0 Tib`. While I enjoy having the flexibility, I think it's a little easier to read the results when using `auto` as a unit.
* The `*-clickable.py` scripts use a hack to allow both clickability AND running on an interval. Use cases include when I want to click on my CPU usage module to see different output formats. This will be explained in the [Clickability](#clickability) section.

## Formatting disk and memory usage output
There are currently six tokens that can be used to format the output when using `filesystem-usage-formatted.py` and `memory-usage-formatted.py`:
* `^total`     - Total available memory/disk
* `^used`      - Used memory/disk
* `^free`      - Free memory/disk
* `^pct_total` - Total percentage of available memory/disk (yes, always 100)
* `^pct_used`  - Percentage of available memory/disk in use
* `^pct_free`  - Percentage of available memory/disk free

### Formatting examples
Glyphs and formatting noise have been removed for readbility's sake. In the last example, all I did was change the display unit.
```
% ./scripts/memory-usage-formatted.py --format '{^pct_used used out of a total of ^total}'
17% used out of a total of 59.75 GiB

% ./scripts/memory-usage-formatted.py --format '{^used / ^total}'
10.12 GiB / 59.75 GiB

% ./scripts/filesystem-usage-formatted.py --mountpoint "/work" --format '{^used (or ^pct_used) out of ^total}'
/work 1.21 TiB (or 36%) out of 3.58 TiB

% ./scripts/filesystem-usage-formatted.py --mountpoint "/work" --format '{^used (or ^pct_used) out of ^total}' --unit Gi
/work 1236.41 GiB (or 36%) out of 3666.49 GiB
```

## Clickability
My goal was to have a module that would both run on an interval and also be clickable. By default, it seems these two are mutually exclusive. The `custom/script` type allows me to use the `interval` parameter but doesn't allow me use the features of `custom/ipc`, such as sending messages via `polybar-msg`. You can see my frustration. Fortunately I was able to find a workaround in the form of a bit of a hack. Let's look at a single example.
```
[module/memory-usage-clickable]
type = custom/ipc
label = %output%
initial = 1
hook-0 = ~/.config/polybar/scripts/memory-usage-clickable.py --unit auto
click-left = ~/.config/polybar/scripts/memory-usage-clickable.py --unit auto --toggle && polybar-msg action memory-usage-clickable hook 0
daemonize = true
daemonize-arg-interval = 2
```
When the module is executed, `hook-0` is called, which simply displays the default output. The `click-left` action executes the script with `--toggle`, which updates the output format via state file. It also displays the output in the new format.

To accomplish executing these scripts on an interval, I've added two flags, `--daemonize` and `--interval`. The `daemonize-*` parameters are parsed by `launch.py` (which is invoked by the required `launch.sh`). There is logic to manage these scripts so that there aren't multiple copies of them running, etc. Anyhow, when `launch.py` is executed, there is a function that daemonizes the modules that currently support this. In a future release, `launch.py` will do this without them being hardcoded.

Upon invocation, `launch.py` does the following:
1. Configures the logger
2. Verifies both `polybar` and `polybar-msg` are in the PATH
3. Determines the path of the configuration file
4. Parses the configuration file
5. Determines if IPC is enabled and kills polybar using either `polybar-msg` or `kill`
6. Re-launches polybar
7. Daemonizes modules that are configured to do so

If any step in the process fails, the script exits with an explanation as to what caused the failure.

Note, at every interval, a daemonized script will check to see if polybar is running. If it is not running, the script exits on its own. Scripts with a longer interval, e.g., `polybar-speedtest` will take a fair amount of time to exit on their own because it may be in a sleep state.

## Speedtest Hack
If there is an official way of doing this, please do tell me. :) I wrote the Speedtest script, but the output wouldn't render until the script completed. It didn'tlike that because the module would just pop in and say "Hello! I'm all done, here are the results!" I wanted something to say show, "Hey, I'm doing work here, please hang tight."
```
[module/polybar-speedtest]
type = custom/ipc
label = %output%
initial = 1
hook-0 = echo "%{F#F0C674}%{F-} Speedtest running..."
daemonize = true
daemonize-arg-download =
daemonize-arg-upload =
daemonize-arg-interval = 300
```
All the module does is set the initial text, which is a loading message. But using `launch.py`, I am able to daemonize this module. So as soon as the loading message is up, the script is working in the background, running the test(s). When the script is daemonized, it displays the loading text right before it starts the test(s), so you're always aware that it's working.

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
```

## Configuration
Please see `config.ini.example` to see how I wired everything
