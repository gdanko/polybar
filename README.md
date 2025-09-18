# polybar

## Introduction
I use [Xbar](https://xbarapp.com) and [SwiftBar](https://swiftbar.app) on my Macs and I really enjoy their functionality. I was looking for something similar in the Linux world and stumbled across [Polybar](https://polybar.github.io). While it doesn't offer quite the same level as power that the others do, e.g, hierarchical menus and so forth, it suits my needs nicely. In this repo, I've ported many of my Mac equivalents to Linux as Polybar scripts, written in Python. I use [NerdFonts](https://www.nerdfonts.com) to display glyphs for most of the scripts. I hope you enjoy my work.

## Installation
* `cd` to `~/.config`
* Clone this repository

## Modules

### CPU Usage
This module shows CPU information with four available output formats that can be toggled by clicking the item in the bar.

#### Output Formats
1. `user 0.99%, sys 0.46%, idle 98.43%`
2. `load 0.20,  0.27,  0.44`
3. `8C/16T x AMD Ryzen 7 5700U`
4. `current: 3.29 GHz, min: 400 Mhz, max: 4.37 GHz`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
```
[module/cpu-usage]
type = custom/ipc
label = %output%
initial = 1
hook-0 = ~/.config/polybar/scripts/cpu-usage.py
click-left = ~/.config/polybar/scripts/cpu-usage.py --toggle && polybar-msg action cpu-usage hook 0
background = true
background-arg-interval = 2
```

### Filesystem Usage
This module shows filesystem usage information with three available output formats that can be toggled by clicking the item in the bar.

#### Output Formats
1. `/foo 779.39 GiB / 3.58 TiB`
2. `/foo 22% used`
3. `/foo 779.41 GiB used / 2.64 TiB free`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
```
[filesystem-usage-base]
type = custom/ipc
initial = 1
label = %output%

[module/filesystem-usage-root]
inherit = filesystem-usage-base
; How to use variables here?
; env-mountpoint = /
; env-unit = "auto"
hook-0 = ~/.config/polybar/scripts/filesystem-usage.py --mountpoint / --unit auto
click-left = ~/.config/polybar/scripts/filesystem-usage.py --mountpoint / --unit auto --toggle && polybar-msg action filesystem-usage-root hook 0
background = true
background-script = filesystem-usage.py
background-arg-mountpoint = /
background-arg-label = root
background-arg-interval = 30
```

### Memory Usage
This module shows memory usage information with four available output formats that can be toggled by clicking the item in the bar. This module relies on `dmidecode` so please see the [permissions](#permissions) section before implementing this module.

#### Output Formats
1. `8.04 GiB / 59.75 GiB`
2. `13% used`
3. `8.03 GiB used / 51.72 GiB free`
4. `2 x 32GB SODMIMM @ 3200 MT/s`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
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

### Speedtest
This module connects to [speedtest.net](https://speedtest.net) and gathers download and/or upload speeds. You can left click on it to refresh its output. I added another hack [here](#speedtest-hack) for putting a `Running speedtest...` placeholder while the script fetches the data.

#### Output Formats
1. `<icon> ↓403.13 Mbit/s ↑493.98 Mbit/s`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
```
[module/polybar-speedtest]
type = custom/ipc
label = %output%
; Run both commands on startup:
;   hook-0 = show results (last test or "loading")
;   hook-1 = start a new test in the background
initial = 1
hook-0 = ~/.config/polybar/scripts/polybar-speedtest.py show
hook-1 = ~/.config/polybar/scripts/polybar-speedtest.py run
; On click, trigger a new test
click-left = ~/.config/polybar/scripts/polybar-speedtest.py run
background = true
background-action = run
background-arg-interval = 300
background-arg-download =
background-arg-upload =
```

#### Notes
The speedometer icon is dynamic. It shows slow, medium, or fast depending on the following:
- If only the download test is enabled, the icon is based on download speed.
- If only the upload test is enabled, the icon is based on the upload speed.
- If both download and upload tests are enabled, the icon is based on and average of both speeds.

### Stock Quotes
This module contacts [Yahoo! Finance](https://finance.yahoo.com) and gathers basic information about stock symbols.

##### Output Formats
1. `GOOG $241.38 ↑0.60 (0.25%)`

##### Configuration
```
[stocks-base]
type = custom/script
interval = 900
exec = ~/.config/polybar/scripts/stock-quotes.py --symbol "$symbol"

[module/stocks-goog]
inherit = stocks-base
env-symbol = GOOG

[module/stocks-msft]
inherit = stocks-base
env-symbol = MSFT
```

### Swap Usage
This module shows swap usage information with three available output formats that can be toggled by clicking the item in the bar.

#### Output Formats
1. `0.00 B / 1.91 GiB`
2. `0% used`
3. `0.00 B used / 1.91 GiB free`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
```
[module/swap-usage]
type = custom/ipc
label = %output%
initial = 1
hook-0 = ~/.config/polybar/scripts/swap-usage.py --unit auto
click-left = ~/.config/polybar/scripts/swap-usage.py --unit auto --toggle && polybar-msg action swap-usage hook 0
background = true
background-arg-interval = 2
```

### System Updates
This module displays the number of available outputs for the following package managers: `apt`, `brew`, `dnf`, `flatpak`, `mintupdate`, `pacman`, `snap`, `yay`, `yay-aur`, `yum`. Please see the [permissions](#permissions) section before implementing this module.

#### Output Formats
1. `apt 0 outdated packages`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
```
[system-updates-base]
type = custom/ipc
label = %output%
initial = 1

[module/system-updates-apt]
inherit = system-updates-base
hook-0 = ~/.config/polybar/scripts/system-updates.py show --type apt
hook-1 = ~/.config/polybar/scripts/system-updates.py run --type apt
click-left = ~/.config/polybar/scripts/system-updates.py run --type apt
background = true
background-action = run
background-script = system-updates.py
background-arg-interval = 1800
background-arg-type = apt
```

#### Notes
For non Ubuntu-based systems, I've tested using simulated data in text files. If you find something isn't working, please create an issue.

### Weather
This module retrieves weather from [weatherapi.com](https://www.weatherapi.com) and has five available output formats.

#### Output Formats
1. `San Diego 73.0°F`
2. `San Diego ↑76.5°F ↓64.6°F`
3. `San Diego <wind icon> 9.6 mph @ 267°`
4. `San Diego <sunrise icon> 06:32 <sunset icon> 18:55`
5. `San Diego <moonrise icon> 23:06 <moonset icon> 14:25`

#### Configuration
In order for it to be launched in the background, you will need to launch it via `launch.py` or a script with similar functionality. The `background-*` parameters are used to instruct `launch.py` how to properly put the module's worker in the background.
```
[weather-base]
type = custom/ipc
label = %output%
initial = 1

[module/weather-san-diego]
inherit = weather-base
hook-0 = ~/.config/polybar/scripts/weather.py show --location "San Diego, CA, US" --label "san-diego"
hook-1 = ~/.config/polybar/scripts/weather.py run --location "San Diego, CA, US" --api-key "<your_weather_api_key>" --label "san-diego"
click-left = ~/.config/polybar/scripts/weather.py run --api-key "<your_weather_api_key>" --location "San Diego, CA, US" --label "san-diego" --toggle
click-right = ~/.config/polybar/scripts/weather.py run --api-key "<your_weather_api_key>" --location "San Diego, CA, US" --label "san-diego"
background = true
background-action = run
background-script = weather.py
background-arg-api-key = <your_weather_api_key>
background-arg-location = "San Diego, CA, US"
background-arg-label = san-diego
background-arg-interval = 300
```

### Wi-Fi Status
This module displays the signal strength in dBm for the specified interface.

#### Output Formats
1. `wlo1 -48 dBm`

#### Configuration
```
[wlan-base]
type = custom/script
interval = 10
exec = ~/.config/polybar/scripts/wifi-status.py --interface "$interface"

[module/wlan-wlo1]
inherit = wlan-base
env-interface = wlo1
```

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
If there is an official way of doing this, please do tell me. :) I wrote the Speedtest script, but the output wouldn't render until the script completed. I didn't like that because the module would just pop in and say "Hello! I'm all done, here are the results!" I wanted something to say, "Hey, I'm doing work here, please hang tight."
```
[module/speedtest]
type = custom/ipc
label = %output%
initial = 2
hook-0 = ~/.config/polybar/scripts/speedtest.py show
hook-1 = ~/.config/polybar/scripts/speedtest.py run
click-left = ~/.config/polybar/scripts/speedtest.py run
```
When executed, `hook-1` is executed because `initial = 2`. The `run` action first writes the loading text to the temp file and then executes the test in the backround and immediately exectutes `hook-0`, which executions the script with the `show` action.

## Permissions
You will need to add yourself to `/etc/sudoers` in order to execute some commands. Do something like this. Obviously pick only the ones you need.

### For Systems Update
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

### For Memory Usage
```
user ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode
```

## Configuration
Please see `config.ini.example` for more details
