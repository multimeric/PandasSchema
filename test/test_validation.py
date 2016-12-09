import json

from validation import LeadingWhitespaceValidation, TrailingWhitespaceValidation, CanCallValidation, \
    DateFormatValidation, InListValidation, MatchesRegexValidation, CanConvertValidation, Validation
import unittest
import pandas as pd
import typing
import re

from validation_error import ValidationError


class ValidationTestBase(unittest.TestCase):
    def seriesEquality(self, s1: pd.Series, s2: pd.Series, msg: str = None):
        if not s1.equals(s2):
            raise self.failureException(msg)

    def validate_and_compare(self, series: list, expected_result: bool, msg: str = None):

        # Check that self.validator is correct
        if not self.validator or not isinstance(self.validator, Validation):
            raise ValueError('The class must have the validator field set to an instance of a Validation subclass')

        # Ensure we're comparing series correctly
        self.addTypeEqualityFunc(pd.Series, self.seriesEquality)

        # Convert the input list to a series and validate it
        results = self.validator.validate(pd.Series(series))

        # Now find any items where their validation does not correspond to the expected_result
        for item, result in zip(series, results):
            with self.subTest(value=item):
                self.assertEqual(result, expected_result, msg)

    @staticmethod
    def assertMatches(list: typing.Iterable, condition: typing.Callable[[object], bool], number: int):
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

    def assertValidationError(self, list: typing.List[ValidationError], row: int, column: str, regex: str = '',
                              number: int = 1):
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

    def assertNoValidationError(self, list: typing.List[ValidationError], row: int, column: str, regex: str = ''):
        """
        Assert that a ValidationError with the given row, column, and with a message matching the given regex does not exist in the list
        :param list: The list to search in
        :param row: The row number to check
        :param column: The column name to check
        :param regex: The pattern to match the message against
        """
        self.assertValidationError(list, row, column, regex, 0)


class LeadingWhitespace(ValidationTestBase):
    """
    Tests the LeadingWhitespaceValidation
    """

    def setUp(self):
        self.validator = LeadingWhitespaceValidation()

    def test_validate_trailing_whitespace(self):
        self.validate_and_compare(
            [
                'trailing space   ',
                'trailing tabs  ',
                '''trailing newline
                '''
            ],
            True,
            'is incorrectly failing on trailing whitespace'
        )

    def test_validate_leading_whitespace(self):
        self.validate_and_compare(
            [
                '   leading spaces',
                '   leading tabs',
                '''
                leading newline''',
            ],
            False,
            'does not detect leading whitespace'
        )

    def test_validate_middle_whitespace(self):
        self.validate_and_compare(
            [
                'middle spaces',
                'middle tabs',
                '''middle
                newline''',
            ],
            True,
            'is incorrectly failing on central whitespace'
        )


class TrailingWhitespace(ValidationTestBase):
    """
    Tests the TrailingWhitespaceValidation
    """

    def setUp(self):
        self.validator = TrailingWhitespaceValidation()
        super().setUp()

    def test_validate_trailing_whitespace(self):
        self.validate_and_compare(
            [
                'trailing space   ',
                'trailing tabs  ',
                '''trailing newline
                '''
            ],
            False,
            'is not detecting trailing whitespace'
        )

    def test_validate_leading_whitespace(self):
        self.validate_and_compare(
            [
                '   leading spaces',
                '   leading tabs',
                '''
                leading newline''',
            ],
            True,
            'is incorrectly failing on leading whitespace'
        )

    def test_validate_middle_whitespace(self):
        self.validate_and_compare(
            [
                'middle spaces',
                'middle tabs',
                '''middle
                newline''',
            ],
            True,
            'is incorrectly failing on central whitespace'
        )


