#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, state, util
from urllib.parse import quote, urlunparse
from typing import Any, Dict, List, Optional, NamedTuple
from urllib.request import urlopen, Request
import json
import logging
import os
import subprocess
import sys
import urllib.request

util.validate_requirements(required=['click'])

import click

_label: str |None=None
_location: str | None=None

class WeatherData(NamedTuple):
    success           : Optional[bool]  = False
    error             : Optional[str]   = None
    icon              : Optional[str]   = None
    avg_humidity      : Optional[int]   = 0
    condition_code    : Optional[int]   = 0
    country           : Optional[str]   = None
    dewpoint          : Optional[str]   = None
    current_temp      : Optional[str]   = None
    feels_like        : Optional[str]   = None
    gust              : Optional[str]   = None
    heat_index        : Optional[str]   = None
    humidity          : Optional[str]   = None
    location_full     : Optional[str]   = None
    location_short    : Optional[str]   = None
    moonrise          : Optional[str]   = None
    moonset           : Optional[str]   = None
    moon_illumination : Optional[int]   = 0
    precipitation     : Optional[str]   = None
    region            : Optional[str]   = None
    sunrise           : Optional[str]   = None
    sunset            : Optional[str]   = None
    todays_high       : Optional[str]   = None
    todays_low        : Optional[str]   = None
    visibility        : Optional[str]   = None
    wind_chill        : Optional[str]   = None
    wind_degree       : Optional[int]   = 0
    wind_dir          : Optional[str]   = None
    wind_speed        : Optional[str]   = None

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
LOADING = f'{util.color_title(glyphs.md_weather_sunny)} Fetching weather...'
LOGFILE = Path.home() / '.polybar-weather-test-result.log'

logging.basicConfig(
    filename=LOGFILE,
    filemode='a',  # 'a' = append, 'w' = overwrite
    format='%(asctime)s [%(levelname)-5s] - %(message)s',
    level=logging.INFO
)

def set_globals(label: str=None, location: str=None):
    global _label
    global _location
    _label = label
    _location = location

def get_statefile():
    global _label
    global _location

    module = os.path.basename(__file__)
    module_no_ext = os.path.splitext(module)[0]

    return Path.home() / f'.polybar-{module_no_ext}-{_label}-state'    

def get_tempfile():
    global _label
    global _location

    module = os.path.basename(__file__)
    module_no_ext = os.path.splitext(module)[0]

    return Path.home() / f'.polybar-{module_no_ext}-{_label}-result.txt'

def get_weather_icon(condition_code, is_day):
    # https://www.weatherapi.com/docs/weather_conditions.json
    if condition_code == 1000: # Sunny
        if is_day == 1:
            return glyphs.md_weather_sunny
        else:
            return glyphs.md_weather_night

    elif condition_code == 1003:
        if is_day == 1: # Partly cloudy
            return glyphs.md_weather_partly_cloudy
        else:
            return glyphs.md_weather_night_partly_cloudy

    elif condition_code == 1006: # Cloudy
        if is_day == 1:
            return glyphs.weather_day_cloudy
        else:
            return glyphs.weather_night_cloudy

    elif condition_code == 1009: # Overcast
        if is_day == 1:
            return glyphs.weather_day_sunny_overcast
        else:
            return glyphs.weather_night_cloudy

    elif condition_code == 1030: # Mist
        if is_day == 1:
            return glyphs.md_weather_hazy
        else:
            return glyphs.md_weather_hazy

    elif condition_code == 1063: # Patchy rain possible
        if is_day == 1:
            return glyphs.md_weather_partly_rainy
        else:
            return glyphs.md_weather_partly_rainy

    elif condition_code == 1066: # Patchy snow possible
        if is_day == 1:
            return glyphs.md_weather_partly_snowy
        else:
            return glyphs.md_weather_partly_snowy

    elif condition_code == 1114: # Blowing snow
        if is_day == 1:
            return glyphs.weather_snow_wind
        else:
            return glyphs.weather_day_snow_wind

    elif condition_code in [1069, 1204, 1249]: # Patchy sleet possible / Light sleet /Light sleet showers
        if is_day == 1:
            return glyphs.weather_day_sleet
        else:
            return glyphs.weather_night_sleet

    elif condition_code in [1207, 1252]: # Moderate or heavy sleet / Moderate or heavy sleet showers
        if is_day == 1:
            return glyphs.weather_day_sleet_storm
        else:
            return glyphs.weather_night_alt_sleet_storm

    elif condition_code in [1210, 1213, 1216, 1219, 1222, 1225] : # Patchy light snow / Light snow / Patchy moderate snow / Moderate snow / Patchy heavy snow / Heavy snow
        if is_day == 1:
            return glyphs.weather_day_snow
        else:
            return glyphs.weather_night_snow

    elif condition_code == 1240: # Light rain shower
        if is_day == 1:
            return glyphs.weather_day_rain
        else:
            return glyphs.weather_night_rain

    elif condition_code == 1243: # Moderate or heavy rain shower
        if is_day == 1:
            return glyphs.weather_day_showers
        else:
            return glyphs.weather_night_showers

    elif condition_code == 1246: # Torrential rain shower
        if is_day == 1:
            return glyphs.weather_day_storm_showers
        else:
            return glyphs.weather_night_storm_showers

    return glyphs.md_weather_sunny

