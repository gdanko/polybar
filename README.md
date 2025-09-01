# polybar

## Introduction
I use [Xbar](https://xbarapp.com) and [SwiftBar](https://swiftbar.app) on my Macs and I really enjoy their functionality. I was looking for something similar in the Linux world and stumbled across [Polybar](https://polybar.github.io). While it doesn't offer quite the same level as power that the others do, e.g, hierarchical menus and so forth, it suits my needs nicely. In this repo, I've ported many of my Mac equivalents to Linux as Polybar scripts, written in Python. I use [NerdFonts](https://www.nerdfonts.com) to display glyphs for most of the scripts. I hope you enjoy my work.

## Installation
* `cd` to `~/.config`
* Clone this repository

## The Scripts
* `cpu-usage.py` - This script shows CPU utilization in the format: `user 2.13%, sys 0.92%, idle 96.73%`. It relies on `mpstat` which is part of the `sysstat` package. If `mpstat` isn't available, you will be asked to install `sysstat`.
* `disk-usage.py` - This script shows disk usage in the format: `<used> GiB / <total> GiB`. This script uses `df -B 1` to gather the data. It has an optional `--unit` flag that allows you to force the unit you want to display it in.
* `memory-usage.py` - This script shows memory usage in the format: `<used> GiB / <total> GiB`. This script uses `free -b -w` to gather the data. It has an optional `--unit` flag that allows you to force the unit you want to display it in.
* `stock-quotes.py` - This script shows basic information about a given stock symbol. It shows the symbol, last price, change amount and percent. It uses [Yahoo! Finance](https://finance.yahoo.com) to gather the data so please use a sane interval as Yahoo! is quick to rate-limit you.
* `weather.py` - This script pulls weather data from [Weather API](https://weatherapi.com). You will need to get a free API key from this site to use it. The output shows location name, current temperature, and daily high and low temperatures.
* `wifi-status.py` - This script uses `iwconfig` to display the current signal strength for the specified interface.

## Formatting disk and memory usage output
There are currently six tokens that can be used to format the output:
* `^total`     - Total available memory/disk
* `^used`      - Used memory/disk
* `^free`      - Free memory/disk
* `^pct_total` - Total percentage of available memory/disk (yes, always 100)
* `^pct_used`  - Percentage of available memory/disk in use
* `^pct_free`  - Percentage of available memory/disk free

### Formatting examples
Glyphs and formatting noise have been removed for readbility's sake. In the last example, all I did was change the display unit.
```
% ./scripts/memory-usage-test.py --format '{^pct_used used out of a total of ^total}'
17% used out of a total of 59.75 GiB

% ./scripts/memory-usage-test.py --format '{^used / ^total}'
10.12 GiB / 59.75 GiB

% ./scripts/disk-usage-test.py --mountpoint "/work" --format '{^used (or ^pct_used) out of ^total}'
/work 1.21 TiB (or 36%) out of 3.58 TiB

% ./scripts/disk-usage-test.py --mountpoint "/work" --format '{^used (or ^pct_used) out of ^total}' --unit Gi
/work 1236.41 GiB (or 36%) out of 3666.49 GiB
```

## Configuration
This is how I have set up my `config.ini` to use these scripts

```
[filesystem-base]
type = custom/script
interval = 25
exec = ~/.config/polybar/scripts/disk-usage.py --mountpoint "$mountpoint"

[module/filesystem-root]
inherit = filesystem-base
env-mountpoint = "/"

[module/filesystem-work]
inherit = filesystem-base
env-mountpoint = "/work"

[module/memory]
type = custom/script
interval = 2
exec = ~/.config/polybar/scripts/memory-usage.py

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

[module/weather-san-diego]
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

