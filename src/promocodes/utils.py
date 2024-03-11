import re
import requests

from datetime import datetime
from django.conf import settings
from typing import TypedDict, List

OPEN_WEATHER_KEY = settings.OPEN_WEATHER_KEY


class IntegerRestriction(TypedDict):
    """
    Note: added underscore to the keys to avoid conflict with the built-in keywords.
    """

    _eq: int
    _lt: int
    _gt: int


class DateRestriction(TypedDict):
    """
    Note: added underscore to the keys to avoid conflict with the built-in keywords.
    """

    _after: str
    _before: str


class WeatherRestriction(TypedDict):
    """
    Note: added underscore to the keys to avoid conflict with the built-in keywords.
    """

    _is: str
    _temp: "IntegerRestriction"


class Restriction(TypedDict):
    """
    Note: added underscore to the keys to avoid conflict with the built-in keywords.

    TODO : this is not an accurate representation of the restrictions JSON object
    since only one of the keys can be present at a time.
    """

    _date: "DateRestriction"
    _age: "IntegerRestriction"
    _weather: "WeatherRestriction"
    _or: List["Restriction"]
    _and: List["Restriction"]


Restrictions = List[Restriction]


def is_valid_date(date_str: str) -> bool:
    """
    Check if the given date string matches the format "YYYY-MM-DD" using regex pattern matching.
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    # Use re.match to check if the pattern matches the entire string
    match = re.match(pattern, date_str)
    return bool(match)


def validate_restrictions(restrictions: Restrictions):
    """
    Validate the restrictions data structure.
    """
    if not isinstance(restrictions, list):
        return 'Restrictions must be an array of objects.'

    # Check that the restrictions array is not empty
    if len(restrictions) == 0:
        return 'Restrictions array cannot be empty.'

    # Iterate through the restrictions array and validate each object
    # This function is calling itself recursively to validate nested objects
    for restriction in restrictions:
        if not isinstance(restriction, dict):
            return 'Restrictions must be an array of objects.'

        if "date" in restriction:
            date = restriction["date"]
            if not isinstance(date, dict):
                return "Date must be a JSON object."
            elif "after" not in date and "before" not in date:
                return "Date must contain either an after or before key."
            elif "after" in date and not isinstance(date["after"], str):
                return "After must be a string."
            elif "before" in date and not isinstance(date["before"], str):
                return "Before must be a string."
            elif "after" in date and not is_valid_date(date["after"]):
                return "After must be in the format of YYYY-MM-DD."
            elif "before" in date and not is_valid_date(date["before"]):
                return "Before must be in the format of YYYY-MM-DD."

        elif "or" in restriction:
            or_ = restriction["or"]
            if not isinstance(or_, list):
                return "Or must be an array."
            if not or_:
                return "Or array cannot be empty."
            return validate_restrictions(or_)

        elif "and" in restriction:
            and_ = restriction["and"]
            if not isinstance(and_, list):
                return "And must be an array."
            if not and_:
                return "And array cannot be empty."
            return validate_restrictions(and_)

        elif "age" in restriction:
            age = restriction["age"]
            if not isinstance(age, dict):
                return "Age must be a JSON object."
            if "eq" in age and not isinstance(age["eq"], int):
                return "eq must be an integer."
            if "lt" in age and not isinstance(age["lt"], int):
                return "lt must be an integer."
            if "gt" in age and not isinstance(age["gt"], int):
                return "gt must be an integer."

        elif "weather" in restriction:
            weather = restriction["weather"]
            if not isinstance(weather, dict):
                return "Weather must be a JSON object."
            if "is" not in weather:
                return "Weather must contain an is key."
            if "temp" in weather:
                temp = weather["temp"]
                if not isinstance(temp, dict):
                    return "Temp must be a JSON object."
                if "gt" in temp and not isinstance(temp["gt"], int):
                    return "Gt must be an integer."
                if "lt" in temp and not isinstance(temp["lt"], int):
                    return "Lt must be an integer."
        else:
            return "Restriction must contain a date, or, and, age, or weather key."

        return None


def validate_advantage(advantage):
    """
    Validate the advantage data structure.
    """
    if not isinstance(advantage, dict):
        return 'Advantage must be a JSON object.'
    if 'percent' not in advantage and 'value' not in advantage:
        return 'Advantage must contain either a percent or value key.'
    if 'percent' in advantage and 'value' in advantage:
        return 'Advantage cannot contain both a percent and value key.'
    if 'percent' in advantage and not isinstance(advantage['percent'], int):
        return 'Percent must be an integer.'
    if 'value' in advantage and not isinstance(advantage['value'], int):
        return 'Value must be an integer.'
    return None


def check_condition(condition, val):
    """
    Evaluates a single condition against the provided arguments.
    """
    for key, value in condition.items():
        if key in ['gt', 'lt', 'eq']:
            if key == 'gt' and not (val > value):
                return False
            elif key == 'lt' and not (val < value):
                return False
            elif key == 'eq' and not (val == value):
                return False
        elif key == 'is':
            if val != value:
                return False
    return True


def evaluate_restrictions(restrictions, arguments):
    """
    Recursively evaluates restrictions against provided arguments.
    TODO : Refactor, improve readability
    """
    age = arguments.get('age', None)
    town = arguments.get('town', None)

    failure_reasons = []

    for restriction in restrictions:
        if 'date' in restriction:
            now = datetime.now()
            date_condition = restriction['date']
            # Compare the current date with the condition
            if 'after' in date_condition and now < datetime.strptime(date_condition['after'], '%Y-%m-%d'):
                failure_reasons.append(f"Date must be after {date_condition['after']}.")
            if 'before' in date_condition and now > datetime.strptime(date_condition['before'], '%Y-%m-%d'):
                failure_reasons.append(f"Date must be before {date_condition['before']}.")

        elif 'age' in restriction:
            if not age:
                failure_reasons.append("Age condition not met.")
            else:
                age_condition = restriction['age']
                if not check_condition(age_condition, age):
                    failure_reasons.append("Age condition not met.")

        elif 'weather' in restriction:
            if not town:
                failure_reasons.append("Weather condition not met.")
            else:
                expected_weather = restriction['weather'].get('is', None)
                expected_temp = restriction['weather'].get('temp', None)

                # Call the weather API to get the current weather : https://openweathermap.org/current
                # requests.get('http://api.openweathermap.org/data/2.5/weather?q={town}&appid={API_KEY}')
                location_endpoint = f'http://api.openweathermap.org/geo/1.0/direct?q={town}&limit=1&appid={OPEN_WEATHER_KEY}'
                response = requests.get(location_endpoint)
                if response.status_code != 200:
                    failure_reasons.append(f"Failed to retrieve weather for location {town}.")

                location = response.json()[0]
                lat, lon = location['lat'], location['lon']

                weather_endpoint = f'http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={OPEN_WEATHER_KEY}&exclude=minutely,hourly,daily,alerts&units=metric'
                response = requests.get(weather_endpoint)
                if response.status_code != 200:
                    failure_reasons.append(f"Failed to retrieve weather for location {town}.")

                temperature = response.json()['current']['temp']
                weather = response.json()['current']['weather'][0]['main'].lower()

                if expected_weather and weather != expected_weather:
                    failure_reasons.append(f"Weather must be {expected_weather} - current weather: {weather}.")
                if expected_temp and not check_condition(expected_temp, temperature):
                    failure_reasons.append("Weather temperature condition not met.")

        elif 'or' in restriction:
            results = [evaluate_restrictions([sub_condition], arguments) for sub_condition in restriction['or']]
            failures = [res for res in results if res != []]

            # Success if any of the sub-conditions are met, i,e, at least one of evaluation returned no failures
            success = any([True for res in results if res == []])
            if success:
                return []

            # flatten the list of lists
            failures = [item for sublist in failures for item in sublist]
            failure_reasons.extend(failures)

        elif 'and' in restriction:
            results = [evaluate_restrictions([sub_condition], arguments) for sub_condition in restriction['and']]
            failures = [res for res in results if res != []]

            # Success if all of the sub-conditions are met, i,e, all evaluations return empty lists
            success = len(failures) == 0
            if success:
                return []

            # flatten the list of lists
            failures = [item for sublist in failures for item in sublist]
            failure_reasons.extend(failures)

    # Remove duplicates
    return list(set(failure_reasons))


def validate_arguments(arguments):
    # arguments is an object which may contain the following keys:
    # - age : integer representing the age of the user.
    # - weather : a string representing the weather conditions.
    if 'age' in arguments and not isinstance(arguments['age'], int):
        return "Invalid argument - age must be an integer."
    if 'town' in arguments and not isinstance(arguments['town'], str):
        return "Invalid argument - town must be a string."
    return None


#  TODO : This may belong in the models file
def validate_promo_code(restrictions, arguments):
    """
    restrictions is an array of restriction objects
    arguments is an object which may contain the following keys:
    - age : integer representing the age of the user.
    - town : a string representing the town the user is in.
    """
    if not restrictions:
        return []

    arguments_err = validate_arguments(arguments)
    if arguments_err:
        raise ValueError(f'Failed to validate arguments: {arguments_err}')

    failure_reasons = evaluate_restrictions(restrictions, arguments)
    return failure_reasons
