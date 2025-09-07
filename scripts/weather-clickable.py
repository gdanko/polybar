#!/usr/bin/env python3

from collections import namedtuple
from pathlib import Path
from polybar import glyphs, state, util
from typing import Any, Dict, List, Optional, NamedTuple
from urllib.parse import quote, urlunparse
from urllib.request import urlopen, Request
import argparse
import sys
import urllib.request

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

def get_statefile_name() -> str:
    statefile = os.path.basename(__file__)
    statefile_no_ext = os.path.splitext(statefile)[0]
    return os.path.join(
        util.get_home_directory(),
        f'.polybar-{statefile_no_ext}-state'
    )

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

def remove_field(nt, field):
    fields = [f for f in nt._fields if f != field]
    NT = namedtuple(nt.__class__.__name__, fields)
    values = [getattr(nt, f) for f in fields]
    return NT(*values)

def add_field(nt_instance, field_name, default=None):
    # Original fields
    old_fields = nt_instance._fields
    # New NamedTuple class
    NT = namedtuple(nt_instance.__class__.__name__, old_fields + (field_name,))
    # Original values + default for new field
    values = list(nt_instance)
    values.append(default)
    return NT(*values)

def get_weather_data(api_key, location, use_celsius):
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
            # util.pprint(json_data)

            location = json_data['location']
            location_keys = namedtuple('Location', location.keys())
            location_tuple = location_keys(**location)
            util.pprint(location_tuple)
            print()

            current_condition = json_data['current']['condition']
            current_condition_keys = namedtuple('CurrentCondition', current_condition.keys())
            current_condition_tuple = current_condition_keys(**current_condition)
            util.pprint(current_condition_tuple)
            print()

            current = json_data['current']
            current_keys = namedtuple('Current', current.keys())
            current_tuple = current_keys(**current)
            current_tuple = remove_field(current_tuple, 'condition')
            current_tuple = add_field(current_tuple, 'condition', current_condition_tuple)
            util.pprint(current_tuple)

            print(current_tuple.condition.code)
            print()


           

            exit()

            if err:
                weather_data = WeatherData(
                    success        = False,
                    error          = f'could not retrieve the weather for {location}: {err}',
                    location_full  = location,
                )
            else:
            
                unit = 'C' if use_celsius else 'F'
                unit_lower = unit.lower()

                if use_celsius:
                    distance = 'km'
                    height = 'mm'
                    speed = 'kph'
                    unit = 'C'
                else:
                    distance = 'miles'
                    height = 'mm'
                    speed = 'mph'
                    unit = 'F'
                
                unit_lower = unit.lower()

                avg_humidity  = json_data['forecast']['forecastday'][0]['day']['avghumidity']
                current_temp  = json_data['current'][f'temp_{unit_lower}']
                dewpoint      = json_data['current'][f'dewpoint_{unit_lower}']
                feels_like    = json_data['current'][f'feelslike_{unit_lower}']
                gust          = json_data['current'][f'gust_{speed}']
                heat_index    = json_data['current'][f'heatindex_{unit_lower}']
                humidity      = json_data['current']['humidity']
                precipitation = json_data['forecast']['forecastday'][0]['day'][f'totalprecip_{height}']
                todays_high   = json_data['forecast']['forecastday'][0]['day'][f'maxtemp_{unit_lower}']
                todays_low    = json_data['forecast']['forecastday'][0]['day'][f'mintemp_{unit_lower}']
                visibility    = json_data['current'][f'vis_{distance}']
                wind_chill    = json_data['current'][f'windchill_{unit_lower}']
                wind_dir      = json_data['current']['wind_dir']
                wind_speed    = json_data['current'][f'wind_{speed}']

                weather_data = WeatherData(
                    success        = True,
                    icon           = get_weather_icon(json_data['current']['condition']['code'], json_data['current']['is_day']),

                    avg_humidity   = f'{avg_humidity}%',
                    condition_code = json_data['current']['condition']['code'],
                    country        = json_data['location']['country'],
                    current_temp   = f'{current_temp}°{unit}',
                    dewpoint       = f'{dewpoint}°{unit}',
                    feels_like     = f'{feels_like}°{unit}',
                    gust           = f'{gust} {speed}',
                    heat_index     = f'{heat_index}°{unit}',
                    humidity       = f'{humidity}%',
                    location_full  = location,
                    location_short = json_data['location']['name'],
                    moonrise       = json_data['forecast']['forecastday'][0]['astro']['moonrise'],
                    moonset        = json_data['forecast']['forecastday'][0]['astro']['moonset'],
                    precipitation  = f'{precipitation} {height}',
                    region         = json_data['location']['region'],
                    sunrise        = json_data['forecast']['forecastday'][0]['astro']['sunrise'],
                    sunset         = json_data['forecast']['forecastday'][0]['astro']['sunset'],
                    todays_high    = f'{todays_high}°{unit}',
                    todays_low     = f'{todays_low}°{unit}',
                    visibility     = f'{visibility} {distance}',
                    wind_chill     = f'{wind_chill}°{unit}',
                    wind_degree    = json_data['current']['wind_degree'],
                    wind_dir       = wind_dir,
                    wind_speed     = f'{wind_speed} {speed}',
                )
        else:
            weather_data = WeatherData(
                success        = False,
                error          = f'non-200 ({response.status}) code returned',
                location_full  = location,
            )

    return weather_data

def main():
    parser = argparse.ArgumentParser(description='Get weather info from World Weather API')
    parser.add_argument('-a', '--api-key', help='World Weather API key', required=True)
    parser.add_argument('-l', '--location', help='The location to query', required=True)
    parser.add_argument('-c', '--use-celsius', action='store_true', help='Use Celsius instead of Fahrenheit', required=False, default=False)
    parser.add_argument('-t', '--toggle', action='store_true', help='Toggle the output format', required=False)
    parser.add_argument('-i', '--interval', help='The update interval (in seconds)', required=False, default=2, type=int)
    parser.add_argument('-b', '--background', action='store_true', help='Run this script in the background', required=False)
    args = parser.parse_args()

    if not util.network_is_reachable():
        print(f'{util.color_title(glyphs.md_network_off_outline)} {util.color_error("the network is unreachable")}')
        sys.exit(1)

    weather_data = get_weather_data(args.api_key, args.location, args.use_celsius)
    util.pprint(weather_data)
    exit()

    if weather_data.success:
        print(f'{util.color_title(weather_data.icon)} {weather_data.location_short} {weather_data.current_temp}°{weather_data.unit} ({weather_data.todays_high}°{weather_data.unit}{glyphs.cod_arrow_small_up} {weather_data.todays_low}°{weather_data.unit}{glyphs.cod_arrow_small_down})')
        sys.exit(0)
    else:
        print(f'{util.color_title(glyphs.md_alert)} {util.color_error(weather_data.error)}')
        sys.exit(1)

if __name__ == '__main__':
    main()
