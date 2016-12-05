from validation import Validation, LeadingWhitespaceValidation, TrailingWhitespaceValidation
from schema import Schema
from column import Column
import unittest
import pandas as pd
import typing
import re

from validation_error import ValidationError

class BuiltInValidationTest(unittest.TestCase):
    schema = Schema([
        Column('Fail', [
            LeadingWhitespaceValidation(),
            TrailingWhitespaceValidation(),
        ]),
        Column('Succeed')
    ])

    @staticmethod
    def assertMatches(list: typing.Iterable, condition: typing.Callable[[object], bool], number:int):
        """
        Assert that the condition matches elements in the list, n amount of times
        :param list: The list whose elements we are testing
        :param condition: The function to apply to each element to find if it passes
        :param number: The number of matches we expect
        """
        matches = [m for m in list if condition(m)]
        num_matches = len(matches)
        if num_matches == number:
            return True
        else:
            raise AssertionError('Expected {} match[es]. Obtained {} matches'.format(number, num_matches))

    def assertValidationError(self, list: typing.List[ValidationError], row: int, column: str, regex: str, number: int = 1):
        """
        Assert that a ValidationError with the given row, column, and with a message matching the given regex matches n times
        :param list: The list to search in
        :param row: The row number to check
        :param column: The column name to check
        :param regex: The pattern to match the message against
        :param number: The number of matches we expect. Defaults to 1
        """
        def match(error: ValidationError):
            if error.row == row and error.column == column and re.search(regex, error.message):
                return True
            else:
                return False

        self.assertMatches(list, match, number)

    def assertNoValidationError(self, list: typing.List[ValidationError], row: int, column: str, regex: str):
        """
        Assert that a ValidationError with the given row, column, and with a message matching the given regex does not exist in the list
        :param list: The list to search in
        :param row: The row number to check
        :param column: The column name to check
        :param regex: The pattern to match the message against
        """
        self.assertValidationError(list, row, column, regex, 0)

    def test_whitespace(self):
        entries = [
            '   leading spaces',
            '   leading tabs',
            '''
            leading newline''',
            'nowhitespace',
            'trailing space   ',
            'trailing tabs  ',
            '''trailing newline
            '''
        ]

        data = pd.DataFrame({
            'Fail': entries,
            'Succeed': entries
        })

        errors = self.schema.validate(data)

        # Assert that validations failed where they should have
        self.assertValidationError(errors, 0, 'Fail', 'leading')
        self.assertValidationError(errors, 1, 'Fail', 'leading')
        self.assertValidationError(errors, 2, 'Fail', 'leading')
        self.assertNoValidationError(errors, 3, 'Fail', '')
        self.assertValidationError(errors, 4, 'Fail', 'trailing')
        self.assertValidationError(errors, 5, 'Fail', 'trailing')
        self.assertValidationError(errors, 6, 'Fail', 'trailing')

        # Everything in the succeed column should have passed
        for i in range(7):
            self.assertNoValidationError(errors, i, 'Succeed', '')
