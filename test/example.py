import unittest
import sys
import pathlib

here = pathlib.Path(__file__).parent
sys.path.append(str((here / '../..').resolve()))

class Example(unittest.TestCase):
    def test_example(self):

        import pandas as pd
        from io import StringIO
        from pandas_schema import Column, Schema
        from pandas_schema.validation import LeadingWhitespaceValidation, TrailingWhitespaceValidation, CanConvertValidation, MatchesRegexValidation, InRangeValidation, InListValidation

        schema = Schema([
            Column('Given Name', [LeadingWhitespaceValidation(), TrailingWhitespaceValidation()]),
            Column('Family Name', [LeadingWhitespaceValidation(), TrailingWhitespaceValidation()]),
            Column('Age', [InRangeValidation(0, 120)]),
            Column('Sex', [InListValidation(['Male', 'Female', 'Other'])]),
            Column('Customer ID', [MatchesRegexValidation(r'\d{4}[A-Z]{4}')])
        ])

        test_data = pd.read_csv(StringIO('''
Given Name,Family Name,Age,Sex,Customer ID
Gerald ,Hampton,82,Male,2582GABK
Yuuwa,Miyake,270,male,7951WVLW
Edyta,Majewska ,50,Female,775ANSID
            '''.strip()), sep=',', dtype=str)

        errors = schema.validate(test_data)
        for error in errors:
            print(error)
