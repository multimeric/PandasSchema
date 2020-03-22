"""
Tests for pandas_schema.validations
"""
import json
import unittest
import re

from numpy import nan, dtype
import numpy as np
import pandas as pd

from pandas_schema.validations import *
from pandas_schema.core import CombinedValidation, BaseValidation
from pandas_schema.index import ColumnIndexer as ci
from pandas_schema.schema import Schema
from pandas_schema.column import column, column_sequence
from pandas_schema import ValidationWarning


def get_warnings(validator: BaseValidation, series: list) -> typing.Collection[
    ValidationWarning]:
    """
    Tests a validator by asserting that it generates the amount of warnings
    :param series_dtype: Explicitly specifies the dtype for the generated Series
    :param series: The series to check
    :param expected_result: Whether the elements in this series should pass the validation
    :param msg: The message to display if this test fails
    """

    # # Check that self.validator is correct
    # if not self.validator or not isinstance(self.validator, BooleanSeriesValidation, index=0):
    #     raise ValueError('The class must have the validator field set to an instance of a Validation subclass')
    #
    # # Ensure we're comparing series correctly
    # self.addTypeEqualityFunc(pd.Series, self.seriesEquality)

    df = pd.Series(series).to_frame()
    warnings = validator.validate(df)
    return list(warnings)
    #
    # # Now find any items where their validation does not correspond to the expected_result
    # for item, result in zip(series, results):
    #     with self.subTest(value=item):
    #         self.assertEqual(result, expected_result, msg)


class ValidationTestBase(unittest.TestCase):
    def seriesEquality(self, s1: pd.Series, s2: pd.Series, msg: str = None):
        if not s1.equals(s2):
            raise self.failureException(msg)


class CustomSeries(ValidationTestBase):
    """
    Tests the CustomSeriesValidation
    """

    def setUp(self):
        self.validator = CustomSeriesValidation(
            lambda s: ~s.str.contains('fail'),
            message='contained the word fail',
            index=0
        )

    def test_valid_inputs(self):
        assert len(get_warnings(self.validator, ['good',
                                                 'success'])) == 0, 'did not accept valid inputs'

    def test_invalid_inputs(self):
        assert len(get_warnings(self.validator,
                                ['fail', 'failure'])) == 2, 'accepted invalid inputs'


class CustomElement(ValidationTestBase):
    """
    Tests the CustomElementValidation
    """

    def setUp(self):
        self.validator = CustomElementValidation(
            lambda s: s.startswith('_start_'),
            message="Didn't begin with '_start_'",
            index=0
        )

    def test_valid_inputs(self):
        assert len(
            get_warnings(self.validator, ['_start_sdiyhsd', '_start_234fpwunxc\n'])
        ) == 0, 'did not accept valid inputs'

    def test_invalid_inputs(self):
        assert len(
            get_warnings(self.validator, ['fail', '324wfp9ni'])
        ) == 2, 'accepted invalid inputs'


class LeadingWhitespace(ValidationTestBase):
    """
    Tests the LeadingWhitespaceValidation
    """

    def setUp(self):
        self.validator = LeadingWhitespaceValidation(index=0)

    def test_validate_trailing_whitespace(self):
        assert len(get_warnings(self.validator, [
            'trailing space   ',
            'trailing tabs  ',
            '''trailing newline
            '''
        ])) == 0, 'is incorrectly failing on trailing whitespace'

    def test_validate_leading_whitespace(self):
        assert len(get_warnings(self.validator, [
            '   leading spaces',
            '   leading tabs',
            '''
            leading newline''',
        ])) == 3, 'does not detect leading whitespace'

    def test_validate_middle_whitespace(self):
        assert len(get_warnings(self.validator, [
            'middle spaces',
            'middle tabs',
            '''middle
            newline''',
        ])) == 0, 'is incorrectly failing on central whitespace'


