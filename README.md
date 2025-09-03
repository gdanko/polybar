# polybar

## Introduction
I use [Xbar](https://xbarapp.com) and [SwiftBar](https://swiftbar.app) on my Macs and I really enjoy their functionality. I was looking for something similar in the Linux world and stumbled across [Polybar](https://polybar.github.io). While it doesn't offer quite the same level as power that the others do, e.g, hierarchical menus and so forth, it suits my needs nicely. In this repo, I've ported many of my Mac equivalents to Linux as Polybar scripts, written in Python. I use [NerdFonts](https://www.nerdfonts.com) to display glyphs for most of the scripts. I hope you enjoy my work.

## Installation
* `cd` to `~/.config`
* Clone this repository

## The scripts
* `brew-outdated.py` - This script looks for outdated [linuxbrew](https://docs.brew.sh/Homebrew-on-Linux) casks and formulae and displays the count.
* `cpu-usage.py` - This script shows CPU utilization in the format: `user 2.13%, sys 0.92%, idle 96.73%`. It relies on `mpstat` which is part of the `sysstat` package. If `mpstat` isn't available, you'll be asked to install `sysstat`.
* `filesystem-usage.py` - This script shows disk usage in the format: `<used> GiB / <total> GiB`. This script uses `df -B 1` to gather the data.
* `filesystem-usage-clickable.py` - This is a version of `filesystem-usage.py` that allows you to click on the item in the bar to cycle through several output formats.
* `filesystem-usage-formatted.py` - This is a version of `filesystem-usage.py` that has a `--format` flag which allows you to specify a custom output format. Formatting details will be discussed below.
* `memory-usage.py` - This script shows memory usage in the format: `<used> GiB / <total> GiB`. This script uses `free -b -w` to gather the data.
* `memory-usage-clickable.py` - This is a version of `memory-usage.py` that allows you to click on the item in the bar to cycle through several output formats.
* `memory-usage-formatted.py` - This is a version of `memory-usage.py` that has a `--format` flag which allows you to specify a custom output format. Formatting details will be discussed below.
* `polybar-speedtest.py` - This script connects to [speedtest.net](https://speedtest.net) and displays current upload and download speeds. It's an enhanced version of this awseome [script](https://github.com/haideralipunjabi/polybar-speedtest/tree/main).
* `stock-quotes.py` - This script shows basic information about a given stock symbol. It shows the symbol, last price, change amount and percent. It uses [Yahoo! Finance](https://finance.yahoo.com) to gather the data so please use a sane interval as Yahoo! is quick to rate-limit you.
* `weather.py` - This script pulls weather data from [Weather API](https://weatherapi.com). You will need to get a free API key from this site to use it. The output shows location name, current temperature, and daily high and low temperatures.
* `wifi-status.py` - This script uses `iwconfig` to display the current signal strength for the specified interface.

### Notes
* The `filesystem-usage*.py` and `memory-usage*.py` scripts have a `--unit` flag that allows you to force the unit the output is displayed in.
* Valid units for the `--unit` flag are `K, Ki, M, Mi, G, Gi, T, Ti, P, Pi, E, Ei, Z, Zi, auto` with the default being `auto`.
* The `auto` option will intelligently determine which unit to use, depending on the number. For example, if you're using 50.2 GiB on a 4 TiB drive, `auto` would render the output to look like this `50.2 GiB / 4.0 TiB`, where selecting the `Ti` unit would give you `0.05 TiB / 4.0 Tib`. While I enjoy having the flexibility, I think it's a little easier to read the results when using `auto` as a unit.
* The `filesystem-usage-clickable.py` uses a hack to overcome the limitation where `click-*` doesn't allow `env-*` variables. Each inherited instances has a variable `env-toggle_script` which is the name of the script that will be created to toggle the output format. It's passed via the `--toggle-script` flag. A small shell script is generated and `chmod 755`'d. The `click-left` action is simply to call this script. It's kludgy, but it works.

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

## Configuration
This is how I have set up my `config.ini` to use these scripts

```
[filesystem-base-formatted]
type = custom/script
interval = 25
env-format = "{^used / ^total}"
env-unit = "auto"
exec = ~/.config/polybar/scripts/filesystem-usage-formatted.py --mountpoint "$mountpoint" --format "$format" --unit "$unit"

[module/filesystem-root]
inherit = filesystem-base
env-mountpoint = "/"

[module/filesystem-work]
inherit = filesystem-base
env-mountpoint = "/work"

[filesystem-usage-clickable-base]
type = custom/script
interval = 2
env-unit = "auto"
exec = ~/.config/polybar/scripts/filesystem-usage-clickable.py --mountpoint "$mountpoint" --unit "$unit" --toggle-script "$toggle_script"

[module/filesystem-usage-clickable-root]
inherit = filesystem-usage-clickable-base
env-mountpoint = "/"
env-unit = "auto"
env-toggle_script = "/tmp/toggle-gdanko-root.sh"
click-left = /tmp/toggle-gdanko-root.sh

[module/filesystem-usage-clickable-work]
inherit = filesystem-usage-clickable-base
env-mountpoint = "/work"
env-unit = "auto"
env-toggle_script = "/tmp/toggle-gdanko-work.sh"
click-left = /tmp/toggle-gdanko-work.sh

[module/memory-usage]
type = custom/script
interval = 2
exec = ~/.config/polybar/scripts/memory-usage.py

[module/memory-usage-clickable]
type = custom/script
interval = 1
exec = ~/.config/polybar/scripts/memory-usage-clickable.py
click-left = ~/.config/polybar/scripts/memory-usage-clickable.py --toggle

[module/memory-usage-formatted]
type = custom/script
interval = 2
env-format = "{^used! / ^total!}"
env-unit = "auto"
exec = ~/.config/polybar/scripts/memory-usage-formatted.py --format "$format" --unit "$unit"

[module/cpu]
type = custom/script
interval = 2
exec = ~/.config/polybar/scripts/cpu-usage.py

[wlan-base]
type = custom/script
interval = 2
exec = ~/.config/polybar/scripts/wifi-status.py --interface "$interface"

[module/wlan-wlo1]
inherit = wlan-base
env-interface = "wlo1"

[weather-base]
type = custom/script
interval = 900
env-api_key = "<your api key>"
exec = ~/.config/polybar/scripts/weather.py --api-key "$api_key" --location "$location"

[module/weather-denver]
inherit = weather-base
env-location = "Denver, CO, US"

[stocks-base]
type = custom/script
interval = 900
exec = ~/.config/polybar/scripts/stock-quotes.py --symbol "$symbol"

[module/stocks-goog]
inherit = stocks-base
env-symbol = "GOOG"
```

## To Do
* Try to figure out if there is a way to click on each item for multiple formats, like the date module

