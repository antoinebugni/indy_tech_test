import unittest

from datetime import datetime, timedelta
from unittest.mock import patch

from .utils import (
    check_condition,
    evaluate_restrictions,
    is_valid_date,
    validate_advantage,
    validate_arguments,
    validate_restrictions,
)

# TODO : Refactor - create a base class to make the tests DRY
# TODO : Switch to pytest + parameterized tests


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class TestUtils(unittest.TestCase):
    def test_validate_advantage(self):
        test_cases = [
            ("", "Advantage must be a JSON object."),
            ({}, "Advantage must contain either a percent or value key."),
            ({"value": "10"}, "Value must be an integer."),
            ({"percent": "10"}, "Percent must be an integer."),
            ({"value": 10, "percent": 10}, "Advantage cannot contain both a percent and value key."),
            ({"value": 10}, None),
            ({"percent": 10}, None),
        ]
        for idx, (input, expected) in enumerate(test_cases):
            actual = validate_advantage(input)
            self.assertEqual(actual, expected, f"Case {idx}: Expected '{expected}', got '{actual}' with input {input}")

    def test_is_valid_date(self):
        test_cases = [
            ("2024-01-01", True),
            ('2024-01', False),
        ]
        for idx, (input, expected) in enumerate(test_cases):
            actual = is_valid_date(input)
            self.assertEqual(actual, expected, f"Case {idx}: Expected '{expected}', got '{actual}' with input {input}")

    def test_check_condition(self):
        test_cases = [
            ({'gt': 1}, 1, False),
            ({'gt': 1}, 2, True),
            ({'gt': 3, 'lt': 5}, 4, True),
            ({'gt': 3, 'lt': 5}, 6, False),
            ({'gt': 3, 'lt': 5}, 3, False),
            ({'gt': 3, 'lt': 5}, 5, False),
            ({'eq': 4}, 4, True),
            ({'is': '2024-01-01'}, '2024-01-01', True),
            ({'is': '2024-01-01'}, '2024-01-02', False),
        ]
        for idx, (input_1, input_2, expected) in enumerate(test_cases):
            actual = check_condition(input_1, input_2)
            self.assertEqual(actual, expected, f"Case {idx}: Expected '{expected}', got '{actual}' with : {input_1} , {input_2}")

    def test_validate_arguments(self):
        test_cases = [
            ({"age": "14"}, "Invalid argument - age must be an integer."),
            ({"town": {"name": "Paris"}}, "Invalid argument - town must be a string."),
            ({"age": 14, "town": "Paris"}, None),
            ({"town": "Paris"}, None),
            ({"age": 14, "town": "Paris", "date": "2024-01-01"}, None),
        ]
        for idx, (input_1, expected) in enumerate(test_cases):
            actual = validate_arguments(input_1)
            self.assertEqual(actual, expected, f"Case {idx}: Expected '{expected}', got '{actual}' with : {input_1}")

    def test_validate_restrictions(self):
        test_cases = [
            ({"age": '20'}, 'Restrictions must be an array of objects.'),
            (["age"], "Restrictions must be an array of objects."),
            ([{"age": "20"}], "Age must be a JSON object."),
            ([{"age": {"gt": 20}}], None),
            #  TODO : Add more test cases... test coverage is not complete whatsoever.
        ]
        for idx, (input, expected) in enumerate(test_cases):
            actual = validate_restrictions(input)
            self.assertEqual(actual, expected, f"Case {idx}: Expected '{expected}', got '{actual}' with : {input}")

    def test_evaluate_restrictions(self):
        test_cases = [
            ([{"age": {"gt": 20}}], {"age": 21}, []),
            ([{"age": {"gt": 20}}], {"age": 20}, ["Age condition not met."]),
            ([{'and': [{"age": {"gt": 20}}, {"age": {"lt": 30}}]}], {"age": 25}, []),
            ([{'and': [{"age": {"gt": 20}}, {"age": {"lt": 30}}]}], {"age": 31}, ["Age condition not met."]),
            ([{'or': [{"age": {"gt": 20}}, {"age": {"lt": 30}}]}], {"age": 25}, []),
            ([{'or': [{"age": {"gt": 40}}, {"age": {"lt": 20}}]}], {"age": 15}, []),
            ([{'or': [{"age": {"gt": 40}}, {"age": {"lt": 20}}]}], {"age": 30}, ["Age condition not met."]),
            # TODO : Add more test cases... test coverage is not complete whatsoever.
        ]
        for idx, (input_1, input_2, expected) in enumerate(test_cases):
            actual = evaluate_restrictions(input_1, input_2)
            self.assertEqual(actual, expected, f"Case {idx}: Expected '{expected}', got '{actual}' with : {input_1} , {input_2}")

    # Mock the request.get method to test the validate_promo_code function
    @patch("requests.get")
    def test_evaluate_restrictions_with_api(self, mock_get):
        # TODO : Refactor this code - make it DRY

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        restriction_test_case = [
            {"date": {"after": today, "before": tomorrow}},
            {
                "or": [
                    {"age": {"eq": 40}},
                    {"and": [{"age": {"lt": 30, "gt": 15}}, {"weather": {"is": "clear", "temp": {"gt": 15}}}]},
                ]
            },
        ]

        # Mock the response from the weather api - valid weather
        mock_get.side_effect = [
            # Mock response from weather api to get lat + lon
            MockResponse([{"lat": 0, "lon": 0}], 200),
            # Mock response from weather api to get weather
            MockResponse({"current": {"weather": [{"main": "Clear"}], "temp": 20}}, 200),
        ]

        # Fails if town is not provided
        args = {"age": 20}
        actual = evaluate_restrictions(restriction_test_case, args)
        expected = ['Weather condition not met.', 'Age condition not met.']
        for expected_item in expected:
            self.assertIn(
                expected_item,
                actual,
                f"Expected {expected}, got '{actual}' with args: {args}",
            )

        # Success if town is provided
        args = {"age": 20, "town": "Lyon"}
        actual = evaluate_restrictions(restriction_test_case, args)
        expected = []
        self.assertEqual(
            expected,
            actual,
            f"Expected {expected}, got '{actual}' with args: {args}",
        )

        # Fails if age is incorrect
        args = {"age": 45}
        actual = evaluate_restrictions(restriction_test_case, args)
        expected = ['Weather condition not met.', 'Age condition not met.']
        for expected_item in expected:
            self.assertIn(
                expected_item,
                actual,
                f"Expected {expected}, got '{actual}' with args: {args}",
            )

        # Mock the response from the weather api - invalid weather
        mock_get.side_effect = [
            # Mock response from weather api to get lat + lon
            MockResponse([{"lat": 0, "lon": 0}], 200),
            # Mock response from weather api to get weather
            MockResponse({"current": {"weather": [{"main": "Clouds"}], "temp": 20}}, 200),
        ]

        # Fails because of the weather
        args = {"age": 25, "town": "Paris"}
        actual = evaluate_restrictions(restriction_test_case, args)
        expected = ['Age condition not met.', 'Weather must be clear - current weather: clouds.']
        for expected_item in expected:
            self.assertIn(
                expected_item,
                actual,
                f"Expected {expected}, got '{actual}' with args: {args}",
            )