class TrailingWhitespace(ValidationTestBase):
    """
    Tests the TrailingWhitespaceValidation
    """

    def setUp(self):
        self.validator = TrailingWhitespaceValidation(index=0)
        super().setUp()

    def test_validate_trailing_whitespace(self):
        assert len(get_warnings(self.validator, [
            'trailing space   ',
            'trailing tabs  ',
            '''trailing newline
            '''
        ])) == 3, 'is not detecting trailing whitespace'

    def test_validate_leading_whitespace(self):
        assert len(get_warnings(self.validator, [
            '   leading spaces',
            '   leading tabs',
            '''
            leading newline''',
        ])) == 0, 'is incorrectly failing on leading whitespace'

    def test_validate_middle_whitespace(self):
        assert len(get_warnings(self.validator, [
            'middle spaces',
            'middle tabs',
            '''middle
            newline''',
        ])) == 0, 'is incorrectly failing on central whitespace'


class CanCallJson(ValidationTestBase):
    """
    Tests the CanCallValidation using json.loads
    """

    def setUp(self):
        self.validator = CanCallValidation(json.loads, index=0)

    def test_validate_valid_json(self):
        assert len(get_warnings(self.validator, [
            '[1, 2, 3]',
            '{"a": 1.1, "b": 2.2, "c": 3.3}',
            '"string"'
        ])) == 0, 'is incorrectly failing on valid JSON'

    def test_validate_invalid_json(self):
        assert len(get_warnings(self.validator, [
            '[1, 2, 3',
            '{a: 1.1, b: 2.2, c: 3.3}',
            'string'
        ])) == 3, 'is not detecting invalid JSON'


class CanCallLambda(ValidationTestBase):
    """
    Tests the CanCallValidation using a custom lambda function
    """

    def setUp(self):
        # Succeed if it's divisible by 2, otherwise cause an error
        self.validator = CanCallValidation(lambda x: False if x % 2 == 0 else 1 / 0,
                                           index=0)

    def test_validate_noerror(self):
        assert len(get_warnings(self.validator, [
            2,
            4,
            6
        ])) == 0, 'is incorrectly failing on even numbers'

    def test_validate_error(self):
        assert len(get_warnings(self.validator, [
            1,
            3,
            5
        ])) == 3, 'should fail on odd numbers'


class CanConvertInt(ValidationTestBase):
    """
    Tests CanConvertValidation using the int type
    """

    def setUp(self):
        self.validator = CanConvertValidation(int, index=0)

    def test_valid_int(self):
        assert len(get_warnings(self.validator, [
            '1',
            '10',
            '999',
            '99999'
        ])) == 0, 'does not accept valid integers'

    def test_invalid_int(self):
        assert len(get_warnings(self.validator, [
            '1.0',
            '9.5',
            'abc',
            '1e-6'
        ])) == 4, 'accepts invalid integers'


class InListCaseSensitive(ValidationTestBase):
    def setUp(self):
        self.validator = InListValidation(['a', 'b', 'c'], index=0)

    def test_valid_elements(self):
        assert len(get_warnings(self.validator, [
            'a',
            'b',
            'c'
        ])) == 0, 'does not accept elements that are in the validation list'

    def test_invalid_elements(self):
        assert len(get_warnings(self.validator, [
            'aa',
            'bb',
            'd',
            'A',
            'B',
            'C'
        ])) == 6, 'accepts elements that are not in the validation list'


class InListCaseInsensitive(ValidationTestBase):
    def setUp(self):
        self.validator = InListValidation(['a', 'b', 'c'], case_sensitive=False,
                                          index=0)

    def test_valid_elements(self):
        assert len(get_warnings(self.validator, [
            'a',
            'b',
            'c',
            'A',
            'B',
            'C'
        ])) == 0, 'does not accept elements that are in the validation list'

    def test_invalid_elements(self):
        assert len(get_warnings(self.validator, [
            'aa',
            'bb',
            'd',
        ])) == 3, 'accepts elements that are not in the validation list'


class DateFormat(ValidationTestBase):
    def setUp(self):
        self.validator = DateFormatValidation('%Y%m%d', index=0)

    def test_valid_dates(self):
        assert len(get_warnings(self.validator, [
            '20160404',
            '00011212'
        ])) == 0, 'does not accept valid dates'

    def test_invalid_dates(self):
        assert len(get_warnings(self.validator, [
            '1/2/3456',
            'yyyymmdd',
            '11112233'
        ])) == 3, 'accepts invalid dates'