class CanCallJson(ValidationTestBase):
    """
    Tests the CanCallValidation using json.loads
    """

    def setUp(self):
        self.validator = CanCallValidation(json.loads)

    def test_validate_valid_json(self):
        self.validate_and_compare(
            [
                '[1, 2, 3]',
                '{"a": 1.1, "b": 2.2, "c": 3.3}',
                '"string"'
            ],
            True,
            'is incorrectly failing on valid JSON'
        )

    def test_validate_invalid_json(self):
        self.validate_and_compare(
            [
                '[1, 2, 3',
                '{a: 1.1, b: 2.2, c: 3.3}',
                'string'
            ],
            False,
            'is not detecting invalid JSON'
        )


class CanCallLambda(ValidationTestBase):
    """
    Tests the CanCallValidation using a custom lambda function
    """

    def setUp(self):
        # Succeed if it's divisible by 2, otherwise cause an error
        self.validator = CanCallValidation(lambda x: False if x % 2 == 0 else 1 / 0)

    def test_validate_noerror(self):
        self.validate_and_compare(
            [
                2,
                4,
                6
            ],
            True,
            'is incorrectly failing on even numbers'
        )

    def test_validate_error(self):
        self.validate_and_compare(
            [
                1,
                3,
                5
            ],
            False,
            'should fail on odd numbers'
        )


class CanConvertInt(ValidationTestBase):
    """
    Tests CanConvertValidation using the int type
    """

    def setUp(self):
        self.validator = CanConvertValidation(int)

    def test_valid_int(self):
        self.validate_and_compare(
            [
                '1',
                '10',
                '999',
                '99999'
            ],
            True,
            'does not accept valid integers'
        )

    def test_invalid_int(self):
        self.validate_and_compare(
            [
                '1.0',
                '9.5',
                'abc',
                '1e-6'
            ],
            False,
            'accepts invalid integers'
        )


class InList(ValidationTestBase):
    def setUp(self):
        self.validator = InListValidation(['a', 'b', 'c'])

    def test_valid_elements(self):
        self.validate_and_compare(
            [
                'a',
                'b',
                'c'
            ],
            True,
            'does not accept elements that are in the validation list'
        )

    def test_invalid_elements(self):
        self.validate_and_compare(
            [
                'aa',
                'bb',
                'd'
            ],
            False,
            'accepts elements that are not in the validation list'
        )


class DateFormat(ValidationTestBase):
    def setUp(self):
        self.validator = DateFormatValidation('%Y%m%d')

    def test_valid_dates(self):
        self.validate_and_compare(
            [
                '20160404',
                '00011212'
            ],
            True,
            'does not accept valid dates'
        )

    def test_invalid_dates(self):
        self.validate_and_compare(
            [
                '1/2/3456',
                'yyyymmdd',
                '11112233'
            ],
            False,
            'accepts invalid dates'
        )


class StringRegexMatch(ValidationTestBase):
    def setUp(self):
        self.validator = MatchesRegexValidation('^.+\.txt$')

    def test_valid_strings(self):
        self.validate_and_compare(
            [
                'pass.txt',
                'a.txt',
                'lots of words.txt'
            ],
            True,
            'does not accept strings matching the regex'
        )

    def test_invalid_strings(self):
        self.validate_and_compare(
            [
                'pass.TXT',
                '.txt',
                'lots of words.tx'
            ],
            False,
            'accepts strings that do not match the regex'
        )

class CompiledRegexMatch(ValidationTestBase):
    """
    Tests the MatchesRegexValidation, using a compiled regex
    """
    def setUp(self):
        self.validator = MatchesRegexValidation(re.compile('^.+\.txt$', re.IGNORECASE))


    def test_valid_strings(self):
        self.validate_and_compare(
            [
                'pass.txt',
                'a.TXT',
                'lots of words.tXt'
            ],
            True,
            'does not accept strings matching the regex'
        )

    def test_invalid_strings(self):
        self.validate_and_compare(
            [
                'pass.txtt',
                '.txt',
                'lots of words.tx'
            ],
            False,
            'accepts strings that do not match the regex'
        )
