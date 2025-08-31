#!/usr/bin/env python3

from pathlib import Path
from polybar import util
from urllib.parse import quote, urlunparse
from urllib.request import urlopen, Request
import json
import os
import sys
import urllib.request

def sanitize_config(config):
    if not 'locations' in config:
        config['locations'] = ['Los Angeles, CA, US']
    else:
        if len(config['locations']) == 0:
            config['locations'] = ['Los Angeles, CA, US']

    if not 'use_celsius' in config:
        config['use_celsius'] = True
    
    return config

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

def get_weather_data(config):
    output = {
        'locations': {},
    }

    api_key = config['api_key']
    locations = config['locations']
    use_celsius = config['use_celsius']

    for location in locations:
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
                weather_data, err = util.parse_json_string(body)

                if not location in output['locations']:
                    output['locations'][location] = {}


                if err:
                    output['locations'][location]['error'] = f'could not retrieve the weather for {location}: {err}'
                else:
                    output['locations'][location]['location'] = weather_data['location']['name']
                    output['locations'][location]['condition_code'] = weather_data['current']['condition']['code']
                    output['locations'][location]['icon'] = get_weather_icon(
                        weather_data['current']['condition']['code'],
                        weather_data['current']['is_day'],
                    )

                    if use_celsius:
                        output['locations'][location]['current_temp'] = weather_data['current']['temp_c']
                        output['locations'][location]['unit'] = 'C'
                    else:
                        output['locations'][location]['current_temp'] = weather_data['current']['temp_f']
                        output['locations'][location]['unit'] = 'F'

    return output

def main():
    config_file = util.get_config_file_path('weather.json')
    config, err = util.parse_config_file(filename=config_file, required_keys=['api_key'])
    if err != '':
        print(f'Weather: {err}')
        sys.exit(1)

    config = sanitize_config(config)
    weather_data = get_weather_data(config)

    output = []
    if len(weather_data['locations']) > 0:
        for location, location_data in weather_data['locations'].items():
            current_temp = location_data['current_temp']
            unit = location_data['unit']
            icon = location_data['icon']
            output.append(f'{util.colorize(icon)} {location} {current_temp}°{unit}')

    print(' | '.join(output))
    sys.exit(0)

if __name__ == '__main__':
    main()