def get_weather_data(api_key, location, use_celsius, label, mode):
    weather_data = None

    url_parts = (
        'https',
        'api.weatherapi.com',
        f'v1/forecast.json?key={api_key}&q={quote(location)}&aqi=no&alerts=no',
        '',
        '',
        '',
    )
    url = urlunparse(url_parts)

    with urllib.request.urlopen(url) as response:
        body = response.read().decode('utf-8')
        if response.status == 200:
            json_data, err = util.parse_json_string(body)
            if err:
                weather_data = WeatherData(
                    success        = False,
                    error          = f'could not retrieve the weather for {location}: {err}',
                    location_full  = location,
                )
            else:
                if use_celsius:
                    distance = 'km'
                    height = 'mm'
                    speed = 'kph'
                    unit = 'C'
                else:
                    distance = 'miles'
                    height = 'in'
                    speed = 'mph'
                    unit = 'F'
                
                unit_lower = unit.lower()

                try:
                    astro_data     = json_data['forecast']['forecastday'][0]['astro']
                    condition_data = json_data['current']['condition']
                    current_data   = json_data['current']
                    forecast_data  = json_data['forecast']['forecastday'][0]['day']
                    location_data  = json_data['location']

                    weather_data = WeatherData(
                        success        = True,
                        icon           = get_weather_icon(current_data['condition']['code'], current_data['is_day']),
                        avg_humidity   = f'{forecast_data.get("avghumidity")}%' if forecast_data.get('avghumidity') is not None else 'Unknown',
                        condition_code = current_data.get('condition').get('code') if 'code' in current_data.get('condition') else 'Unknown',
                        country        = location_data.get('country') if location_data.get('country') is not None else 'Unknown',
                        current_temp   = f'{current_data.get(f"temp_{unit_lower}")}°{unit}' if current_data.get(f'temp_{unit_lower}') is not None else 'Unknown',
                        dewpoint       = f'{current_data.get(f"dewpoint_{unit_lower}")}°{unit}' if current_data.get(f'dewpoint_{unit_lower}') is not None else 'Unknown',
                        feels_like     = f'{current_data.get(f"feelslike_{unit_lower}")}°{unit}' if current_data.get(f'feelslike_{unit_lower}') is not None else 'Unknown',
                        gust           = f'{current_data.get(f"gust_{speed}")} {speed}' if current_data.get(f'gust_{speed}') is not None else 'Unknown',
                        heat_index     = f'{current_data.get(f"heatindex_{unit_lower}")}°{unit}' if current_data.get(f'heatindex_{unit_lower}') is not None else 'Unknown',
                        humidity       = f'{current_data.get("humidity")}%' if current_data.get('humidity') is not None else 'Unknown',
                        location_full  = location,
                        location_short = location_data.get('name') if location_data.get('name') is not None else 'Unknown',
                        moonrise       = astro_data.get('moonrise') if astro_data.get('moonrise') is not None else 'Unknown',
                        moonset        = astro_data.get('moonset') if astro_data.get('moonset') is not None else 'Unknown',
                        sunrise        = astro_data.get('sunrise') if astro_data.get('sunrise') is not None else 'Unknown',
                        sunset         = astro_data.get('sunset') if astro_data.get('sunset') is not None else 'Unknown',
                        precipitation  = f'{forecast_data.get(f"totalprecip_{height}")} {height}' if forecast_data.get(f'totalprecip_{height}') is not None else 'Unknown',
                        region         = location_data.get('region') if location_data.get('region') is not None else 'Unknown',
                        todays_high    = f'{forecast_data.get(f"maxtemp_{unit_lower}")}°{unit}' if forecast_data.get(f'maxtemp_{unit_lower}') is not None else 'Unknown',
                        todays_low     = f'{forecast_data.get(f"mintemp_{unit_lower}")}°{unit}' if forecast_data.get(f'mintemp_{unit_lower}') is not None else 'Unknown',
                        visibility     = f'{current_data.get(f"vis_{distance}")} {distance}' if current_data.get(f'vis_{distance}') is not None else 'Unknown',
                        wind_chill     = f'{current_data.get(f"windchill_{unit_lower}")}°{unit}' if current_data.get(f'windchill_{unit_lower}') is not None else 'Unknown',
                        wind_degree    = current_data.get('wind_degree') if current_data.get('wind_degree') is not None else 'Unknown',
                        wind_dir       = current_data.get('wind_dir') if current_data.get('wind_dir') is not None else 'Unknown',
                        wind_speed     = f'{current_data.get(f"wind_{speed}")} {speed}' if current_data.get(f'wind_{speed}') is not None else 'Unknown',
                    )
                except Exception as e:
                    weather_data = WeatherData(
                        success        = False,
                        error          = f'could not retrieve the weather for {location}: {err}',
                        location_full  = location,
                    )
        else:
            weather_data = WeatherData(
                success        = False,
                error          = f'a non-200 ({response.status}) was received',
                location_full  = location,
            )

    tempfile = get_tempfile()
    if weather_data.success:
        current_temp = weather_data.current_temp
        low_temp     = weather_data.todays_low
        high_temp    = weather_data.todays_high
        icon         = weather_data.icon
        location     = weather_data.location_short
        sunrise      = weather_data.sunrise
        sunset       = weather_data.sunset
        wind_degree  = weather_data.wind_degree
        wind_speed   = weather_data.wind_speed      

        if mode == 0:
            tempfile.write_text(f'{util.color_title(icon)} {location} {current_temp}')
        elif mode == 1:
            tempfile.write_text(f'{util.color_title(icon)} {location} {high_temp}{glyphs.cod_arrow_small_up} {low_temp}{glyphs.cod_arrow_small_down}')
        elif mode == 2:
            tempfile.write_text(f'{util.color_title(glyphs.fa_wind)} {location} {wind_speed} @ {wind_degree}°')
        elif mode == 3:
            tempfile.write_text(f'{util.color_title(glyphs.md_weather_sunny)} {location}  {glyphs.weather_sunrise}  {sunrise} {glyphs.weather_sunset}  {sunset}')
    else:
        tempfile.write_text(f'{util.color_title(glyphs.md_alert)} {util.color_error(weather_data.error)}')

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    Weather fetcher
    """
    pass

@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option('-l', '--location', required=True, default='Los Angeles, CA, US', help='The location to query')
@click.option('--label', required=True, help='A "friendly name" to be used to form the IPC calls')
def show(location, label):
    """
    Display the weather information
    """
    logging.info('[show] entering function')
    set_globals(label=label, location=location)
    tempfile = get_tempfile()

    if tempfile.exists():
        print(tempfile.read_text().strip())
    else:
        print(LOADING)

@cli.command(help='Get weather info from World Weather API', context_settings=CONTEXT_SETTINGS)
@click.option('-a', '--api-key', required=True, help=f'World Weather API key')
@click.option('-l', '--location', required=True, default='Los Angeles, CA, US', help='The location to query')
@click.option('-c', '--use-celsius', default=False, is_flag=True, help='Use Celsius instead of Fahrenheit')
@click.option('--label', required=True, help='A "friendly name" to be used to form the IPC calls')
@click.option('-t', '--toggle', is_flag=True, help='Toggle the output format (not yet implemented)', required=False)
def run(api_key, location, use_celsius, label, toggle):
    mode_count = 4
    util.check_network()
    set_globals(label=label, location=location)

    if toggle:
        mode = state.next_state(statefile=get_statefile(), mode_count=mode_count)
    else:
        mode = state.read_state(statefile=get_statefile())

    subprocess.run(['polybar-msg', 'action', f'#weather-{label}.send.{LOADING}'])
    get_weather_data(api_key, location, use_celsius, label, mode)
    subprocess.run(['polybar-msg', 'action', f'#weather-{label}.hook.0'])

if __name__ == '__main__':
    cli()