class StringRegexMatch(ValidationTestBase):
    def setUp(self):
        self.validator = MatchesPatternValidation(r'^.+\.txt$', index=0)

    def test_valid_strings(self):
        assert len(get_warnings(self.validator, [
            'pass.txt',
            'a.txt',
            'lots of words.txt'
        ])) == 0, 'does not accept strings matching the regex'

    def test_invalid_strings(self):
        assert len(get_warnings(self.validator, [
            'pass.TXT',
            '.txt',
            'lots of words.tx'
        ])) == 3, 'accepts strings that do not match the regex'


class IsDistinct(ValidationTestBase):
    def setUp(self):
        self.validator = IsDistinctValidation(index=0)

    def test_valid_strings(self):
        assert len(get_warnings(self.validator, [
            '1',
            '2',
            '3',
            '4'
        ])) == 0, 'does not accept unique strings'

    def test_invalid_strings(self):
        validation = self.validator.select_cells(pd.Series([
            '1',
            '1',
            '3',
            '4'
        ]))

        self.assertTrue((validation == pd.Series([
            True,
            False,
            True,
            True
        ])).all(), 'did not identify the error')


class CompiledRegexMatch(ValidationTestBase):
    """
    Tests the MatchesRegexValidation, using a compiled regex
    """

    def setUp(self):
        self.validator = MatchesPatternValidation(
            re.compile('^.+\.txt$', re.IGNORECASE), index=0)

    def test_valid_strings(self):
        assert len(get_warnings(self.validator, [
            'pass.txt',
            'a.TXT',
            'lots of words.tXt'
        ])) == 0, 'does not accept strings matching the regex'

    def test_invalid_strings(self):
        test_data = [
            'pass.txtt',
            '.txt',
            'lots of words.tx'
        ]
        warnings = get_warnings(self.validator, test_data)

        # Check that every piece of data failed
        assert len(warnings) == 3, 'accepts strings that do not match the regex'

        # Also test the messages
        for i, (warning, data) in enumerate(zip(warnings, test_data)):
            assert 'Row {}'.format(i) in warning.message
            assert 'Column 0' in warning.message
            assert data in warning.message
            assert self.validator.pattern.pattern in warning.message


class InRange(ValidationTestBase):
    """
    Tests the InRangeValidation
    """

    def setUp(self):
        self.validator = InRangeValidation(7, 9, index=0)

    def test_valid_items(self):
        assert len(get_warnings(self.validator, [
            7,
            8,
            7
        ])) == 0, 'does not accept integers in the correct range'

    def test_invalid_items(self):
        assert len(get_warnings(self.validator, [
            1,
            2,
            3
        ])) == 3, 'Incorrectly accepts integers outside of the range'


class Dtype(ValidationTestBase):
    """
    Tests the DtypeValidation
    """

    def setUp(self):
        self.validator = IsDtypeValidation(np.number, index=0)

    def test_valid_items(self):
        errors = self.validator.validate_series(pd.Series(
            [
                1,
                2,
                3
            ]))

        self.assertEqual(len(errors), 0)

    def test_invalid_items(self):
        errors = self.validator.validate_series(pd.Series(
            [
                'a',
                '',
                'c'
            ]))

        self.assertEqual(len(errors), 1)
        self.assertEqual(type(errors[0]), ValidationWarning)

    def test_schema(self):
        """
        Test this validation inside a schema, to ensure we get helpful error messages.
        In particular, we want to make sure that a ValidationWarning without a row number won't break the schema
        """
        df = pd.DataFrame(data={
            'wrong_dtype1': ['not_an_int'],
            'wrong_dtype2': [123],
            'wrong_dtype3': [12.5]
        })

        schema = Schema([
            IsDtypeValidation(dtype('int64'), index=ci('wrong_dtype1')),
            IsDtypeValidation(dtype('float64'), index=ci('wrong_dtype2')),
            IsDtypeValidation(dtype('int64'), index=ci('wrong_dtype3')),
        ])

        errors = schema.validate(df)

        self.assertEqual(
            [x.props for x in errors],
            [
                {'dtype': np.object},
                {'dtype': np.int64},
                {'dtype': np.float64},
            ]
        )


