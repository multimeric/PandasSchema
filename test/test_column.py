import unittest
import pandas as pd

from pandas_schema import Column
from pandas_schema.validation import CanConvertValidation, LeadingWhitespaceValidation, TrailingWhitespaceValidation


class SingleValidationColumn(unittest.TestCase):
    """
    Test a column with one single validation
    """
    NAME = 'col1'

    col = Column(NAME, [CanConvertValidation(int)], allow_empty=False)
    ser = pd.Series([
        'a',
        'b',
        'c'
    ])

    def test_name(self):
        self.assertEqual(self.col.name, self.NAME, 'A Column does not store its name correctly')

    def test_outputs(self):
        results = self.col.validate(self.ser)

        self.assertEqual(len(results), len(self.ser), 'A Column produces the wrong number of errors')
        for i in range(2):
            self.assertTrue(any([r.row == i for r in results]), 'A Column does not report errors for every row')


class DoubleValidationColumn(unittest.TestCase):
    """
    Test a column with two different validations
    """
    NAME = 'col1'

    col = Column(NAME, [TrailingWhitespaceValidation(), LeadingWhitespaceValidation()], allow_empty=False)
    ser = pd.Series([
        ' a ',
        ' b ',
        ' c '
    ])

    def test_outputs(self):
        results = self.col.validate(self.ser)

        # There should be 6 errors, 2 for each row
        self.assertEqual(len(results), 2 * len(self.ser), 'A Column produces the wrong number of errors')
        for i in range(2):
            in_row = [r for r in results if r.row == i]
            self.assertEquals(len(in_row), 2, 'A Column does not report both errors for every row')


class AllowEmptyColumn(unittest.TestCase):
    """
    Test a column with one single validation that allows empty columns
    """
    NAME = 'col1'

    col = Column(NAME, [CanConvertValidation(int)], allow_empty=True)
    ser = pd.Series([
        '',
    ])

    def test_outputs(self):
        results = self.col.validate(self.ser)
        self.assertEqual(len(results), 0, 'allow_empty is not allowing empty columns')
