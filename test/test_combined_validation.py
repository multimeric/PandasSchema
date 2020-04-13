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

        assert len(warnings) == 6, 'accepts values that should pass'

class AndOr(unittest.TestCase):
    validator = InListValidation(['one', 'two', 'three']) | (
        IsDtypeValidation(int) & InRangeValidation(1, 3)
    )
    def test_and_or(self):
        pass

