#!/usr/bin/env python3

from pathlib import Path
from polybar import glyphs, util
from urllib.parse import quote, urlunparse
from urllib.request import urlopen, Request
import argparse
import sys
import urllib.request

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

def get_weather_data(api_key, location, use_celsius):
    output = {
        'locations': {},
    }

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
                    output['locations'][location]['todays_high'] = weather_data['forecast']['forecastday'][0]['day']['maxtemp_c']
                    output['locations'][location]['todays_low'] = weather_data['forecast']['forecastday'][0]['day']['mintemp_c']
                    output['locations'][location]['unit'] = 'C'
                else:
                    output['locations'][location]['current_temp'] = weather_data['current']['temp_f']
                    output['locations'][location]['todays_high'] = weather_data['forecast']['forecastday'][0]['day']['maxtemp_f']
                    output['locations'][location]['todays_low'] = weather_data['forecast']['forecastday'][0]['day']['mintemp_f']
                    output['locations'][location]['unit'] = 'F'

    return output

def main():
    parser = argparse.ArgumentParser(description="Get weather info from World Weather API")
    parser.add_argument("-a", "--api-key", help="World Weather API key", required=True)
    parser.add_argument("-l", "--location", help="The location to query", required=True)
    parser.add_argument("-c", "--use-celsius", help="Use Celsius instead of Fahrenheit", required=False, default=False, type=bool)
    args = parser.parse_args()

    locations = args.location if args.location else config['locations']
    weather_data = get_weather_data(args.api_key, args.location, args.use_celsius)

    output = []
    if len(weather_data['locations']) > 0:
        for location, location_data in weather_data['locations'].items():
            current_temp = location_data['current_temp']
            low_temp = location_data['todays_low']
            high_temp = location_data['todays_high']
            unit = location_data['unit']
            icon = location_data['icon']
            output.append(f'{util.color_title(icon)} {location} {current_temp}°{unit} ({high_temp}°{unit}{glyphs.cod_arrow_small_up} {low_temp}°{unit}{glyphs.cod_arrow_small_down})')

    print(' | '.join(output))
    sys.exit(0)

if __name__ == '__main__':
    main()
