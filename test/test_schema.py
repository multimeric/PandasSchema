from io import StringIO

from schema import Schema
import unittest
import column
from validation import LeadingWhitespaceValidation
import pandas as pd


class UnorderedSchema(unittest.TestCase):
    schema = Schema([
        column.Column('a'),
        column.Column('b', [LeadingWhitespaceValidation()])
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
        Tests that when ordered=False, the schema columns are associated with data frame columns by name, not position.
        In this case, the schema's column order is [a, b], while the data frame's order is [b, a]. There is an error in
        column b in the data frame (leading whitespace), and a validation on column b in the schema.

        Schema         a                b (validation)
        Data Frame     b (error)        a

        Thus there will only be an error if column b in the schema is linked to column b in the data frame,
        as is correct behaviour.
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

class OrderedSchema(unittest.TestCase):
    schema = Schema([
        column.Column('a', [LeadingWhitespaceValidation()]),
        column.Column('b')
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
