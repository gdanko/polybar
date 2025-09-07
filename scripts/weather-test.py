#!/usr/bin/env python3

from collections import namedtuple
from polybar import glyphs, state, util
from typing import Any, Dict, List, Optional, NamedTuple
import json
import os

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

def main():
    filename = os.path.join(
        util.get_script_directory(),
        'weather.txt'
    )

    class Dummy(NamedTuple):
        location : namedtuple
        current  : namedtuple
        forecast : []

    with open(filename, 'r') as f:
        json_data = json.load(f)

    #################################
    #
    # Location
    #
    #################################

    # Dynamically create a namedtuple class
    location = json_data['location']
    Location = namedtuple('Location', location.keys())

    # Instantiate it with the dictionary values
    location_instance = Location(**location)

    #################################
    #
    # Current Condition
    #
    #################################

    # Dynamically create a namedtuple class
    current_condition_item = json_data['current']['condition']
    CurrentCondition = namedtuple('CurrentCondition', current_condition_item.keys())

    # Instantiate it with the dictionary values
    current_condition_instance = CurrentCondition(**current_condition_item)

    #################################
    #
    # Current Condition
    #
    #################################

    # Dynamically create a namedtuple class
    current_item = json_data['current']
    Current = namedtuple('Current', current_item.keys())

    # Instantiate it with the dictionary values
    current_instance = Current(**current_item)

    # Remove condition
    current_instance = remove_field(current_instance, 'condition')

    # Add the condition namedtuple
    current_instance = add_field(current_instance, 'condition', current_condition_instance)

    for forecast_item in json_data['forecast']['forecastday']:
        # Dynamically create a namedtuple class
        ForecastDay = namedtuple('ForecastDay', forecast_item.keys())

        # Instantiate it with the dictionary values
        forecast_day_instance = ForecastDay(**forecast_item)

        # Remove some fields
        forecast_day_instance = remove_field(forecast_day_instance, 'day')
        forecast_day_instance = remove_field(forecast_day_instance, 'astro')
        forecast_day_instance = remove_field(forecast_day_instance, 'hour')

        #################################
        #
        # Day
        #
        #################################

        # Dynamically create a namedtuple class
        day_item = forecast_item['day']
        Day = namedtuple('Day', forecast_item['day'].keys())

        # Instantiate it with the dictionary values
        day_instance = Day(**day_item)

        # Remove some fields
        day_instance = remove_field(day_instance, 'condition')

        # Dynamically create a namedtuple class
        day_condition_item = forecast_item['day']['condition']
        DayCondition = namedtuple('DayCondition', forecast_item['day']['condition'].keys())

        # Instantiate it with the dictionary values
        day_condition_instance = DayCondition(**day_condition_item)

        #################################
        #
        # Astro
        #
        #################################

        # Dynamically create a namedtuple class
        astro_item = forecast_item['astro']
        Astro = namedtuple('Astro', forecast_item['astro'].keys())

        # Instantiate it with the dictionary values
        astro_instance = Astro(**astro_item)

        #################################
        #
        # Hour
        #
        #################################

        #################################
        #
        # Put it all together
        #
        #################################

        day_instance = add_field(day_instance, 'condition', day_condition_instance)
        # forecast_day_instance = add_field(forecast_day_instance, 'location', location_instance)
        # forecast_day_instance = add_field(forecast_day_instance, 'current', current_instance)
        forecast_day_instance = add_field(forecast_day_instance, 'day', day_instance)
        forecast_day_instance = add_field(forecast_day_instance, 'astro', astro_instance)

        # util.pprint(forecast_day_instance)
        # print()
        # print(location_instance.localtime)
        # print(current_instance.is_day)
        # print(current_instance.condition.text)
        # print(forecast_day_instance.date)
        # print(forecast_day_instance.day.maxtemp_f)
        # print(forecast_day_instance.day.uv)
        # print(forecast_day_instance.day.condition.icon)
        # print(forecast_day_instance.astro.sunrise)
        # print(forecast_day_instance.astro.is_moon_up)

        class Dummy(NamedTuple):
            Location : namedtuple
            Current  : namedtuple
        
        test = Dummy(
            Location = location_instance,
            Current  = current_instance,
        )

        util.pprint(test)
        print(test.Location.localtime)
        print(test.Current.is_day)
        print(test.Current.condition.text)


if __name__ == '__main__':
    main()
