from io import StringIO
import unittest
import pandas as pd
from numpy.core.multiarray import dtype

from pandas_schema import Schema, Column
from pandas_schema.validation import LeadingWhitespaceValidation, IsDtypeValidation
from pandas_schema.errors import PanSchArgumentError

class UnorderedSchema(unittest.TestCase):
    schema = Schema([
        Column('a'),
        Column('b', [LeadingWhitespaceValidation()])
    ], ordered=False)

    def test_fields(self):
        self.assertEqual(len(self.schema.columns), 2, 'The schema is not storing all of its columns')
        self.assertEqual(self.schema.ordered, False, 'The schema is not storing the correct value of ordered')

    def test_validate_valid(self):
        df = pd.DataFrame({
            'a': ['1', '2', '3'],
            'b': ['1', '2', '3']
        })
        results = self.schema.validate(df)
        self.assertEqual(len(results), 0, 'A correct data frame should have no errors')

    def test_validate_invalid(self):
        df = pd.DataFrame({
            'a': [' 1', '2', '3'],
            'b': [' 1', '2', '3']
        })
        results = self.schema.validate(df)
        self.assertEqual(len(results), 1, 'An incorrect data frame should report errors')

    def test_mixed_columns(self):
        """
        Tests that when ordered=False, the schema columns are
        associated with data frame columns by name, not position.
        In this case, the schema's column order is [a, b], while
         the data frame's order is [b, a]. There is an error in
        column b in the data frame (leading whitespace), and a
        validation on column b in the schema.

        Schema         a                b (validation)
        Data Frame     b (error)        a

        Thus there will only be an error if column b in the schema
        is linked to column b in the data frame, as is correct
        behaviour.
        """

        df = pd.read_csv(StringIO('''
b,a
 1,1
2,3
3,3
        '''), sep=',', header=0, dtype=str)
        results = self.schema.validate(df)

        self.assertEqual(len(results), 1, 'There should be 1 error')
        self.assertEqual(results[0].row, 0)
        self.assertEqual(results[0].column, 'b', 'The Schema object is not associating columns and column schemas by name')

    def test_column_subset_detect(self):
        """
        Tests that when ordered=False, validation is possible by
        passing a subset of the columns contained in the schema

        Schema         a*                b (validation)
        Data Frame     b (error)        a not passed

        column* is not being passed

        Thus there will only be an error if column b in the schema
        is linked to column b in the data frame, as is correct
        behaviour
        """

        df = pd.read_csv(StringIO('''
b,a
 1,1
2,3
3,3
        '''), sep=',', header=0, dtype=str)

        results = self.schema.validate(df, columns=['b'])

        self.assertEqual(len(results), 1, 'There should be 1 error')
        self.assertEqual(results[0].row, 0)
        self.assertEqual(results[0].column, 'b', 'The Schema object is not associating columns and column schemas by name')

    def test_column_subset_detect_empty(self):
        """
        Tests that when ordered=False, validation is possible by
        passing a subset of the columns contained in the schema

        Schema         a                b* (validation)
        Data Frame     b (error)        a

        column* is not being passed

        There will be an error if other than zero errors are found.
        """

        df = pd.read_csv(StringIO('''
b,a
 1,1
2,3
3,3
        '''), sep=',', header=0, dtype=str)
        # should detect no errors
        results_empty = self.schema.validate(df, columns=['a'])

        self.assertEqual(len(results_empty), 0, 'There should be no errors')

    def test_column_subset_error(self):
        """
        Tests that when ordered=False, validation is possible by
        passing a subset of the columns contained in the schema

        Schema         a                b (validation)
        Data Frame     b (error)        a

        There will be an error if a column different than 'a' or 'b' is passed
        """

        df = pd.read_csv(StringIO('''
b,a
 1,1
2,3
3,3
        '''), sep=',', header=0, dtype=str)

        # should raise a PanSchArgumentError
        self.assertRaises(PanSchArgumentError, self.schema.validate, df, columns=['c'])


class OrderedSchema(unittest.TestCase):
    schema = Schema([
        Column('a', [LeadingWhitespaceValidation()]),
        Column('b')
    ], ordered=True)

    def test_mixed_columns(self):
        """
        Tests that when ordered=True, the schema columns are associated with data frame columns by position, not name.

        In this case, the schema's column order is [a, b], while the data frame's order is [b, a]. There is an error in
        column b in the data frame (leading whitespace), and a validation on column a in the schema.

        Schema         a (validation)   b
        Data Frame     b (error)        a

        Thus there will only be an error if column b in the schema is linked to column a in the data frame,
        as is correct behaviour when ordered=True.
        """
        df = pd.read_csv(StringIO('''
b,a
 1,1
2,3
3,3
        '''), sep=',', header=0, dtype=str)
        results = self.schema.validate(df)

        self.assertEqual(len(results), 1, 'There should be 1 error')
        self.assertEqual(results[0].row, 0)
        self.assertEqual(results[0].column, 'b', 'The Schema object is not associating columns and column schemas by position')
