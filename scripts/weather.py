#!/usr/bin/env python3

from pathlib import Path
from polybar import util
from urllib.parse import quote, urlunparse
from urllib.request import urlopen, Request
import json
import os
import sys
import urllib.request

def get_weather_icon(condition_code, is_day):
    if condition_code == 1000:
        if is_day == 1:
            return '\uf185' # md_weather_sunny
        else:
            return util.surrogatepass('\udb81\udd94') # md_weather_night

    elif condition_code == 1003:
        if is_day == 1:
            return util.surrogatepass('\udb81\udd95') # md_weather_partly_cloudy
        else:
            return util.surrogatepass('\udb83\udf31') # md_weather_night_partly_cloudy

    elif condition_code == 1006:
        if is_day == 1:
            return util.surrogatepass('\udb81\udd90') # md_weather_cloudy
        else:
            return util.surrogatepass('\udb83\udf31') # md_weather_cloudy

    elif condition_code == 1009: # Overcast
        if is_day == 1:
            return util.surrogatepass('\ue30c') # weather_day_sunny_overcast
        else:
            return util.surrogatepass('\ue30c') # weather_day_sunny_overcast

    elif condition_code == 1030: # Mist
        if is_day == 1:
            return util.surrogatepass('\udb83\udf30') # md_weather_hazy
        else:
            return util.surrogatepass('\udb83\udf30') # md_weather_hazy

    elif condition_code == 1063: # Patchy rain possible
        if is_day == 1:
            return util.surrogatepass('\udb83\udf33') # md_weather_partly_rainy
        else:
            return util.surrogatepass('\udb83\udf33') # md_weather_partly_rainy

    elif condition_code == 1066: # Patchy snow possible
        if is_day == 1:
            return util.surrogatepass('\udb83\udf34') # md_weather_partly_snowy
        else:
            return util.surrogatepass('\udb83\udf34') # md_weather_partly_snowy

    return '\uf185' # md_weather_sunny

def get_weather(api_key, locations, days, use_celsius):
    start_colorize = '%{F#F0C674}'
    end_colorize = '%{F-}'
    start_nerdfont = '%{T3}'
    end_nerdfont = '%{T-}'

    url_parts = (
        'https',
        'api.weatherapi.com',
        f'v1/forecast.json?key={api_key}&q={quote(locations[0])}&days={days}&aqi=yes&alerts=yes',
        '',
        '',
        '',
    )
    url = urlunparse(url_parts)

    with urllib.request.urlopen(url) as response:
        body = response.read().decode('utf-8')
        if response.status == 200:
            try:
                weather_data = json.loads(body)
            except:
                return "Weather data unavailable"
            
            condition_code = weather_data['current']['condition']['code']
            is_day = weather_data['current']['is_day']
            icon = get_weather_icon(condition_code, is_day)
            location = weather_data['location']['name']

            if use_celsius:
                current_temp = weather_data['current']['temp_c']
                unit = 'C'
            else:
                current_temp = weather_data['current']['temp_f']
                unit = 'F'
            
            weather = f'{start_colorize}{start_nerdfont}{icon}{end_nerdfont}{end_colorize} {location} {current_temp}°{unit}'
            return weather

        else:
            return "Weather data unavailable"

def main():
    start_colorize = '%{F#F0C674}'
    end_colorize = '%{F-}'
    start_nerdfont = '%{T3}'
    end_nerdfont = '%{T-}'

    config_file = util.get_config_file_path('weather.json')
    config, err = util.parse_config_file(filename=config_file, required_keys=['api_key'])
    if err != '':
        print(f'Weather: {err}')
        sys.exit(1)

    # Set defaults if the config is missing values
    if not 'locations' in config:
        config['locations'] = ['Los Angeles, CA, US']
    else:
        if len(config['locations']) == 0:
            config['locations'] = ['Los Angeles, CA, US']

    if not 'days' in config:
        config['days'] = 2

    if not 'use_celsius' in config:
        config['use_celsius'] = True

    weather_string = get_weather(config['api_key'], config['locations'], config['days'], config['use_celsius'])
    print(weather_string)
    sys.exit(0)

if __name__ == '__main__':
    main()