class Negate(ValidationTestBase):
    """
    Tests the ~ operator on a MatchesPatternValidation
    """

    def setUp(self):
        self.validator = ~MatchesPatternValidation('fail', index=0)

    def test_valid_items(self):
        assert len(get_warnings(self.validator, [
            'Pass',
            '1',
            'True'
        ])) == 0, 'Rejects values that should pass'

    def test_invalid_items(self):
        assert len(get_warnings(self.validator, [
            'fail',
            'thisfails',
            'failure'
        ])) == 3, 'Accepts values that should pass'


class Or(ValidationTestBase):
    """
    Tests the | operator on two MatchesPatternValidations
    """

    def setUp(self):
        self.validator = MatchesPatternValidation(
            'yes', index=0
        ) | MatchesPatternValidation(
            'pass', index=0
        )

    def test_valid_items(self):
        assert len(get_warnings(self.validator, [
            'pass',
            'yes',
            'passyes',
            '345yes345'
        ])) == 0, 'rejects values that should pass'

    def test_invalid_items(self):
        assert len(get_warnings(self.validator, [
            'fail',
            'YES',
            'YPESS'
        ])) == 6, 'accepts values that should pass'


class CustomMessage(ValidationTestBase):
    """
    Tests that custom error messages work as expected
    """

    def setUp(self):
        self.message = "UNUSUAL MESSAGE THAT WOULDN'T BE IN A NORMAL ERROR"

    def test_default_message(self):
        validator = InRangeValidation(min=4, index=0)
        for error in validator.validate_series(pd.Series(
                [
                    1,
                    2,
                    3
                ]
        ), flatten=True):
            self.assertNotRegex(error.message, self.message,
                                'Validator not using the default warning message!')

    def test_custom_message(self):
        validator = InRangeValidation(min=4, message=self.message, index=0)
        for error in validator.validate_series(pd.Series(
                [
                    1,
                    2,
                    3
                ]
        ), flatten=True):
            self.assertRegex(error.message, self.message,
                             'Validator not using the custom warning message!')


@unittest.skip('allow_empty no longer exists')
class GetErrorTests(ValidationTestBase):
    """
    Tests for float valued columns where allow_empty=True
    """

    def setUp(self):
        self.vals = [1.0, None, 3]

    def test_in_range_allow_empty_with_error(self):
        validator = InRangeValidation(min=4, index=0)
        errors = list(validator.validate_series(pd.Series(self.vals)))
        self.assertEqual(len(errors), sum(v is not None for v in self.vals))

    def test_in_range_allow_empty_with_no_error(self):
        validator = InRangeValidation(min=0, index=0)
        errors = list(validator.validate_series(pd.Series(self.vals)))
        self.assertEqual(len(errors), 0)

    def test_in_range_allow_empty_false_with_error(self):
        validator = InRangeValidation(min=4, index=0)
        errors = list(validator.validate_series(pd.Series(self.vals)))
        self.assertEqual(len(errors), len(self.vals))


class PandasDtypeTests(ValidationTestBase):
    """
    Tests Series with various pandas dtypes that don't exist in numpy (specifically categories)
    """

    def setUp(self):
        self.validator = InListValidation(['a', 'b', 'c'], case_sensitive=False,
                                          index=0)

    def test_valid_elements(self):
        errors = self.validator.validate_series(
            pd.Series(['a', 'b', 'c', 'A', 'B', 'C'], dtype='category'))
        assert len(list(errors)) == 0

    def test_invalid_empty_elements(self):
        errors = self.validator.validate_series(
            pd.Series(['aa', 'bb', 'd', None], dtype='category'))
        assert len(list(errors)) == 4

    def test_invalid_and_empty_elements(self):
        errors = self.validator.validate_series(
            pd.Series(['a', None], dtype='category'))
        assert len(list(errors)) == 1

    def test_invalid_elements(self):
        errors = self.validator.validate_series(
            pd.Series(['aa', 'bb', 'd'], dtype='category'))
        assert len(list(errors)) == 3
