import json
import unittest
import re
import math

from numpy import nan, dtype
import numpy as np
import pandas as pd

from pandas_schema.validations import *
from pandas_schema.core import CombinedValidation, BaseValidation
from pandas_schema.index import ColumnIndexer as ci
from pandas_schema.schema import Schema
from pandas_schema.column import column, column_sequence
from pandas_schema import ValidationWarning

from .util import get_warnings


class Or(unittest.TestCase):
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
        warnings = get_warnings(self.validator, [
            'pass',
            'yes',
            'passyes',
            '345yes345'
        ])
        assert len(warnings) == 0, 'rejects values that should pass'

    def test_invalid_items(self):
        warnings = get_warnings(self.validator, [
            'fail',
            'YES',
            'YPESS'
        ])

        assert len(warnings) == 3, 'accepts values that should pass'


class AndOr(unittest.TestCase):
    """
    Tests a more complex case where we have an "or" and then an "and"
    """
    validator = InListValidation(['one', 'two', 'three'], index=0) | (
            IsDtypeValidation(np.int_, index=0) & InRangeValidation(1, 4, index=0)
    )

    def test_passing_words(self):
        warnings = get_warnings(self.validator, [
            'one',
            'two',
            'three'
        ])
        assert len(warnings) == 0

    def test_failing_words(self):
        warnings = get_warnings(self.validator, [
            'four',
            'five',
            'six'
        ])
        assert len(warnings) == 3

    def test_passing_numbers(self):
        warnings = get_warnings(self.validator, [
            1,
            2,
            3
        ])
        assert len(warnings) == 0

    def test_failing_numbers(self):
        warnings = get_warnings(self.validator, pd.Series([
            4,
            5,
            6
        ], dtype=np.int_))
        assert len(warnings) == 3
        for warning in warnings:
            print(warning.message)

class Optional(unittest.TestCase):
    """
    Tests the "optional" method, which Ors the validation with an IsEmptyValidation
    """
    validator = InRangeValidation(5, 10, index=0).optional()

    def test_passing(self):
        warnings = get_warnings(self.validator, [
            5,
            None,
            6,
            None,
            7,
            None
        ])

        assert warnings == [], 'is not accepting null values'

    def test_failing(self):
        assert len(get_warnings(self.validator, [
            0,
            math.inf,
            -1,
            10
        ])) == 4, 'is accepting invalid values'


